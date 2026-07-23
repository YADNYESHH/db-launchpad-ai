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


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["synthetic_only"] is True


def test_login_rejects_bad_password():
    resp = client.post("/auth/login", data={"username": "anna.schmidt@launchpad.demo", "password": "wrong"})
    assert resp.status_code == 401


def test_full_rm_workflow_novatrade_end_to_end():
    rm_token = _login("anna.schmidt@launchpad.demo")

    # profile already seeded on startup
    resp = client.get(f"/profiles/{NOVATRADE_ID}", headers=_auth(rm_token))
    assert resp.status_code == 200
    assert resp.json()["profile"]["synthetic_flag"] is True

    # score
    resp = client.post(f"/profiles/{NOVATRADE_ID}/score", headers=_auth(rm_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["score_record"]["priority_band"] == "high_priority"
    assert body["score_record"]["missing_data_flags"] == []

    # generate recommendation (should succeed: high_priority)
    resp = client.post(
        "/recommendations/generate", json={"startup_id": NOVATRADE_ID, "force": False}, headers=_auth(rm_token)
    )
    assert resp.status_code == 200, resp.text
    rec = resp.json()
    assert rec["approval_status"] == "draft"
    assert rec["guardrail_flags"] == []
    assert "guaranteed" not in rec["client_summary"].lower()
    for phrase in ("guaranteed", "suitable for you", "approved for credit"):
        assert phrase not in rec["client_summary"].lower()
        assert phrase not in rec["why_now"].lower()
    rec_id = rec["recommendation_id"]

    # approve
    resp = client.post(
        f"/recommendations/{rec_id}/approve", json={"decision": "approved"}, headers=_auth(rm_token)
    )
    assert resp.status_code == 200
    assert resp.json()["approval_status"] == "approved"
    assert resp.json()["approver"] is not None

    # audit trail has every stage
    resp = client.get(f"/audit/{NOVATRADE_ID}", headers=_auth(rm_token))
    assert resp.status_code == 200
    event_types = [e["event_type"] for e in resp.json()]
    assert "score_calculated" in event_types
    assert "recommendation_generated" in event_types
    assert "recommendation_approved" in event_types


def test_recommendation_cannot_be_generated_without_prior_score():
    rm_token = _login("anna.schmidt@launchpad.demo")
    po_token = _login("priya.nair@launchpad.demo")

    resp = client.post(
        "/profiles",
        json={
            "profile": {
                "startup_id": "ST-UNSCORED",
                "name": "Unscored GmbH",
                "sector": "Test",
                "hq_country": "Germany",
                "growth_stage": "Seed",
                "funding_stage": "Seed",
                "annual_revenue_eur": 1000,
            }
        },
        headers=_auth(po_token),
    )
    assert resp.status_code == 201

    resp = client.post(
        "/recommendations/generate", json={"startup_id": "ST-UNSCORED", "force": True}, headers=_auth(rm_token)
    )
    assert resp.status_code == 404


def test_recommendation_blocked_for_non_high_priority_without_force():
    po_token = _login("priya.nair@launchpad.demo")
    rm_token = _login("anna.schmidt@launchpad.demo")

    resp = client.post(
        "/profiles",
        json={
            "profile": {
                "startup_id": "ST-LOW",
                "name": "LowSignal GmbH",
                "sector": "Test",
                "hq_country": "Germany",
                "growth_stage": "Seed",
                "funding_stage": "Seed",
                "annual_revenue_eur": 500_000,
            }
        },
        headers=_auth(po_token),
    )
    assert resp.status_code == 201

    resp = client.post("/profiles/ST-LOW/score", headers=_auth(rm_token))
    assert resp.status_code == 200
    assert resp.json()["score_record"]["priority_band"] != "high_priority"

    resp = client.post(
        "/recommendations/generate", json={"startup_id": "ST-LOW", "force": False}, headers=_auth(rm_token)
    )
    assert resp.status_code == 409


def test_rbac_blocks_non_rm_from_approving():
    po_token = _login("priya.nair@launchpad.demo")
    rm_token = _login("anna.schmidt@launchpad.demo")

    client.post(f"/profiles/{NOVATRADE_ID}/score", headers=_auth(rm_token))
    resp = client.post(
        "/recommendations/generate", json={"startup_id": NOVATRADE_ID, "force": False}, headers=_auth(rm_token)
    )
    rec_id = resp.json()["recommendation_id"]

    # Product Owner is not allowed to approve
    resp = client.post(
        f"/recommendations/{rec_id}/approve", json={"decision": "approved"}, headers=_auth(po_token)
    )
    assert resp.status_code == 403


def test_weight_propose_and_activate_flow():
    po_token = _login("priya.nair@launchpad.demo")
    admin_token = _login("admin@launchpad.demo")
    cr_token = _login("wei.chen@launchpad.demo")

    resp = client.get("/weights", headers=_auth(cr_token))
    assert resp.status_code == 200
    active_version = resp.json()["version_id"]

    resp = client.post(
        "/weights/propose",
        json={"change_reason": "Test recalibration after RM feedback."},
        headers=_auth(po_token),
    )
    assert resp.status_code == 201
    proposed_version = resp.json()["version_id"]
    assert proposed_version != active_version
    assert resp.json()["active"] is False

    # Control Reviewer cannot activate
    resp = client.post(f"/weights/{proposed_version}/activate", headers=_auth(cr_token))
    assert resp.status_code == 403

    # Admin can activate
    resp = client.post(f"/weights/{proposed_version}/activate", headers=_auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["active"] is True

    resp = client.get("/weights", headers=_auth(cr_token))
    assert resp.json()["version_id"] == proposed_version
