"""Seed demo data for Intent-Based Network Controller."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal, init_db
from app.models import Policy, User
from app.schemas.schemas import IntentRequest
from app.services.auth_service import ensure_default_admin, ensure_roles
from app.services.compliance_service import evaluate_all_devices
from app.services.deployment_service import deploy_policy
from app.services.discovery_service import discover_devices
from app.services.policy_service import create_policy_from_intent
from app.services.telemetry_service import collect_all
from app.services.topology_service import rebuild_topology



def main() -> None:
    init_db()
    with SessionLocal() as db:
        ensure_roles(db)
        ensure_default_admin(db)

        discover_devices(db)
        rebuild_topology(db)
        collect_all(db)

        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            raise RuntimeError("Admin user was not created")

        existing = db.query(Policy).filter(Policy.name == "Guest to Corporate Isolation").first()
        if not existing:
            payload = IntentRequest(
                name="Guest to Corporate Isolation",
                description="Deny guest VLAN traffic towards corporate VLAN.",
                source_group="guest",
                destination_group="corporate",
                action="deny",
                scope="campus",
                parameters={"vlan_id": 30},
            )
            policy = create_policy_from_intent(db, payload, admin)
            deploy_policy(db, policy.id, admin)

        evaluate_all_devices(db)

    print("Seed complete.")


if __name__ == "__main__":
    main()
