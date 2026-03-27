# Intent-Based Network Controller: Architecture Plan

## End-to-End Workflow

`Discover -> Model -> Define -> Deploy -> Monitor -> Enforce`

1. **Discover**: scan IP targets/subnet, identify active devices (mocked for local demo), collect inventory.
2. **Model**: persist devices/interfaces and derive LLDP/CDP-like topology graph.
3. **Define**: accept high-level intent through API/UI and normalize into structured policy objects.
4. **Deploy**: translate policy into vendor-aware device configs via templates, push with retries and rollback.
5. **Monitor**: continuously ingest telemetry and compute health scores.
6. **Enforce**: run compliance checks, detect drift, and remediate automatically/on-demand.

## Layered Architecture

### A) Intent Layer
- FastAPI endpoints and web dashboard forms.
- JWT authentication and role-based authorization.
- Input validation through Pydantic schemas.
- Intent normalization to internal policy JSON.

### B) Control Layer
- SQLAlchemy data model for inventory, topology, policy, deployments, compliance, telemetry, and audit.
- Services:
  - `policy_service` (intent to structured policy)
  - `config_service` (policy to device config)
  - `deployment_service` (orchestration, retries, rollback)
  - `compliance_service` (intended vs live state)
  - `telemetry_service` (time-series samples and health score)

### C) Device Layer
- Mock network device catalog with per-vendor metadata.
- Simulated SSH deployment behavior and deterministic retry/failure path.
- Simulated LLDP/CDP neighbor map.

### D) Assurance Layer
- Background monitor loops for telemetry and compliance.
- Drift simulation for demo visibility.
- On-demand remediation endpoint.

## Data Model Coverage

Implemented entities:
- `users`
- `roles`
- `devices`
- `interfaces`
- `topology_edges`
- `policies`
- `deployments`
- `deployment_logs`
- `config_snapshots`
- `telemetry`
- `audit_logs`
- `compliance_status`

## Agile Milestones

1. **Milestone 1**: auth, RBAC, DB schema, baseline inventory APIs.
2. **Milestone 2**: discovery + topology graph persistence.
3. **Milestone 3**: intent/policy engine + template configuration generation.
4. **Milestone 4**: multi-device deployment orchestration with rollback.
5. **Milestone 5**: compliance, drift detection, remediation.
6. **Milestone 6**: telemetry pipeline and dashboard pages.
7. **Milestone 7**: audit logging, tests, seed data, demo documentation.
