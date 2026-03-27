from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = Field(default="Viewer")


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    role: RoleOut

    model_config = {"from_attributes": True}


class InterfaceOut(BaseModel):
    id: int
    name: str
    ip_address: str | None = None
    mac_address: str | None = None
    admin_status: str
    oper_status: str
    speed_mbps: int | None = None

    model_config = {"from_attributes": True}


class DeviceOut(BaseModel):
    id: int
    hostname: str
    management_ip: str
    os_version: str | None = None
    vendor: str | None = None
    hardware_model: str | None = None
    serial_number: str | None = None
    device_group: str
    status: str
    last_seen: datetime

    model_config = {"from_attributes": True}


class DeviceDetailOut(DeviceOut):
    interfaces: list[InterfaceOut] = []
    desired_config: str = ""
    current_config: str = ""


class DiscoveryRequest(BaseModel):
    ip_targets: list[str] | None = None
    subnet: str | None = None


class DiscoveryResponse(BaseModel):
    scanned: int
    discovered: int
    devices: list[DeviceOut]


class TopologyNode(BaseModel):
    id: int
    hostname: str
    management_ip: str
    group: str


class TopologyEdgeOut(BaseModel):
    source_device_id: int
    target_device_id: int
    local_interface: str | None = None
    remote_interface: str | None = None
    protocol: str
    last_seen: datetime

    model_config = {"from_attributes": True}


class TopologyResponse(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdgeOut]


class IntentRequest(BaseModel):
    name: str
    description: str | None = None
    source_group: str
    destination_group: str
    action: str = Field(pattern="^(allow|deny)$")
    scope: str = "global"
    affected_devices: list[int] | None = None
    parameters: dict[str, Any] | None = None


class PolicyOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    source_group: str
    destination_group: str
    action: str
    scope: str
    affected_devices_json: list[int] | None = None
    parameters_json: dict[str, Any] | None = None
    structured_policy_json: dict[str, Any]
    enabled: bool
    created_at: datetime
    created_by: int

    model_config = {"from_attributes": True}


class DeploymentLogOut(BaseModel):
    id: int
    deployment_id: int
    device_id: int | None = None
    level: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DeploymentOut(BaseModel):
    id: int
    policy_id: int
    initiated_by: int
    status: str
    retry_count: int
    rollback_performed: bool
    generated_configs_json: dict[str, str] | None = None
    summary: str | None = None
    started_at: datetime
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}


class DeployResponse(BaseModel):
    deployment: DeploymentOut
    message: str


class ComplianceOut(BaseModel):
    device_id: int
    status: str
    drift_detected: bool
    drift_details: str | None = None
    desired_hash: str | None = None
    live_hash: str | None = None
    auto_remediated: bool
    last_checked: datetime

    model_config = {"from_attributes": True}


class TelemetryOut(BaseModel):
    id: int
    device_id: int
    cpu_usage: float
    memory_usage: float
    packet_errors: int
    packet_drops: int
    interface_stats_json: dict[str, Any]
    link_status_json: dict[str, Any]
    health_score: float
    collected_at: datetime

    model_config = {"from_attributes": True}


class TelemetryLatestOut(BaseModel):
    device_id: int
    hostname: str
    cpu_usage: float
    memory_usage: float
    packet_errors: int
    packet_drops: int
    health_score: float
    collected_at: datetime


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None = None
    username: str | None = None
    role: str | None = None
    action: str
    resource: str
    method: str | None = None
    path: str | None = None
    details_json: dict[str, Any] | None = None
    status_code: int | None = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    message: str


TokenResponse.model_rebuild()
