from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.auth_token import create_access_token, decode_access_token
from app.core.config import settings
from app.core.security import (
    create_verification_code,
    create_verification_token,
    hash_password,
    verification_expiry,
    verify_password,
)
from app.db import get_db
from app.models import CloudInstance, CloudOSImage, OutboundMessage, User
from app.services.cloud_service import start_async_provisioning
from app.services.email_service import send_verification_email

router = APIRouter(prefix="/api", tags=["api"])
security = HTTPBearer(auto_error=False)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class VerifyCodeIn(BaseModel):
    email: EmailStr
    code: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class CreateInstanceIn(BaseModel):
    name: str
    os_image_id: int
    region: str
    cpu_cores: int
    memory_gb: int
    disk_gb: int


def _serialize_instance(vm: CloudInstance) -> dict:
    return {
        "id": vm.id,
        "name": vm.name,
        "status": vm.status,
        "region": vm.region,
        "cpu_cores": vm.cpu_cores,
        "memory_gb": vm.memory_gb,
        "disk_gb": vm.disk_gb,
        "public_ip": vm.public_ip,
        "access_username": vm.access_username,
        "os_image": {
            "id": vm.os_image.id,
            "name": vm.os_image.name,
            "family": vm.os_image.family,
            "version": vm.os_image.version,
        },
    }


def _get_current_user(
    db: Session,
    credentials: HTTPAuthorizationCredentials | None,
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "mycloudos-backend"}


@router.post("/auth/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> dict:
    normalized_email = payload.email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already used")

    code = create_verification_code()
    token = create_verification_token()
    user = User(
        email=normalized_email,
        password_hash=hash_password(payload.password),
        verification_code=code,
        verification_token=token,
        code_expires_at=verification_expiry(),
    )
    db.add(user)
    db.commit()

    verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"
    send_verification_email(db, normalized_email, code, verification_link)
    return {"message": "Account created. Verify your email via code or link."}


@router.post("/auth/verify-code")
def verify_code(payload: VerifyCodeIn, db: Session = Depends(get_db)) -> dict:
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")

    if user.is_verified:
        return {"message": "Account already verified"}

    now = datetime.now(UTC)
    if not user.code_expires_at or user.code_expires_at < now:
        raise HTTPException(status_code=400, detail="Verification code expired")

    if user.verification_code != payload.code.strip():
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.is_verified = True
    user.verification_code = None
    user.verification_token = None
    user.code_expires_at = None
    db.add(user)
    db.commit()
    return {"message": "Account verified"}


@router.get("/auth/verify")
def verify_token(token: str, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification link")

    if user.code_expires_at and user.code_expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Verification link expired")

    user.is_verified = True
    user.verification_code = None
    user.verification_token = None
    user.code_expires_at = None
    db.add(user)
    db.commit()
    return {"message": "Account verified"}


@router.post("/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)) -> dict:
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Account not verified")

    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email},
    }


@router.get("/cloud/os-images")
def list_os_images(db: Session = Depends(get_db)) -> list[dict]:
    os_images = db.query(CloudOSImage).filter(CloudOSImage.is_available.is_(True)).all()
    return [
        {
            "id": image.id,
            "name": image.name,
            "family": image.family,
            "version": image.version,
            "architecture": image.architecture,
            "description": image.description,
        }
        for image in os_images
    ]


@router.get("/cloud/instances")
def list_instances(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> list[dict]:
    user = _get_current_user(db, credentials)
    instances = (
        db.query(CloudInstance)
        .filter(CloudInstance.owner_id == user.id)
        .order_by(CloudInstance.created_at.desc())
        .all()
    )
    return [_serialize_instance(vm) for vm in instances]


@router.post("/cloud/instances")
def create_instance(
    payload: CreateInstanceIn,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    user = _get_current_user(db, credentials)
    image = db.get(CloudOSImage, payload.os_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="OS image not found")

    instance = CloudInstance(
        name=payload.name.strip(),
        status="provisioning",
        region=payload.region.strip(),
        cpu_cores=max(1, min(payload.cpu_cores, 16)),
        memory_gb=max(2, min(payload.memory_gb, 64)),
        disk_gb=max(20, min(payload.disk_gb, 512)),
        owner_id=user.id,
        os_image_id=image.id,
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)

    start_async_provisioning(instance.id)
    db.refresh(instance)

    return {
        "message": "Instance provisioning started",
        "instance": _serialize_instance(instance),
    }


@router.get("/dev/messages")
def list_dev_messages(db: Session = Depends(get_db)) -> list[dict]:
    if settings.EMAIL_MODE != "dev":
        raise HTTPException(status_code=404, detail="Endpoint available only in EMAIL_MODE=dev")

    messages = db.query(OutboundMessage).order_by(OutboundMessage.created_at.desc()).limit(20).all()
    return [
        {
            "id": msg.id,
            "recipient": msg.recipient,
            "subject": msg.subject,
            "body": msg.body,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]
