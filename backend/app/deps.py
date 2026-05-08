from starlette.requests import Request

from app.db import SessionLocal
from app.models import User


def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    db = SessionLocal()
    try:
        return db.get(User, user_id)
    finally:
        db.close()
