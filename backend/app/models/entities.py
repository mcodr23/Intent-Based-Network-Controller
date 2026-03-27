from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[list[User]] = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    role: Mapped[Role] = relationship("Role", back_populates="users")

    policies: Mapped[list[Policy]] = relationship("Policy", back_populates="creator")
    deployments: Mapped[list[Deployment]] = relationship("Deployment", back_populates="initiator")
    audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hostname: Mapped[str] = mapped_column(String(100), nullable=False)
    management_ip: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    os_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(80), nullable=True)
    hardware_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    device_group: Mapped[str] = mapped_column(String(80), default="default", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="up", nullable=False)
    current_config: Mapped[str] = mapped_column(Text, default="", nullable=False)
    desired_config: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    interfaces: Mapped[list[Interface]] = relationship("Interface", back_populates="device", cascade="all, delete-orphan")
    source_edges: Mapped[list[TopologyEdge]] = relationship(
        "TopologyEdge",
        back_populates="source_device",
        foreign_keys="TopologyEdge.source_device_id",
        cascade="all, delete-orphan",
    )
    target_edges: Mapped[list[TopologyEdge]] = relationship(
        "TopologyEdge",
        back_populates="target_device",
        foreign_keys="TopologyEdge.target_device_id",
        cascade="all, delete-orphan",
    )
    snapshots: Mapped[list[ConfigSnapshot]] = relationship("ConfigSnapshot", back_populates="device")
    telemetry_samples: Mapped[list[Telemetry]] = relationship("Telemetry", back_populates="device")
    compliance_states: Mapped[list[ComplianceStatus]] = relationship("ComplianceStatus", back_populates="device")


class Interface(Base):
    __tablename__ = "interfaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mac_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    admin_status: Mapped[str] = mapped_column(String(20), default="up")
    oper_status: Mapped[str] = mapped_column(String(20), default="up")
    speed_mbps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    device: Mapped[Device] = relationship("Device", back_populates="interfaces")

    __table_args__ = (UniqueConstraint("device_id", "name", name="uq_interface_device_name"),)


class TopologyEdge(Base):
    __tablename__ = "topology_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    target_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    local_interface: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remote_interface: Mapped[str | None] = mapped_column(String(100), nullable=True)
    protocol: Mapped[str] = mapped_column(String(20), default="LLDP")
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_device: Mapped[Device] = relationship("Device", back_populates="source_edges", foreign_keys=[source_device_id])
    target_device: Mapped[Device] = relationship("Device", back_populates="target_edges", foreign_keys=[target_device_id])


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_group: Mapped[str] = mapped_column(String(80), nullable=False)
    destination_group: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    scope: Mapped[str] = mapped_column(String(80), default="global")
    affected_devices_json: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    parameters_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structured_policy_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    creator: Mapped[User] = relationship("User", back_populates="policies")
    deployments: Mapped[list[Deployment]] = relationship("Deployment", back_populates="policy")


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    initiated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    rollback_performed: Mapped[bool] = mapped_column(Boolean, default=False)
    generated_configs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    policy: Mapped[Policy] = relationship("Policy", back_populates="deployments")
    initiator: Mapped[User] = relationship("User", back_populates="deployments")
    logs: Mapped[list[DeploymentLog]] = relationship("DeploymentLog", back_populates="deployment", cascade="all, delete-orphan")
    snapshots: Mapped[list[ConfigSnapshot]] = relationship("ConfigSnapshot", back_populates="deployment", cascade="all, delete-orphan")


class DeploymentLog(Base):
    __tablename__ = "deployment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deployment_id: Mapped[int] = mapped_column(ForeignKey("deployments.id"), nullable=False, index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"), nullable=True)
    level: Mapped[str] = mapped_column(String(20), default="INFO")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deployment: Mapped[Deployment] = relationship("Deployment", back_populates="logs")


class ConfigSnapshot(Base):
    __tablename__ = "config_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    deployment_id: Mapped[int] = mapped_column(ForeignKey("deployments.id"), nullable=False)
    before_config: Mapped[str] = mapped_column(Text, nullable=False)
    after_config: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device: Mapped[Device] = relationship("Device", back_populates="snapshots")
    deployment: Mapped[Deployment] = relationship("Deployment", back_populates="snapshots")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, index=True)
    cpu_usage: Mapped[float] = mapped_column(Float, nullable=False)
    memory_usage: Mapped[float] = mapped_column(Float, nullable=False)
    packet_errors: Mapped[int] = mapped_column(Integer, default=0)
    packet_drops: Mapped[int] = mapped_column(Integer, default=0)
    interface_stats_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    link_status_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    health_score: Mapped[float] = mapped_column(Float, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    device: Mapped[Device] = relationship("Device", back_populates="telemetry_samples")


class ComplianceStatus(Base):
    __tablename__ = "compliance_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(30), default="unknown")
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    drift_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    desired_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    live_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    auto_remediated: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device: Mapped[Device] = relationship("Device", back_populates="compliance_states")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")
