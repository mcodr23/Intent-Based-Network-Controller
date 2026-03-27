from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Device, User
from app.schemas.schemas import DeviceDetailOut, DeviceOut, DiscoveryRequest, DiscoveryResponse
from app.services.audit_service import log_action
from app.services.discovery_service import discover_devices
from app.services.topology_service import rebuild_topology


router = APIRouter(tags=["Inventory"])


@router.get("/devices", response_model=list[DeviceOut])
def list_devices(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    devices = db.query(Device).all()
    log_action(
        db,
        action="list_devices",
        resource="devices",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"count": len(devices)},
        status_code=200,
    )
    return devices


@router.post("/discovery/start", response_model=DiscoveryResponse)
def start_discovery(
    payload: DiscoveryRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer")),
):
    scanned, discovered = discover_devices(db, payload.ip_targets, payload.subnet)
    rebuild_topology(db)

    log_action(
        db,
        action="start_discovery",
        resource="discovery",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"scanned": scanned, "discovered": len(discovered)},
        status_code=200,
    )

    return DiscoveryResponse(scanned=scanned, discovered=len(discovered), devices=discovered)


@router.get("/devices/{device_id}", response_model=DeviceDetailOut)
def get_device(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    log_action(
        db,
        action="get_device",
        resource="device",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"device_id": device_id},
        status_code=200,
    )

    return device
