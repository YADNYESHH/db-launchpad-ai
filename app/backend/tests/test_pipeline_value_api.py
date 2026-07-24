import os

os.environ.setdefault("STORE_BACKEND", "memory")

import pytest
from fastapi.testclient import TestClient

from ..main import app
from ..seed.data import NOVATRADE_ID

# TestClient must be used as a context manager for FastAPI's lifespan
# startup/shutdown hooks (our demo-data seeding) to actually run.
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


def test_profile_bundle_has_pipeline_value():
    token = _login("anna.schmidt@launchpad.demo")
    resp = client.get(f"/profiles/{NOVATRADE_ID}", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["score"] is not None
    pv = body["pipeline_value"]
    assert pv is not None
    assert pv["estimated_annual_bank_revenue_eur"] > 0
    assert isinstance(pv["breakdown"], dict)
    assert pv["basis"]


def test_portfolio_summary():
    token = _login("anna.schmidt@launchpad.demo")
    resp = client.get("/portfolio/summary", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {
        "total_pipeline_value_eur",
        "band_counts",
        "scored_count",
        "total_count",
    }
    assert body["total_pipeline_value_eur"] > 0
    assert body["total_count"] >= 6
    assert isinstance(body["band_counts"], dict)
    assert body["scored_count"] <= body["total_count"]
