"""Integration tests for FastAPI endpoints and Slack webhook handler."""

import pytest
import json
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ResolveFlow"


def test_readiness_check_endpoint():
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["currency"] == "AUD"


def test_dispute_ingest_and_slack_resolution_flow():
    # 1. Ingest dispute ticket that requires approval (> $100)
    ingest_payload = {
        "customer_email": "jane.doe@example.com.au",
        "customer_name": "Jane Doe",
        "transaction_id": "ch_3N8au82eZvKYlo2C1g9X8xYz",
        "tracking_number": "AP982347102AU",
        "amount_aud": 285.00,
        "claim_type": "ITEM_NOT_RECEIVED",
        "evidence_notes": "Goods not received.",
    }

    ingest_res = client.post("/api/v1/disputes/ingest", json=ingest_payload)
    assert ingest_res.status_code == 200
    data = ingest_res.json()
    assert data["status"] == "PAUSED_PENDING_APPROVAL"
    assert data["is_interrupted"] is True
    thread_id = data["thread_id"]
    ticket_id = data["ticket_id"]

    # 2. Query state endpoint
    state_res = client.get(f"/api/v1/disputes/{thread_id}/state")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["is_paused"] is True

    # 3. Simulate Slack interactive button click to Reject Dispute
    slack_payload = {
        "user": {"id": "U12345", "username": "ops_manager_sydney"},
        "actions": [
            {
                "action_id": "btn_reject_dispute",
                "value": json.dumps({
                    "ticket_id": ticket_id,
                    "thread_id": thread_id,
                    "action": "REJECT",
                }),
            }
        ],
    }

    slack_res = client.post(
        "/api/v1/slack/interactions",
        data={"payload": json.dumps(slack_payload)},
    )
    assert slack_res.status_code == 200
    slack_data = slack_res.json()
    assert "Dispute" in slack_data["text"]
    assert slack_data["settlement_status"] == "SETTLED_NO_REFUND"
