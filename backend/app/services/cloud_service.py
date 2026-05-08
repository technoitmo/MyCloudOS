import hashlib
import threading
import time
from datetime import datetime, UTC

from app.core.config import settings
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


def _complete_provisioning_local(instance_id: int) -> None:
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


def _resolve_openstack_image_name(instance: CloudInstance) -> str:
    return f"{instance.os_image.name} {instance.os_image.version}"


def _complete_provisioning_openstack(instance_id: int) -> None:
    db = SessionLocal()
    try:
        instance = db.get(CloudInstance, instance_id)
        if not instance:
            return

        try:
            import openstack
        except ImportError as exc:
            raise RuntimeError(
                "openstacksdk is required for CLOUD_PROVIDER=openstack"
            ) from exc

        conn = openstack.connection.Connection(
            auth_url=settings.OPENSTACK_AUTH_URL,
            username=settings.OPENSTACK_USERNAME,
            password=settings.OPENSTACK_PASSWORD,
            project_name=settings.OPENSTACK_PROJECT_NAME,
            user_domain_name=settings.OPENSTACK_USER_DOMAIN_NAME,
            project_domain_name=settings.OPENSTACK_PROJECT_DOMAIN_NAME,
        )

        image_name = _resolve_openstack_image_name(instance)
        image = conn.compute.find_image(image_name)
        if not image:
            raise RuntimeError(f"OpenStack image not found: {image_name}")

        flavor = conn.compute.find_flavor("m1.small")
        if not flavor:
            raise RuntimeError("OpenStack flavor not found: m1.small")

        server = conn.compute.create_server(
            name=instance.name,
            image_id=image.id,
            flavor_id=flavor.id,
            networks=[],
        )
        server = conn.compute.wait_for_server(server, wait=600)

        public_ip = None
        addresses = getattr(server, "addresses", {}) or {}
        for network_values in addresses.values():
            for ip_info in network_values:
                if ip_info.get("OS-EXT-IPS:type") == "floating":
                    public_ip = ip_info.get("addr")
                    break
            if public_ip:
                break

        instance.status = "running"
        instance.public_ip = public_ip
        instance.access_username = "Administrator" if instance.os_image.family == "windows" else "cloudadmin"
        instance.provisioned_at = datetime.now(UTC)
        db.add(instance)
        db.commit()
    except Exception:
        db.rollback()
        failed_instance = db.get(CloudInstance, instance_id)
        if failed_instance:
            failed_instance.status = "error"
            db.add(failed_instance)
            db.commit()
    finally:
        db.close()


def _complete_provisioning(instance_id: int) -> None:
    if settings.CLOUD_PROVIDER == "openstack":
        _complete_provisioning_openstack(instance_id)
        return

    _complete_provisioning_local(instance_id)


def start_async_provisioning(instance_id: int) -> None:
    thread = threading.Thread(target=_complete_provisioning, args=(instance_id,), daemon=True)
    thread.start()
