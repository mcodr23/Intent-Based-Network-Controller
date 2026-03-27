from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import ComplianceStatus, Device, User
from app.schemas.schemas import ComplianceOut
from app.services.audit_service import log_action
from app.services.compliance_service import evaluate_all_devices, evaluate_device_compliance, remediate_device


router = APIRouter(tags=["Compliance"])


@router.get("/compliance", response_model=list[ComplianceOut])
def compliance_summary(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    statuses = evaluate_all_devices(db)

    log_action(
        db,
        action="list_compliance",
        resource="compliance",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"count": len(statuses)},
        status_code=200,
    )

    return statuses


@router.get("/compliance/{device_id}", response_model=ComplianceOut)
def compliance_for_device(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    status_row = db.query(ComplianceStatus).filter(ComplianceStatus.device_id == device_id).first()
    if not status_row:
        status_row = evaluate_device_compliance(db, device)
        db.commit()
        db.refresh(status_row)

    log_action(
        db,
        action="get_compliance",
        resource="compliance",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"device_id": device_id, "status": status_row.status},
        status_code=200,
    )

    return status_row


@router.post("/remediate/{device_id}", response_model=ComplianceOut)
def remediate(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer")),
):
    try:
        status_row = remediate_device(db, device_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    log_action(
        db,
        action="remediate_device",
        resource="compliance",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"device_id": device_id, "auto_remediated": status_row.auto_remediated},
        status_code=200,
    )

    return status_row
