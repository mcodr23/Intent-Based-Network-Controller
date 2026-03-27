from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.models import Device, Policy


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"


env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)


def _normalize_acl_rule(rule: dict) -> dict:
    src_cidr = rule.get("src_cidr", "any")
    dst_cidr = rule.get("dst_cidr", "any")

    # Junos wants prefix syntax; ACL format can still be retained for Cisco/Arista.
    src_prefix = src_cidr.replace(" 0.0.0.255", "/24").replace("any", "0.0.0.0/0")
    dst_prefix = dst_cidr.replace(" 0.0.0.255", "/24").replace("any", "0.0.0.0/0")

    return {
        "action": rule.get("action", "deny"),
        "src_cidr": src_cidr,
        "dst_cidr": dst_cidr,
        "src_prefix": src_prefix,
        "dst_prefix": dst_prefix,
    }


def validate_config(config_text: str) -> None:
    stripped = config_text.strip()
    if not stripped:
        raise ValueError("Generated configuration is empty")

    if "IBN" not in stripped:
        raise ValueError("Generated configuration does not include policy markers")

    if "None" in stripped:
        raise ValueError("Generated configuration contains unresolved values")


def generate_device_config(policy: Policy, device: Device) -> str:
    template = env.get_template("acl_config.j2")

    structured = policy.structured_policy_json or {}
    acl_rules = [_normalize_acl_rule(rule) for rule in structured.get("acl_rules", [])]
    if not acl_rules:
        acl_rules = [{"action": "deny", "src_cidr": "any", "dst_cidr": "any", "src_prefix": "0.0.0.0/0", "dst_prefix": "0.0.0.0/0"}]

    preferred_interface = (device.interfaces[0].name if device.interfaces else "Gig1/0/1")
    vlan_id = None
    if policy.parameters_json:
        vlan_id = policy.parameters_json.get("vlan_id") or policy.parameters_json.get("guest_vlan")

    config = template.render(
        policy_id=policy.id,
        policy_name=policy.name,
        vendor=device.vendor,
        hostname=device.hostname,
        interface_name=preferred_interface,
        acl_rules=acl_rules,
        vlan_id=vlan_id,
    )
    validate_config(config)
    return config.strip() + "\n"
