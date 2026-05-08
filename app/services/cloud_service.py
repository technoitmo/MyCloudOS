import hashlib
import threading
import time
from datetime import datetime, UTC

from app.db import SessionLocal
from app.models import CloudInstance, CloudOSImage


DEFAULT_OS_IMAGES = [
    {
        "name": "Windows Server 2022",
        "family": "windows",
        "version": "2022",
        "architecture": "x86_64",
        "description": "Ideal pour workloads Windows enterprise et Active Directory.",
    },
    {
        "name": "Ubuntu LTS",
        "family": "linux",
        "version": "24.04",
        "architecture": "x86_64",
        "description": "Distribution generaliste optimisee cloud pour web, API et data.",
    },
    {
        "name": "Debian",
        "family": "linux",
        "version": "12",
        "architecture": "x86_64",
        "description": "OS stable et securise pour applications critiques.",
    },
    {
        "name": "Fedora Cloud",
        "family": "linux",
        "version": "41",
        "architecture": "x86_64",
        "description": "Image cloud moderne avec stack recente pour devops.",
    },
]


def seed_os_images_if_needed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(CloudOSImage).count()
        if existing > 0:
            return
        for item in DEFAULT_OS_IMAGES:
            db.add(CloudOSImage(**item))
        db.commit()
    finally:
        db.close()


def _fake_ip(instance_id: int) -> str:
    digest = hashlib.sha256(f"mycloudos-{instance_id}".encode("utf-8")).hexdigest()
    octets = [int(digest[i : i + 2], 16) for i in range(0, 8, 2)]
    return f"52.{octets[0]}.{octets[1]}.{octets[2]}"


def _complete_provisioning(instance_id: int) -> None:
    time.sleep(4)
    db = SessionLocal()
    try:
        instance = db.get(CloudInstance, instance_id)
        if not instance:
            return
        instance.status = "running"
        instance.public_ip = _fake_ip(instance.id)
        instance.access_username = "Administrator" if instance.os_image.family == "windows" else "cloudadmin"
        instance.provisioned_at = datetime.now(UTC)
        db.add(instance)
        db.commit()
    finally:
        db.close()


def start_async_provisioning(instance_id: int) -> None:
    thread = threading.Thread(target=_complete_provisioning, args=(instance_id,), daemon=True)
    thread.start()
