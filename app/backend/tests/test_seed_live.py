import os

os.environ.setdefault("STORE_BACKEND", "memory")

import pytest
from fastapi.testclient import TestClient

from .. import orchestrator
from ..discovery import seed_live
from ..main import app
from ..store import get_store

# TestClient as a context manager so FastAPI lifespan (synthetic seeding) runs.
_client_cm = TestClient(app)
client = _client_cm.__enter__()


@pytest.fixture(scope="module", autouse=True)
def _close_client():
    yield
    _client_cm.__exit__(None, None, None)


def _login(email: str, password: str = "demo1234") -> str:
    resp = client.post("/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_seed_live_portfolio_is_defensive(monkeypatch):
    """One failing sector must not abort the rest; failures land in reasons."""
    store = get_store()
    seen: list[str] = []

    def fake_run_discovery(store, sector, actor, limit=4):
        seen.append(sector)
        if sector == "boom":
            raise RuntimeError("no GCP creds")
        return {"sector": sector, "discovered": [{"status": "discovered", "name": sector}], "reason": None}

    monkeypatch.setattr(orchestrator, "run_discovery", fake_run_discovery)

    result = seed_live.seed_live_portfolio(
        store, actor="system", sectors=["alpha", "boom", "beta"], per_sector=2
    )

    # Every sector was attempted despite the middle one raising.
    assert seen == ["alpha", "boom", "beta"]
    # Two good sectors each added one startup.
    assert result["added"] == 2
    assert result["live"] is True
    assert result["sectors"] == ["alpha", "boom", "beta"]
    # The failure is recorded, not raised.
    assert any("boom" in reason for reason in result["reasons"])


def test_seed_live_portfolio_reports_not_live_when_nothing_added(monkeypatch):
    store = get_store()

    def empty_run_discovery(store, sector, actor, limit=4):
        return {"sector": sector, "discovered": [], "reason": "grounding unavailable"}

    monkeypatch.setattr(orchestrator, "run_discovery", empty_run_discovery)

    result = seed_live.seed_live_portfolio(store, actor="system", sectors=["one", "two"])
    assert result["added"] == 0
    assert result["live"] is False
    assert len(result["reasons"]) == 2


def test_seed_portfolio_endpoint_authorized(monkeypatch):
    """Authorized role gets 200 and the documented response shape, with the
    discovery layer stubbed so no real network/LLM call happens."""

    def fake_run_discovery(store, sector, actor, limit=4):
        return {
            "sector": sector,
            "discovered": [{"status": "discovered", "name": f"{sector}-co"}],
            "reason": None,
        }

    monkeypatch.setattr(orchestrator, "run_discovery", fake_run_discovery)

    token = _login("anna.schmidt@launchpad.demo")
    resp = client.post(
        "/discovery/seed-portfolio",
        json={"sectors": ["fintech", "logistics"], "per_sector": 1},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    for key in ("added", "sectors", "reasons", "live", "total_profiles"):
        assert key in body
    assert body["added"] == 2
    assert body["live"] is True
    assert body["sectors"] == ["fintech", "logistics"]
    assert body["total_profiles"] >= 2


def test_seed_portfolio_endpoint_forbidden_for_control_reviewer(monkeypatch):
    def fake_run_discovery(store, sector, actor, limit=4):
        return {"sector": sector, "discovered": [], "reason": None}

    monkeypatch.setattr(orchestrator, "run_discovery", fake_run_discovery)

    token = _login("wei.chen@launchpad.demo")  # Control Reviewer
    resp = client.post("/discovery/seed-portfolio", json={}, headers=_auth(token))
    assert resp.status_code == 403
