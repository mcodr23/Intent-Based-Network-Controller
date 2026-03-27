from __future__ import annotations

import random
from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import Device, Telemetry


def _compute_health(cpu: float, memory: float, errors: int, drops: int) -> float:
    score = 100.0
    score -= cpu * 0.35
    score -= memory * 0.30
    score -= min(20, errors * 1.5)
    score -= min(20, drops * 1.2)
    return max(0.0, round(score, 2))


def collect_for_device(db: Session, device: Device) -> Telemetry:
    seed = int(datetime.now(timezone.utc).timestamp()) // 10 + device.id
    rnd = random.Random(seed)

    cpu = round(rnd.uniform(15.0, 88.0), 2)
    memory = round(rnd.uniform(20.0, 92.0), 2)
    errors = rnd.randint(0, 10)
    drops = rnd.randint(0, 8)

    interface_stats: dict[str, dict[str, float | int]] = {}
    link_status: dict[str, str] = {}
    for iface in device.interfaces:
        util = round(rnd.uniform(5.0, 95.0), 2)
        iface_errors = rnd.randint(0, 3)
        iface_drops = rnd.randint(0, 2)
        interface_stats[iface.name] = {
            "utilization": util,
            "errors": iface_errors,
            "drops": iface_drops,
        }
        link_status[iface.name] = "up" if rnd.random() > 0.05 else "down"

    health = _compute_health(cpu, memory, errors, drops)

    sample = Telemetry(
        device_id=device.id,
        cpu_usage=cpu,
        memory_usage=memory,
        packet_errors=errors,
        packet_drops=drops,
        interface_stats_json=interface_stats,
        link_status_json=link_status,
        health_score=health,
        collected_at=datetime.now(timezone.utc),
    )
    db.add(sample)
    db.flush()
    return sample


def collect_all(db: Session) -> list[Telemetry]:
    devices = db.query(Device).all()
    samples = [collect_for_device(db, device) for device in devices]
    db.commit()
    for sample in samples:
        db.refresh(sample)
    return samples


def get_latest_for_all(db: Session) -> list[dict]:
    devices = db.query(Device).all()
    data: list[dict] = []

    for device in devices:
        latest = (
            db.query(Telemetry)
            .filter(Telemetry.device_id == device.id)
            .order_by(desc(Telemetry.collected_at))
            .first()
        )
        if not latest:
            continue
        data.append(
            {
                "device_id": device.id,
                "hostname": device.hostname,
                "cpu_usage": latest.cpu_usage,
                "memory_usage": latest.memory_usage,
                "packet_errors": latest.packet_errors,
                "packet_drops": latest.packet_drops,
                "health_score": latest.health_score,
                "collected_at": latest.collected_at,
            }
        )

    return data
