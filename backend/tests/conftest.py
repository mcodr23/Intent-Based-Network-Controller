import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Must be set before importing app modules that read settings.
os.environ["DATABASE_URL"] = "sqlite:///./test_intent_controller.db"
os.environ["ENABLE_DRIFT_SIMULATION"] = "false"

from app.core.config import get_settings

get_settings.cache_clear()

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    test_db = Path("test_intent_controller.db")
    if test_db.exists():
        try:
            test_db.unlink()
        except PermissionError:
            pass


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def auth_header(client: TestClient):
    login = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
