from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MockInterface:
    name: str
    ip_address: str | None
    mac_address: str
    speed_mbps: int


@dataclass
class MockDevice:
    hostname: str
    management_ip: str
    os_version: str
    vendor: str
    hardware_model: str
    serial_number: str
    device_group: str
    interfaces: list[MockInterface]


MOCK_DEVICES: list[MockDevice] = [
    MockDevice(
        hostname="core-sw1",
        management_ip="10.0.0.1",
        os_version="IOS-XE 17.9",
        vendor="Cisco",
        hardware_model="C9300-24T",
        serial_number="C9300A1B2",
        device_group="corporate",
        interfaces=[
            MockInterface("Gig1/0/1", "172.16.0.1/30", "00:11:22:AA:01:01", 1000),
            MockInterface("Gig1/0/2", "172.16.0.5/30", "00:11:22:AA:01:02", 1000),
            MockInterface("Gig1/0/24", None, "00:11:22:AA:01:18", 1000),
        ],
    ),
    MockDevice(
        hostname="dist-sw1",
        management_ip="10.0.0.2",
        os_version="IOS-XE 17.6",
        vendor="Cisco",
        hardware_model="C9200-48P",
        serial_number="C9200B3C4",
        device_group="corporate",
        interfaces=[
            MockInterface("Gig1/0/1", "172.16.0.2/30", "00:11:22:AA:02:01", 1000),
            MockInterface("Gig1/0/10", "192.168.10.1/24", "00:11:22:AA:02:0A", 1000),
            MockInterface("Gig1/0/20", "192.168.30.1/24", "00:11:22:AA:02:14", 1000),
        ],
    ),
    MockDevice(
        hostname="edge-rtr1",
        management_ip="10.0.0.3",
        os_version="Junos 21.4",
        vendor="Juniper",
        hardware_model="MX204",
        serial_number="MX204X9Y8",
        device_group="edge",
        interfaces=[
            MockInterface("ge-0/0/0", "172.16.0.6/30", "00:11:22:AA:03:01", 1000),
            MockInterface("ge-0/0/1", "203.0.113.2/30", "00:11:22:AA:03:02", 1000),
            MockInterface("ge-0/0/2", "198.51.100.2/30", "00:11:22:AA:03:03", 1000),
        ],
    ),
    MockDevice(
        hostname="guest-sw1",
        management_ip="10.0.0.4",
        os_version="EOS 4.29",
        vendor="Arista",
        hardware_model="7050SX3",
        serial_number="AR7050M5N6",
        device_group="guest",
        interfaces=[
            MockInterface("Ethernet1", "172.16.0.9/30", "00:11:22:AA:04:01", 1000),
            MockInterface("Ethernet10", "192.168.30.2/24", "00:11:22:AA:04:0A", 1000),
            MockInterface("Ethernet20", None, "00:11:22:AA:04:14", 1000),
        ],
    ),
    MockDevice(
        hostname="branch-rtr1",
        management_ip="10.0.0.5",
        os_version="IOS-XE 17.3",
        vendor="Cisco",
        hardware_model="ISR4331",
        serial_number="ISR4P7Q8",
        device_group="branch",
        interfaces=[
            MockInterface("Gig0/0/0", "172.16.0.10/30", "00:11:22:AA:05:01", 1000),
            MockInterface("Gig0/0/1", "10.10.10.1/24", "00:11:22:AA:05:02", 1000),
            MockInterface("Gig0/0/2", None, "00:11:22:AA:05:03", 1000),
        ],
    ),
]


TOPOLOGY_NEIGHBORS: list[dict[str, str]] = [
    {
        "source": "core-sw1",
        "target": "dist-sw1",
        "local_interface": "Gig1/0/1",
        "remote_interface": "Gig1/0/1",
        "protocol": "LLDP",
    },
    {
        "source": "core-sw1",
        "target": "edge-rtr1",
        "local_interface": "Gig1/0/2",
        "remote_interface": "ge-0/0/0",
        "protocol": "LLDP",
    },
    {
        "source": "dist-sw1",
        "target": "guest-sw1",
        "local_interface": "Gig1/0/20",
        "remote_interface": "Ethernet1",
        "protocol": "CDP",
    },
    {
        "source": "guest-sw1",
        "target": "branch-rtr1",
        "local_interface": "Ethernet10",
        "remote_interface": "Gig0/0/0",
        "protocol": "LLDP",
    },
]


GROUP_TO_CIDR = {
    "guest": "192.168.30.0 0.0.0.255",
    "corporate": "192.168.10.0 0.0.0.255",
    "edge": "203.0.113.0 0.0.0.255",
    "branch": "10.10.10.0 0.0.0.255",
    "any": "any",
}


def get_mock_device_by_ip(ip: str) -> MockDevice | None:
    for device in MOCK_DEVICES:
        if device.management_ip == ip:
            return device
    return None


def get_baseline_config(hostname: str) -> str:
    return (
        f"hostname {hostname}\n"
        "service timestamps debug datetime msec\n"
        "service timestamps log datetime msec\n"
        "no ip http server\n"
        "line vty 0 4\n"
        " login local\n"
        " transport input ssh\n"
    )
