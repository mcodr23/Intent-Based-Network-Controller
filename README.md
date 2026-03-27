# Intent-Based Network Controller System

A complete, demo-ready minor project implementing an **Intent-Based Network Controller** with this workflow:

**Discover -> Model -> Define -> Deploy -> Monitor -> Enforce**

It runs fully on a local machine using a **mock device layer** (simulated SSH/SNMP/LLDP/CDP behavior) while keeping production-style architecture and APIs.

## 1) Project Folder Structure

```text
New project/
+-- backend/
¦   +-- app/
¦   ¦   +-- api/
¦   ¦   ¦   +-- deps.py
¦   ¦   ¦   +-- routes/
¦   ¦   ¦       +-- auth.py
¦   ¦   ¦       +-- inventory.py
¦   ¦   ¦       +-- topology.py
¦   ¦   ¦       +-- policies.py
¦   ¦   ¦       +-- deployment.py
¦   ¦   ¦       +-- compliance.py
¦   ¦   ¦       +-- telemetry.py
¦   ¦   ¦       +-- audit.py
¦   ¦   +-- core/
¦   ¦   ¦   +-- config.py
¦   ¦   ¦   +-- security.py
¦   ¦   +-- db/
¦   ¦   ¦   +-- base.py
¦   ¦   ¦   +-- session.py
¦   ¦   ¦   +-- schema.sql
¦   ¦   +-- models/
¦   ¦   ¦   +-- entities.py
¦   ¦   +-- schemas/
¦   ¦   ¦   +-- schemas.py
¦   ¦   +-- services/
¦   ¦   ¦   +-- auth_service.py
¦   ¦   ¦   +-- discovery_service.py
¦   ¦   ¦   +-- topology_service.py
¦   ¦   ¦   +-- policy_service.py
¦   ¦   ¦   +-- config_service.py
¦   ¦   ¦   +-- deployment_service.py
¦   ¦   ¦   +-- compliance_service.py
¦   ¦   ¦   +-- telemetry_service.py
¦   ¦   ¦   +-- monitor_service.py
¦   ¦   ¦   +-- audit_service.py
¦   ¦   ¦   +-- mock_data.py
¦   ¦   +-- templates/
¦   ¦   ¦   +-- acl_config.j2
¦   ¦   +-- main.py
¦   +-- tests/
¦   ¦   +-- conftest.py
¦   ¦   +-- test_api_flow.py
¦   +-- requirements.txt
¦   +-- Dockerfile
+-- frontend/
¦   +-- css/style.css
¦   +-- js/app.js
¦   +-- pages/
¦       +-- login.html
¦       +-- dashboard.html
¦       +-- devices.html
¦       +-- topology.html
¦       +-- policies.html
¦       +-- deployment.html
¦       +-- compliance.html
¦       +-- telemetry.html
¦       +-- audit.html
+-- docs/
¦   +-- ARCHITECTURE.md
¦   +-- sample_payloads.json
+-- scripts/
¦   +-- seed_data.py
+-- docker-compose.yml
+-- README.md
```

## 2) Layered Architecture (Implemented)

### A. Intent Layer
- FastAPI + frontend forms for intent input
- JWT auth + RBAC (`Admin`, `Network Engineer`, `Viewer`)
- Intent validation and normalization

### B. Control Layer
- Central DB-backed state store
- Inventory, topology, policies, deployments, snapshots, compliance, telemetry metadata, audit
- Orchestration and policy translation engines

### C. Device Layer
- Mock devices with vendor/OS/interface metadata
- Simulated SSH config deployment with retries/failures/rollback
- Simulated LLDP/CDP neighbor relationships

### D. Assurance Layer
- Background telemetry collection
- Intended vs live config comparison
- Drift detection + remediation endpoint

## 3) Core Modules Delivered

1. Device Discovery & Inventory
2. Topology Discovery
3. Intent & Policy Engine
4. Policy Translation & Config Generation (Jinja2 templates)
5. Multi-Device Deployment & Orchestration (retries + rollback + logs)
6. Compliance & Drift Detection
7. Telemetry & Health Monitoring
8. REST API + JWT + RBAC + Audit Logging
9. Frontend Dashboard pages for all required views

## 4) Database Entities

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

Schema SQL: `backend/app/db/schema.sql`

## 5) API Endpoints (Implemented)

### Authentication
- `POST /api/login`
- `POST /api/register`

### Inventory
- `GET /api/devices`
- `POST /api/discovery/start`
- `GET /api/devices/{id}`

### Topology
- `GET /api/topology`

### Policies
- `POST /api/intent`
- `GET /api/policies`
- `GET /api/policies/{id}`

### Deployment
- `POST /api/deploy/{policy_id}`
- `GET /api/deployments/{id}`
- `GET /api/deployments/{id}/logs`

### Compliance
- `GET /api/compliance`
- `GET /api/compliance/{device_id}`
- `POST /api/remediate/{device_id}`

### Telemetry
- `GET /api/telemetry`
- `GET /api/telemetry/{device_id}`

### Audit
- `GET /api/audit`

## 6) Setup and Run Instructions

## Prerequisites
- Python 3.11+ (tested with 3.12)

## Local Run
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open:
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Dashboard login: [http://localhost:8000/frontend/pages/login.html](http://localhost:8000/frontend/pages/login.html)

## Default Admin
- Username: `admin`
- Password: `admin123`

## Optional Seed Script
```bash
cd backend
python ..\scripts\seed_data.py
```

## Optional Docker Compose
```bash
docker compose up --build
```

## 7) Tests

```bash
cd backend
python -m pytest tests -q
```

Current result: **2 passed**.

## 8) Demo Steps (Review/Viva Friendly)

1. Login as `admin/admin123`.
2. Go to **Devices** and run discovery (`10.0.0.0/29` or blank).
3. Open **Topology** and show discovered nodes/edges.
4. Go to **Policies** and create intent:
   - source: `guest`
   - destination: `corporate`
   - action: `deny`
5. Deploy from **Policies** or **Deployment** page.
6. Show deployment logs, retries, and rollback behavior.
7. Open **Compliance** and show drift/compliance state.
8. Trigger **Remediate** when drift is present.
9. Open **Telemetry** to show CPU/memory/errors/health scores.
10. Open **Audit** to show user action history.

## 9) Agile Milestone Plan (Implemented Order)

1. Auth + RBAC + DB entities
2. Discovery + inventory + topology
3. Intent normalization + policy storage
4. Template translation + deployment orchestration
5. Compliance + drift + remediation
6. Telemetry + health scoring
7. Dashboard pages + audit + tests + docs

## 10) Sample JSON Payloads

See: `docs/sample_payloads.json`

## 11) How Each Module Works

- **Discovery Service**: scans targets/subnet, matches mock device catalog, upserts inventory/interfaces.
- **Topology Service**: converts LLDP/CDP-style neighbor mock data to `topology_edges`.
- **Policy Service**: transforms business intent into structured ACL policy JSON.
- **Config Service**: renders device-level config from Jinja template (`acl_config.j2`).
- **Deployment Service**: orchestrates multi-device push, retries failed pushes, logs each stage, snapshots config, and rolls back if needed.
- **Compliance Service**: hashes desired/live configs, generates diffs, tracks drift, and remediates.
- **Telemetry Service**: generates time-series-like metrics and computes per-device health score.
- **Monitor Service**: background loop for periodic telemetry and compliance checks.
- **Audit Service**: stores API/user actions for traceability.

## 12) Notes

- This implementation is intentionally **demo-first** and fully local.
- Real SSH/SNMP adapters can be plugged into the service layer by replacing mock functions.
- DB defaults to SQLite for quick run; PostgreSQL is supported through `DATABASE_URL`.
