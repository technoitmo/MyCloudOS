from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.session import add_flash, pop_flashes
from app.db import get_db
from app.deps import get_current_user
from app.models import CloudInstance, CloudOSImage, OutboundMessage, User
from app.services.cloud_service import start_async_provisioning

router = APIRouter(tags=["web"])


@router.get("/")
def home(request: Request):
    current_user = get_current_user(request)
    return request.app.state.templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "current_user": current_user,
            "flashes": pop_flashes(request),
        },
    )


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request)
    if not current_user:
        add_flash(request, "danger", "Connectez-vous pour acceder au dashboard.")
        return RedirectResponse(url="/auth/login", status_code=303)

    os_images = db.query(CloudOSImage).filter(CloudOSImage.is_available.is_(True)).all()
    instances = (
        db.query(CloudInstance)
        .filter(CloudInstance.owner_id == current_user.id)
        .order_by(CloudInstance.created_at.desc())
        .all()
    )

    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "os_images": os_images,
            "instances": instances,
            "flashes": pop_flashes(request),
        },
    )


@router.post("/cloud/instances")
def create_instance(
    request: Request,
    name: str = Form(...),
    os_image_id: int = Form(...),
    region: str = Form(...),
    cpu_cores: int = Form(...),
    memory_gb: int = Form(...),
    disk_gb: int = Form(...),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request)
    if not current_user:
        add_flash(request, "danger", "Session expiree. Reconnectez-vous.")
        return RedirectResponse(url="/auth/login", status_code=303)

    image = db.get(CloudOSImage, os_image_id)
    if not image:
        add_flash(request, "danger", "Image OS introuvable.")
        return RedirectResponse(url="/dashboard", status_code=303)

    instance = CloudInstance(
        name=name.strip(),
        status="provisioning",
        region=region.strip(),
        cpu_cores=max(1, min(cpu_cores, 16)),
        memory_gb=max(2, min(memory_gb, 64)),
        disk_gb=max(20, min(disk_gb, 512)),
        owner_id=current_user.id,
        os_image_id=image.id,
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)

    start_async_provisioning(instance.id)

    add_flash(request, "success", "Instance en cours de creation.")
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/dev/messages")
def dev_messages(request: Request, db: Session = Depends(get_db)):
    messages = db.query(OutboundMessage).order_by(OutboundMessage.created_at.desc()).limit(20).all()
    return request.app.state.templates.TemplateResponse(
        "dev_messages.html",
        {
            "request": request,
            "messages": messages,
            "current_user": get_current_user(request),
            "flashes": pop_flashes(request),
        },
    )
