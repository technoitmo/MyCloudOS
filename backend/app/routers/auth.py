from datetime import datetime, UTC

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_verification_code,
    create_verification_token,
    hash_password,
    verification_expiry,
    verify_password,
)
from app.core.session import add_flash, pop_flashes
from app.db import get_db
from app.models import User
from app.services.email_service import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/register")
def register_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "flashes": pop_flashes(request),
            "current_user": None,
        },
    )


@router.post("/register")
def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_email = email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        add_flash(request, "danger", "Cet email est deja utilise.")
        return RedirectResponse(url="/auth/register", status_code=303)

    code = create_verification_code()
    token = create_verification_token()
    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        verification_code=code,
        verification_token=token,
        code_expires_at=verification_expiry(),
    )
    db.add(user)
    db.commit()

    verification_link = f"{settings.FRONTEND_URL}/auth/verify?token={token}"
    send_verification_email(db, normalized_email, code, verification_link)

    add_flash(request, "success", "Compte cree. Verifiez votre email via code ou lien.")
    return RedirectResponse(url=f"/auth/verify-code?email={normalized_email}", status_code=303)


@router.get("/verify-code")
def verify_code_page(request: Request, email: str = ""):
    return request.app.state.templates.TemplateResponse(
        "verify_code.html",
        {
            "request": request,
            "prefill_email": email,
            "flashes": pop_flashes(request),
            "current_user": None,
        },
    )


@router.post("/verify-code")
def verify_code_submit(
    request: Request,
    email: str = Form(...),
    code: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        add_flash(request, "danger", "Compte introuvable.")
        return RedirectResponse(url="/auth/verify-code", status_code=303)

    if user.is_verified:
        add_flash(request, "info", "Compte deja verifie. Connectez-vous.")
        return RedirectResponse(url="/auth/login", status_code=303)

    now = datetime.now(UTC)
    if not user.code_expires_at or user.code_expires_at < now:
        add_flash(request, "danger", "Code expire. Demandez une nouvelle verification.")
        return RedirectResponse(url=f"/auth/verify-code?email={normalized_email}", status_code=303)

    if user.verification_code != code.strip():
        add_flash(request, "danger", "Code incorrect.")
        return RedirectResponse(url=f"/auth/verify-code?email={normalized_email}", status_code=303)

    user.is_verified = True
    user.verification_code = None
    user.verification_token = None
    user.code_expires_at = None
    db.add(user)
    db.commit()

    add_flash(request, "success", "Compte verifie. Vous pouvez vous connecter.")
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/verify")
def verify_by_link(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        add_flash(request, "danger", "Lien de verification invalide.")
        return RedirectResponse(url="/auth/login", status_code=303)

    if user.is_verified:
        add_flash(request, "info", "Compte deja verifie.")
        return RedirectResponse(url="/auth/login", status_code=303)

    if user.code_expires_at and user.code_expires_at < datetime.now(UTC):
        add_flash(request, "danger", "Lien de verification expire.")
        return RedirectResponse(url="/auth/verify-code", status_code=303)

    user.is_verified = True
    user.verification_code = None
    user.verification_token = None
    user.code_expires_at = None
    db.add(user)
    db.commit()

    add_flash(request, "success", "Verification reussie. Connectez-vous.")
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/login")
def login_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "flashes": pop_flashes(request),
            "current_user": None,
        },
    )


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(password, user.password_hash):
        add_flash(request, "danger", "Identifiants invalides.")
        return RedirectResponse(url="/auth/login", status_code=303)

    if not user.is_verified:
        add_flash(request, "danger", "Compte non verifie. Verifiez via code ou lien.")
        return RedirectResponse(url=f"/auth/verify-code?email={normalized_email}", status_code=303)

    request.session["user_id"] = user.id
    add_flash(request, "success", "Connexion reussie.")
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    add_flash(request, "info", "Vous etes deconnecte.")
    return RedirectResponse(url="/", status_code=303)
