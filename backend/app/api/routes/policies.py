from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Policy, User
from app.schemas.schemas import IntentRequest, PolicyOut
from app.services.audit_service import log_action
from app.services.policy_service import create_policy_from_intent


router = APIRouter(tags=["Policies"])


@router.post("/intent", response_model=PolicyOut)
def create_intent(
    payload: IntentRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer")),
):
    try:
        policy = create_policy_from_intent(db, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    log_action(
        db,
        action="create_intent",
        resource="policy",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"policy_id": policy.id, "policy_name": policy.name},
        status_code=201,
    )
    return policy


@router.get("/policies", response_model=list[PolicyOut])
def list_policies(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    policies = db.query(Policy).order_by(Policy.created_at.desc()).all()
    log_action(
        db,
        action="list_policies",
        resource="policy",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"count": len(policies)},
        status_code=200,
    )
    return policies


@router.get("/policies/{policy_id}", response_model=PolicyOut)
def get_policy(
    policy_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    log_action(
        db,
        action="get_policy",
        resource="policy",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"policy_id": policy_id},
        status_code=200,
    )
    return policy
