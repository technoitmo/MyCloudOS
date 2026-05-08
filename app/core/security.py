import secrets
from datetime import datetime, timedelta, UTC

from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_verification_code() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def create_verification_token() -> str:
    return secrets.token_urlsafe(32)


def verification_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
