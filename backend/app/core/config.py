import os


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    APP_NAME = "MyCloudOS"
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SESSION_COOKIE = "mycloudos_session"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mycloudos.db")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:3009")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8009")
    BASE_URL = os.getenv("BASE_URL", FRONTEND_URL)
    VERIFICATION_CODE_EXPIRE_MINUTES = int(os.getenv("VERIFICATION_CODE_EXPIRE_MINUTES", "30"))
    API_TOKEN_EXPIRE_SECONDS = int(os.getenv("API_TOKEN_EXPIRE_SECONDS", "86400"))

    EMAIL_MODE = os.getenv("EMAIL_MODE", "dev")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@mycloudos.local")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = _as_bool(os.getenv("SMTP_USE_TLS", "true"), default=True)
    SMTP_USE_SSL = _as_bool(os.getenv("SMTP_USE_SSL", "false"), default=False)

    CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "local")

    OPENSTACK_AUTH_URL = os.getenv("OPENSTACK_AUTH_URL", "")
    OPENSTACK_USERNAME = os.getenv("OPENSTACK_USERNAME", "")
    OPENSTACK_PASSWORD = os.getenv("OPENSTACK_PASSWORD", "")
    OPENSTACK_PROJECT_NAME = os.getenv("OPENSTACK_PROJECT_NAME", "")
    OPENSTACK_USER_DOMAIN_NAME = os.getenv("OPENSTACK_USER_DOMAIN_NAME", "Default")
    OPENSTACK_PROJECT_DOMAIN_NAME = os.getenv("OPENSTACK_PROJECT_DOMAIN_NAME", "Default")


settings = Settings()
