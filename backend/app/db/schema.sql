-- Intent-Based Network Controller schema

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role_id INTEGER NOT NULL,
    FOREIGN KEY(role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY,
    hostname VARCHAR(100) NOT NULL,
    management_ip VARCHAR(64) UNIQUE NOT NULL,
    os_version VARCHAR(120),
    vendor VARCHAR(80),
    hardware_model VARCHAR(120),
    serial_number VARCHAR(120),
    device_group VARCHAR(80) NOT NULL,
    status VARCHAR(30) NOT NULL,
    current_config TEXT NOT NULL,
    desired_config TEXT NOT NULL,
    metadata_json JSON,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interfaces (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    mac_address VARCHAR(64),
    ip_address VARCHAR(64),
    admin_status VARCHAR(20) DEFAULT 'up',
    oper_status VARCHAR(20) DEFAULT 'up',
    speed_mbps INTEGER,
    UNIQUE(device_id, name),
    FOREIGN KEY(device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS topology_edges (
    id INTEGER PRIMARY KEY,
    source_device_id INTEGER NOT NULL,
    target_device_id INTEGER NOT NULL,
    local_interface VARCHAR(100),
    remote_interface VARCHAR(100),
    protocol VARCHAR(20) DEFAULT 'LLDP',
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(source_device_id) REFERENCES devices(id),
    FOREIGN KEY(target_device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    source_group VARCHAR(80) NOT NULL,
    destination_group VARCHAR(80) NOT NULL,
    action VARCHAR(20) NOT NULL,
    scope VARCHAR(80) DEFAULT 'global',
    affected_devices_json JSON,
    parameters_json JSON,
    structured_policy_json JSON NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    FOREIGN KEY(created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS deployments (
    id INTEGER PRIMARY KEY,
    policy_id INTEGER NOT NULL,
    initiated_by INTEGER NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    rollback_performed BOOLEAN DEFAULT 0,
    generated_configs_json JSON,
    summary TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY(policy_id) REFERENCES policies(id),
    FOREIGN KEY(initiated_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS deployment_logs (
    id INTEGER PRIMARY KEY,
    deployment_id INTEGER NOT NULL,
    device_id INTEGER,
    level VARCHAR(20) DEFAULT 'INFO',
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(deployment_id) REFERENCES deployments(id),
    FOREIGN KEY(device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS config_snapshots (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    deployment_id INTEGER NOT NULL,
    before_config TEXT NOT NULL,
    after_config TEXT NOT NULL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(device_id) REFERENCES devices(id),
    FOREIGN KEY(deployment_id) REFERENCES deployments(id)
);

CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    cpu_usage FLOAT NOT NULL,
    memory_usage FLOAT NOT NULL,
    packet_errors INTEGER DEFAULT 0,
    packet_drops INTEGER DEFAULT 0,
    interface_stats_json JSON NOT NULL,
    link_status_json JSON NOT NULL,
    health_score FLOAT NOT NULL,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS compliance_status (
    id INTEGER PRIMARY KEY,
    device_id INTEGER UNIQUE NOT NULL,
    status VARCHAR(30) DEFAULT 'unknown',
    drift_detected BOOLEAN DEFAULT 0,
    drift_details TEXT,
    desired_hash VARCHAR(64),
    live_hash VARCHAR(64),
    auto_remediated BOOLEAN DEFAULT 0,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(80),
    role VARCHAR(50),
    action VARCHAR(120) NOT NULL,
    resource VARCHAR(255) NOT NULL,
    method VARCHAR(10),
    path VARCHAR(255),
    details_json JSON,
    status_code INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
