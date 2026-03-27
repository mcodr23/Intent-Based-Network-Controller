from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import audit, auth, compliance, deployment, inventory, policies, telemetry, topology
from app.core.config import FRONTEND_DIR, get_settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal, init_db
from app.models import Device, User
from app.services.audit_service import log_action
from app.services.auth_service import ensure_default_admin, ensure_roles
from app.services.compliance_service import evaluate_all_devices
from app.services.discovery_service import discover_devices
from app.services.monitor_service import MonitorManager
from app.services.telemetry_service import collect_all
from app.services.topology_service import rebuild_topology


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
monitor_manager = MonitorManager()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        ensure_roles(db)
        ensure_default_admin(db)

        devices_count = db.query(Device).count()
        if devices_count == 0:
            discover_devices(db)
            rebuild_topology(db)
            collect_all(db)
            evaluate_all_devices(db)

    await monitor_manager.start()
    yield
    await monitor_manager.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)

    if request.url.path.startswith(settings.api_prefix):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        with SessionLocal() as db:
            user = None
            if token:
                payload = decode_access_token(token)
                if payload and payload.get("user_id"):
                    user = db.query(User).filter(User.id == payload["user_id"]).first()

            log_action(
                db,
                action=f"http_{request.method.lower()}",
                resource=request.url.path,
                method=request.method,
                path=request.url.path,
                user=user,
                details={"query": dict(request.query_params)},
                status_code=response.status_code,
            )

    return response


api_prefix = settings.api_prefix
app.include_router(auth.router, prefix=api_prefix)
app.include_router(inventory.router, prefix=api_prefix)
app.include_router(topology.router, prefix=api_prefix)
app.include_router(policies.router, prefix=api_prefix)
app.include_router(deployment.router, prefix=api_prefix)
app.include_router(compliance.router, prefix=api_prefix)
app.include_router(telemetry.router, prefix=api_prefix)
app.include_router(audit.router, prefix=api_prefix)


if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/")
def root():
    return RedirectResponse(url="/frontend/pages/login.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/docs/architecture")
def architecture_doc():
    architecture_path = Path(__file__).resolve().parents[2] / "docs" / "ARCHITECTURE.md"
    if architecture_path.exists():
        return FileResponse(path=str(architecture_path))
    return {"message": "Architecture documentation not found"}
