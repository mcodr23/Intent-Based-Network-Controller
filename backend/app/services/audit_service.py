from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def log_action(
    db: Session,
    *,
    action: str,
    resource: str,
    method: str | None = None,
    path: str | None = None,
    user: User | None = None,
    details: dict | None = None,
    status_code: int | None = None,
) -> None:
    entry = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        role=user.role.name if user and user.role else None,
        action=action,
        resource=resource,
        method=method,
        path=path,
        details_json=details,
        status_code=status_code,
    )
    db.add(entry)
    db.commit()
