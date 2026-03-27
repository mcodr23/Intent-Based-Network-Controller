from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import ConfigSnapshot, Deployment, DeploymentLog, Device, Policy, User
from app.services.config_service import generate_device_config


def _add_log(db: Session, deployment_id: int, message: str, level: str = "INFO", device_id: int | None = None) -> None:
    log = DeploymentLog(
        deployment_id=deployment_id,
        device_id=device_id,
        level=level,
        message=message,
    )
    db.add(log)
    db.flush()


def _simulate_push(policy: Policy, device: Device, attempt: int, max_retries: int) -> bool:
    params = policy.parameters_json or {}
    forced = set(params.get("force_fail_devices", []))
    if device.id in forced:
        return False

    # Deterministic failure on first attempt for branch router to demonstrate retry behavior.
    if device.hostname.startswith("branch") and attempt == 0:
        return False

    # Optionally fail once when action is deny to simulate more complex device checks.
    if policy.action == "deny" and device.device_group == "guest" and attempt < min(1, max_retries):
        return False

    return True


def _resolve_target_devices(db: Session, policy: Policy) -> list[Device]:
    if policy.affected_devices_json:
        return db.query(Device).filter(Device.id.in_(policy.affected_devices_json)).all()

    groups = {policy.source_group.lower(), policy.destination_group.lower()}
    devices = db.query(Device).all()
    matched = [device for device in devices if device.device_group.lower() in groups]
    return matched or devices


def deploy_policy(db: Session, policy_id: int, user: User, max_retries: int = 2, rollback_on_failure: bool = True) -> Deployment:
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise ValueError("Policy not found")

    target_devices = _resolve_target_devices(db, policy)
    if not target_devices:
        raise ValueError("No target devices available for this policy")

    deployment = Deployment(
        policy_id=policy.id,
        initiated_by=user.id,
        status="running",
        retry_count=0,
        rollback_performed=False,
        generated_configs_json={},
        summary="Deployment in progress",
    )
    db.add(deployment)
    db.flush()

    _add_log(db, deployment.id, f"Starting deployment for policy {policy.name}")

    successful_devices: list[tuple[Device, str]] = []
    failed_devices: list[Device] = []
    generated_configs: dict[str, str] = {}

    for device in target_devices:
        before_config = device.current_config
        _add_log(db, deployment.id, "Taking pre-deployment config snapshot", device_id=device.id)

        try:
            candidate_config = generate_device_config(policy, device)
            generated_configs[str(device.id)] = candidate_config
        except Exception as exc:
            failed_devices.append(device)
            _add_log(
                db,
                deployment.id,
                f"Config generation failed for {device.hostname}: {exc}",
                level="ERROR",
                device_id=device.id,
            )
            continue

        pushed = False
        for attempt in range(max_retries + 1):
            if attempt > 0:
                deployment.retry_count += 1
                _add_log(
                    db,
                    deployment.id,
                    f"Retrying push (attempt {attempt + 1}/{max_retries + 1})",
                    level="WARN",
                    device_id=device.id,
                )

            if _simulate_push(policy, device, attempt, max_retries):
                pushed = True
                break

        if pushed:
            device.current_config = (before_config.strip() + "\n\n" + candidate_config.strip() + "\n").strip() + "\n"
            device.desired_config = device.current_config
            snapshot = ConfigSnapshot(
                device_id=device.id,
                deployment_id=deployment.id,
                before_config=before_config,
                after_config=device.current_config,
            )
            db.add(snapshot)
            successful_devices.append((device, before_config))
            _add_log(db, deployment.id, f"Configuration applied on {device.hostname}", device_id=device.id)
        else:
            failed_devices.append(device)
            snapshot = ConfigSnapshot(
                device_id=device.id,
                deployment_id=deployment.id,
                before_config=before_config,
                after_config=before_config,
            )
            db.add(snapshot)
            _add_log(
                db,
                deployment.id,
                f"Failed to deploy on {device.hostname} after {max_retries + 1} attempts",
                level="ERROR",
                device_id=device.id,
            )

    if failed_devices and rollback_on_failure:
        for device, previous_config in successful_devices:
            device.current_config = previous_config
            device.desired_config = previous_config
            _add_log(db, deployment.id, f"Rollback executed on {device.hostname}", level="WARN", device_id=device.id)
        deployment.rollback_performed = True
        deployment.status = "failed"
    elif failed_devices and successful_devices:
        deployment.status = "partial"
    elif failed_devices:
        deployment.status = "failed"
    else:
        deployment.status = "success"

    deployment.generated_configs_json = generated_configs
    deployment.summary = (
        f"Total devices: {len(target_devices)}, Success: {len(successful_devices)}, "
        f"Failed: {len(failed_devices)}, Rollback: {deployment.rollback_performed}"
    )
    deployment.ended_at = datetime.now(timezone.utc)

    _add_log(db, deployment.id, deployment.summary)

    db.commit()
    db.refresh(deployment)
    return deployment
