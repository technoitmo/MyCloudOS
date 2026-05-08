import os


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


settings = Settings()
