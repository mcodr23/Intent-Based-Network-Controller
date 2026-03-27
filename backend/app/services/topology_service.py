from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Device, TopologyEdge
from app.services.mock_data import TOPOLOGY_NEIGHBORS


def rebuild_topology(db: Session) -> list[TopologyEdge]:
    devices = db.query(Device).all()
    by_hostname = {device.hostname: device for device in devices}

    db.query(TopologyEdge).delete()
    db.flush()

    edges: list[TopologyEdge] = []
    now = datetime.now(timezone.utc)
    for neighbor in TOPOLOGY_NEIGHBORS:
        source = by_hostname.get(neighbor["source"])
        target = by_hostname.get(neighbor["target"])
        if not source or not target:
            continue

        edge = TopologyEdge(
            source_device_id=source.id,
            target_device_id=target.id,
            local_interface=neighbor["local_interface"],
            remote_interface=neighbor["remote_interface"],
            protocol=neighbor["protocol"],
            last_seen=now,
        )
        db.add(edge)
        edges.append(edge)

    db.commit()
    for edge in edges:
        db.refresh(edge)

    return edges


def get_topology(db: Session) -> tuple[list[Device], list[TopologyEdge]]:
    devices = db.query(Device).all()
    edges = db.query(TopologyEdge).all()
    return devices, edges
