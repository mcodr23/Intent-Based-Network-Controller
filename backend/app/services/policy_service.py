from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Policy, User
from app.schemas.schemas import IntentRequest
from app.services.mock_data import GROUP_TO_CIDR


VALID_ACTIONS = {"allow", "deny"}


def _build_structured_policy(payload: IntentRequest) -> dict:
    src_cidr = GROUP_TO_CIDR.get(payload.source_group.lower(), GROUP_TO_CIDR["any"])
    dst_cidr = GROUP_TO_CIDR.get(payload.destination_group.lower(), GROUP_TO_CIDR["any"])

    acl_action = "permit" if payload.action == "allow" else "deny"

    acl_rules = [
        {
            "seq": 10,
            "action": acl_action,
            "src_group": payload.source_group,
            "dst_group": payload.destination_group,
            "src_cidr": src_cidr,
            "dst_cidr": dst_cidr,
        }
    ]

    return {
        "intent_type": "traffic_control",
        "business_intent": f"{payload.action.upper()} {payload.source_group} -> {payload.destination_group}",
        "scope": payload.scope,
        "acl_rules": acl_rules,
        "parameters": payload.parameters or {},
    }


def create_policy_from_intent(db: Session, payload: IntentRequest, user: User) -> Policy:
    action = payload.action.lower()
    if action not in VALID_ACTIONS:
        raise ValueError("Action must be allow or deny")

    structured_policy = _build_structured_policy(payload)

    policy = Policy(
        name=payload.name,
        description=payload.description,
        source_group=payload.source_group,
        destination_group=payload.destination_group,
        action=action,
        scope=payload.scope,
        affected_devices_json=payload.affected_devices,
        parameters_json=payload.parameters or {},
        structured_policy_json=structured_policy,
        created_by=user.id,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy
