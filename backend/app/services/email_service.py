import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import OutboundMessage


def _save_outbound_message(db: Session, recipient: str, subject: str, body: str) -> None:
    message = OutboundMessage(
        recipient=recipient,
        subject=subject,
        body=body,
    )
    db.add(message)
    db.commit()


def _send_smtp_email(recipient: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST is required when EMAIL_MODE=smtp")

    email = EmailMessage()
    email["From"] = settings.EMAIL_FROM
    email["To"] = recipient
    email["Subject"] = subject
    email.set_content(body)

    if settings.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(email)
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(email)


def send_verification_email(db: Session, recipient: str, verification_code: str, verification_link: str) -> None:
    subject = "Verification de compte MyCloudOS"
    body = (
        "Bienvenue sur MyCloudOS.\\n\\n"
        f"Code de verification: {verification_code}\\n"
        f"Lien de verification: {verification_link}\\n\\n"
        "Si vous n'etes pas a l'origine de cette demande, ignorez ce message."
    )

    if settings.EMAIL_MODE == "smtp":
        _send_smtp_email(recipient=recipient, subject=subject, body=body)
        return

    _save_outbound_message(db=db, recipient=recipient, subject=subject, body=body)
