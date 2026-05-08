from sqlalchemy.orm import Session

from app.models import OutboundMessage


def send_verification_email(db: Session, recipient: str, verification_code: str, verification_link: str) -> None:
    body = (
        "Bienvenue sur MyCloudOS.\\n\\n"
        f"Code de verification: {verification_code}\\n"
        f"Lien de verification: {verification_link}\\n\\n"
        "Si vous n'etes pas a l'origine de cette demande, ignorez ce message."
    )
    message = OutboundMessage(
        recipient=recipient,
        subject="Verification de compte MyCloudOS",
        body=body,
    )
    db.add(message)
    db.commit()
