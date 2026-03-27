from __future__ import annotations

import difflib
import hashlib
import random
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import ComplianceStatus, Device


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def evaluate_device_compliance(db: Session, device: Device, auto_remediate: bool = False) -> ComplianceStatus:
    desired = (device.desired_config or "").strip()
    live = (device.current_config or "").strip()

    desired_hash = _hash_text(desired)
    live_hash = _hash_text(live)
    drift_detected = desired_hash != live_hash

    diff_text = None
    auto_remediated = False

    if drift_detected:
        diff = difflib.unified_diff(
            desired.splitlines(),
            live.splitlines(),
            fromfile="desired",
            tofile="live",
            lineterm="",
        )
        diff_lines = list(diff)
        diff_text = "\n".join(diff_lines[:120])

        if auto_remediate:
            device.current_config = device.desired_config
            live_hash = desired_hash
            drift_detected = False
            diff_text = "Auto-remediated: live config restored to desired state"
            auto_remediated = True

    status_text = "compliant" if not drift_detected else "drift"

    compliance = db.query(ComplianceStatus).filter(ComplianceStatus.device_id == device.id).first()
    if not compliance:
        compliance = ComplianceStatus(device_id=device.id)
        db.add(compliance)

    compliance.status = status_text
    compliance.drift_detected = drift_detected
    compliance.drift_details = diff_text
    compliance.desired_hash = desired_hash
    compliance.live_hash = live_hash
    compliance.auto_remediated = auto_remediated
    compliance.last_checked = datetime.now(timezone.utc)

    db.flush()
    return compliance


def evaluate_all_devices(db: Session, auto_remediate: bool | None = None) -> list[ComplianceStatus]:
    settings = get_settings()
    remediate = settings.auto_remediate if auto_remediate is None else auto_remediate

    devices = db.query(Device).all()
    results = [evaluate_device_compliance(db, device, auto_remediate=remediate) for device in devices]
    db.commit()

    for row in results:
        db.refresh(row)

    return results


def remediate_device(db: Session, device_id: int) -> ComplianceStatus:
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise ValueError("Device not found")

    status = evaluate_device_compliance(db, device, auto_remediate=True)
    db.commit()
    db.refresh(status)
    return status


def simulate_drift(db: Session) -> Device | None:
    settings = get_settings()
    if not settings.enable_drift_simulation:
        return None

    devices = db.query(Device).all()
    candidates = [device for device in devices if device.desired_config]
    if not candidates:
        return None

    if random.random() > 0.2:
        return None

    victim = random.choice(candidates)
    victim.current_config = victim.current_config + "\n! unauthorized change: ip route 0.0.0.0/0 203.0.113.254\n"
    db.commit()
    db.refresh(victim)
    return victim
