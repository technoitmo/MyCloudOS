from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import settings


_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="mycloudos-api-token")


def create_access_token(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})


def decode_access_token(token: str) -> int | None:
    try:
        data = _serializer.loads(token, max_age=settings.API_TOKEN_EXPIRE_SECONDS)
        user_id = data.get("uid")
        if not isinstance(user_id, int):
            return None
        return user_id
    except (BadSignature, SignatureExpired):
        return None
