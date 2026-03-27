from fastapi import APIRouter, Depends, Request
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import AuditLog, User
from app.schemas.schemas import AuditLogOut
from app.services.audit_service import log_action


router = APIRouter(tags=["Audit"])


@router.get("/audit", response_model=list[AuditLogOut])
def list_audit_logs(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer")),
):
    logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(300).all()

    log_action(
        db,
        action="list_audit_logs",
        resource="audit",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"returned": len(logs)},
        status_code=200,
    )

    return logs
