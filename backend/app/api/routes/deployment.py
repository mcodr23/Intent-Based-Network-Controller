from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Deployment, DeploymentLog, User
from app.schemas.schemas import DeployResponse, DeploymentLogOut, DeploymentOut
from app.services.audit_service import log_action
from app.services.deployment_service import deploy_policy


router = APIRouter(tags=["Deployment"])


@router.post("/deploy/{policy_id}", response_model=DeployResponse)
def deploy(
    policy_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer")),
):
    try:
        deployment = deploy_policy(db, policy_id, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    log_action(
        db,
        action="deploy_policy",
        resource="deployment",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"deployment_id": deployment.id, "policy_id": policy_id, "status": deployment.status},
        status_code=200,
    )

    return DeployResponse(
        deployment=deployment,
        message=f"Deployment {deployment.id} finished with status: {deployment.status}",
    )


@router.get("/deployments/{deployment_id}", response_model=DeploymentOut)
def get_deployment(
    deployment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")

    log_action(
        db,
        action="get_deployment",
        resource="deployment",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"deployment_id": deployment_id},
        status_code=200,
    )

    return deployment


@router.get("/deployments/{deployment_id}/logs", response_model=list[DeploymentLogOut])
def get_deployment_logs(
    deployment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    logs = (
        db.query(DeploymentLog)
        .filter(DeploymentLog.deployment_id == deployment_id)
        .order_by(DeploymentLog.created_at.asc())
        .all()
    )

    log_action(
        db,
        action="get_deployment_logs",
        resource="deployment_logs",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"deployment_id": deployment_id, "count": len(logs)},
        status_code=200,
    )

    return logs
