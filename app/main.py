from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.db import Base, engine
from app.routers import auth, web
from app.services.cloud_service import seed_os_images_if_needed


app = FastAPI(title="MyCloudOS")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE,
    https_only=False,
    max_age=60 * 60 * 24,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates

# Ensure base schema exists for local runs and test clients.
Base.metadata.create_all(bind=engine)
seed_os_images_if_needed()

app.include_router(auth.router)
app.include_router(web.router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_os_images_if_needed()
