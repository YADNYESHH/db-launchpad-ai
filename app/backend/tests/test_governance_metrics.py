import os

os.environ.setdefault("STORE_BACKEND", "memory")

import pytest
from fastapi.testclient import TestClient

from ..main import app

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


_CONTRACT_KEYS = {
    "total_profiles",
    "scored_profiles",
    "provenance",
    "band_counts",
    "total_pipeline_value_eur",
    "audit_event_count",
    "live_citation_count",
    "active_weight_version",
    "recommendations_generated",
    "human_approval_required",
}


def test_governance_metrics_requires_auth():
    resp = client.get("/governance/metrics")
    assert resp.status_code == 401


def test_governance_metrics_shape_and_values():
    token = _login("anna.schmidt@launchpad.demo")
    resp = client.get("/governance/metrics", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # all contract keys present
    assert _CONTRACT_KEYS.issubset(body.keys())

    # provenance sub-keys
    provenance = body["provenance"]
    assert set(provenance.keys()) == {"live_grounded", "synthetic", "public_manual"}

    # seed portfolio has at least 6 profiles
    assert body["total_profiles"] >= 6

    # provenance ints sum to total_profiles
    assert sum(int(v) for v in provenance.values()) == body["total_profiles"]

    # business value never negative
    assert body["total_pipeline_value_eur"] >= 0

    # governance invariant
    assert body["human_approval_required"] is True

    # scored profiles are a subset of the portfolio
    assert 0 <= body["scored_profiles"] <= body["total_profiles"]

    # band_counts is a mapping of ints
    assert all(isinstance(v, int) for v in body["band_counts"].values())
