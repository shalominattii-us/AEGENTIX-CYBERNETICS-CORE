import hashlib
import hmac
import json
import pytest
from cyberdaw.runtime import STATE, SECRET_KEY


def test_runtime_initial_state():
    STATE._init_defaults()
    assert STATE.gate.state.value == "PRODUCTION_BLOCKED"
    assert "ableton_production" in STATE.gate.production_blockers()
    assert "maxforlive_bridge" in STATE.gate.production_blockers()


def test_runtime_hmac_verification():
    payload = {"test": 123, "event": "PING"}
    canonical = json.dumps(payload, sort_keys=True).encode("utf-8")
    sig = hmac.new(SECRET_KEY, canonical, hashlib.sha256).hexdigest()
    payload["signature"] = sig
    assert STATE.verify_hmac(payload) is True

    payload["signature"] = "invalid_signature"
    assert STATE.verify_hmac(payload) is False


def test_runtime_event_clears_checkpoint():
    STATE._init_defaults()
    assert "maxforlive_bridge" in STATE.gate.production_blockers()

    payload = {"event": "MAX_BRIDGE_CONNECTED"}
    STATE._update_gate_from_event("MAX_BRIDGE_CONNECTED", payload)
    assert "maxforlive_bridge" not in STATE.gate.production_blockers()


def test_runtime_emergency_stop_and_reset():
    STATE._init_defaults()
    payload = {"event": "EMERGENCY_STOP", "command": {"args": {"mute_all": True, "reason": "TEST"}}}
    STATE._update_gate_from_event("EMERGENCY_STOP", payload)
    assert STATE.gate.state.value == "EMERGENCY_STOP"

    STATE.gate.reset_emergency()
    assert STATE.gate.state.value != "EMERGENCY_STOP"
