from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.compliance_service import evaluate_all_devices, simulate_drift
from app.services.telemetry_service import collect_all


logger = logging.getLogger(__name__)


class MonitorManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tasks = [
            asyncio.create_task(self._telemetry_loop(), name="telemetry_loop"),
            asyncio.create_task(self._compliance_loop(), name="compliance_loop"),
        ]

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    async def _telemetry_loop(self) -> None:
        while self._running:
            try:
                with SessionLocal() as db:
                    collect_all(db)
            except Exception as exc:
                logger.exception("Telemetry loop error: %s", exc)
            await asyncio.sleep(self.settings.telemetry_interval_seconds)

    async def _compliance_loop(self) -> None:
        while self._running:
            try:
                with SessionLocal() as db:
                    simulate_drift(db)
                    evaluate_all_devices(db)
            except Exception as exc:
                logger.exception("Compliance loop error: %s", exc)
            await asyncio.sleep(self.settings.compliance_interval_seconds)
