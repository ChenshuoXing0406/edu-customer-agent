import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


_test_data_dir = Path(tempfile.mkdtemp(prefix="edu-agent-tests-"))
_test_database_path = _test_data_dir / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_test_database_path.as_posix()}"
os.environ.pop("LLM_BASE_URL", None)
os.environ.pop("LLM_API_KEY", None)
os.environ.pop("LLM_MODEL", None)

from app.core.database import Base, engine, initialize_database
from app.main import app


@pytest.fixture(autouse=True)
def reset_database(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    Base.metadata.drop_all(bind=engine)
    initialize_database()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    shutil.rmtree(_test_data_dir, ignore_errors=True)
