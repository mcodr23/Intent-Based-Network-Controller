from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.schemas import TopologyNode, TopologyResponse
from app.services.audit_service import log_action
from app.services.topology_service import get_topology


router = APIRouter(tags=["Topology"])


@router.get("/topology", response_model=TopologyResponse)
def topology(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin", "Network Engineer", "Viewer")),
):
    devices, edges = get_topology(db)

    nodes = [
        TopologyNode(id=device.id, hostname=device.hostname, management_ip=device.management_ip, group=device.device_group)
        for device in devices
    ]

    log_action(
        db,
        action="view_topology",
        resource="topology",
        method=request.method,
        path=request.url.path,
        user=user,
        details={"nodes": len(nodes), "edges": len(edges)},
        status_code=200,
    )

    return TopologyResponse(nodes=nodes, edges=edges)
