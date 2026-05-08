from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import Base, engine
from app.routers import api
from app.services.cloud_service import seed_os_images_if_needed


app = FastAPI(title="MyCloudOS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure base schema exists for local runs and test clients.
Base.metadata.create_all(bind=engine)
seed_os_images_if_needed()

app.include_router(api.router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_os_images_if_needed()
