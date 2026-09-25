import pytest
from fastapi.testclient import TestClient
from src.api.main import app, runtime

@pytest.fixture(autouse=True)
def reset_runtime_state(tmp_path):
    """Fixture to provide isolated ledger and WAL replay logs per test."""
    runtime.ledger.block_height = 0
    runtime.ledger.last_state_root = "0x" + "0" * 64
    runtime.replay.log_path = str(tmp_path / "test_replay_log.jsonl")
    runtime.replay.node_role = "STANDBY"
    runtime.replay.replayed_height = 0
    runtime.replay.last_replayed_root = "0x" + "0" * 64
    runtime.sovereign._active_challenges.clear()

client = TestClient(app)

def test_hardware_token_verification():
    # 1. Request Ephemeral Challenge Nonce
    attest_resp = client.post("/api/v1/sov/attest", json={"wallet": "0xSovereignOwner"})
    assert attest_resp.status_code == 200
    nonce = attest_resp.json()["nonce"]
    assert nonce is not None

    # 2. Submit Intent with Valid Hardware Proof
    intent_payload = {
        "route_key": "us_treasury_fed",
        "sender": "0xSovereignOwner",
        "receiver": "0xAlliedSettlement",
        "amount": 100000.0,
        "auth_nonce": nonce,
        "auth_signature": "0xsig_valid_hardware_assertion"
    }
    settle_resp = client.post("/api/v1/intent", json=intent_payload)
    assert settle_resp.status_code == 202
    assert settle_resp.json()["status"] == "SETTLED"
    assert settle_resp.json()["block_height"] == 1

    # 3. Prevent Replay Attacks: Nonce Consumption Assertion (Should Fail)
    replay_attempt = client.post("/api/v1/intent", json=intent_payload)
    assert replay_attempt.status_code == 401
    assert "Invalid Hardware Token Signature" in replay_attempt.json()["detail"]

    # 4. Invalid Nonce Assertion (Should Fail)
    invalid_payload = intent_payload.copy()
    invalid_payload["auth_nonce"] = "0xinvalid_nonce_string"
    invalid_resp = client.post("/api/v1/intent", json=invalid_payload)
    assert invalid_resp.status_code == 401


def test_failover_state_replay_and_promotion():
    # 1. Settle 2 Blocks to Populate WAL Log
    for amt in [250000.0, 750000.0]:
        n_resp = client.post("/api/v1/sov/attest", json={"wallet": "0xSovereignOwner"})
        nonce = n_resp.json()["nonce"]
        client.post("/api/v1/intent", json={
            "route_key": "us_treasury_fed",
            "sender": "0xSovereignOwner",
            "receiver": "0xAlliedSettlement",
            "amount": amt,
            "auth_nonce": nonce,
            "auth_signature": "0xsig_proof"
        })

    # Assert 2 blocks written to ledger
    assert runtime.ledger.block_height == 2

    # 2. Trigger Deterministic State Replay
    replay_resp = client.post("/api/v1/failover/replay")
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()
    assert replay_data["status"] == "STATE_PARITY_VERIFIED"
    assert replay_data["replayed_blocks"] == 2
    assert replay_data["final_height"] == 2
    assert replay_data["state_root"] == runtime.ledger.last_state_root

    # 3. Promote Node to Active
    promote_resp = client.post("/api/v1/failover/promote")
    assert promote_resp.status_code == 200
    assert promote_resp.json()["node_role"] == "ACTIVE"

    # 4. Confirm Health Endpoint Reflects ACTIVE Promotion
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["node_role"] == "ACTIVE"
    assert health_resp.json()["block_height"] == 2
