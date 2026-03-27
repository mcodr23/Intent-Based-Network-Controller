from __future__ import annotations

import ipaddress
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Device, Interface
from app.services.mock_data import MOCK_DEVICES, get_baseline_config, get_mock_device_by_ip


MAX_SCAN_HOSTS = 64


def _expand_targets(ip_targets: list[str] | None, subnet: str | None) -> list[str]:
    if ip_targets:
        return list(dict.fromkeys(ip_targets))

    if not subnet:
        return [device.management_ip for device in MOCK_DEVICES]

    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except ValueError:
        return []

    hosts = [str(host) for host in network.hosts()]
    return hosts[:MAX_SCAN_HOSTS]


def _upsert_device(db: Session, ip: str) -> Device | None:
    mock = get_mock_device_by_ip(ip)
    if not mock:
        return None

    now = datetime.now(timezone.utc)
    device = db.query(Device).filter(Device.management_ip == ip).first()
    if not device:
        device = Device(
            hostname=mock.hostname,
            management_ip=mock.management_ip,
            os_version=mock.os_version,
            vendor=mock.vendor,
            hardware_model=mock.hardware_model,
            serial_number=mock.serial_number,
            device_group=mock.device_group,
            status="up",
            current_config=get_baseline_config(mock.hostname),
            desired_config=get_baseline_config(mock.hostname),
            metadata_json={"discovered_by": "mock_discovery"},
            last_seen=now,
        )
        db.add(device)
        db.flush()
    else:
        device.hostname = mock.hostname
        device.os_version = mock.os_version
        device.vendor = mock.vendor
        device.hardware_model = mock.hardware_model
        device.serial_number = mock.serial_number
        device.device_group = mock.device_group
        device.status = "up"
        device.last_seen = now

    existing_by_name = {iface.name: iface for iface in device.interfaces}
    for mock_iface in mock.interfaces:
        iface = existing_by_name.get(mock_iface.name)
        if not iface:
            iface = Interface(
                device_id=device.id,
                name=mock_iface.name,
                ip_address=mock_iface.ip_address,
                mac_address=mock_iface.mac_address,
                speed_mbps=mock_iface.speed_mbps,
                admin_status="up",
                oper_status="up",
            )
            db.add(iface)
        else:
            iface.ip_address = mock_iface.ip_address
            iface.mac_address = mock_iface.mac_address
            iface.speed_mbps = mock_iface.speed_mbps
            iface.admin_status = "up"
            iface.oper_status = "up"

    db.flush()
    return device


def discover_devices(db: Session, ip_targets: list[str] | None = None, subnet: str | None = None) -> tuple[int, list[Device]]:
    targets = _expand_targets(ip_targets, subnet)
    discovered: list[Device] = []
    for ip in targets:
        device = _upsert_device(db, ip)
        if device:
            discovered.append(device)

    db.commit()
    for device in discovered:
        db.refresh(device)

    return len(targets), discovered
