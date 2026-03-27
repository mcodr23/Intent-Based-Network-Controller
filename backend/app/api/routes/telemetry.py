from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Device, Telemetry, User
from app.schemas.schemas import TelemetryLatestOut, TelemetryOut
from app.services.audit_service import log_action
from app.services.telemetry_service import collect_all, get_latest_for_all


router = APIRouter(tags=["Telemetry"])


@router.get("/telemetry", response_model=list[TelemetryLatestOut])
def telemetry_overview(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    latest = get_latest_for_all(db)
    if not latest:
        collect_all(db)
        latest = get_latest_for_all(db)

    log_action(
        db,
        action="list_telemetry",
        resource="telemetry",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"devices": len(latest)},
        status_code=200,
    )
    return latest


@router.get("/telemetry/{device_id}", response_model=list[TelemetryOut])
def telemetry_device(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    samples = (
        db.query(Telemetry)
        .filter(Telemetry.device_id == device_id)
        .order_by(desc(Telemetry.collected_at))
        .limit(20)
        .all()
    )

    log_action(
        db,
        action="get_telemetry_device",
        resource="telemetry",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"device_id": device_id, "samples": len(samples)},
        status_code=200,
    )

    return list(reversed(samples))
