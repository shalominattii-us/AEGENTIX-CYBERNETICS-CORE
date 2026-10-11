import json
from cyberdaw.m4l_bridge import (
    COMMANDS,
    MaxForLiveBridgeAdapter,
    make_envelope,
    validate_envelope,
)


def test_valid_envelope_passes():
    envelope = make_envelope("transport", {"action": "play"}, None)
    ok, errors = validate_envelope(envelope)
    assert ok, errors


def test_envelope_requires_all_schema_fields():
    envelope = {
        "version": "1.0",
        "source": "aegentix",
        "command": {"name": "transport", "args": {}},
    }
    ok, errors = validate_envelope(envelope)
    assert not ok
    assert any("id" in e for e in errors)
    assert any("timestamp" in e for e in errors)


def test_wrong_source_fails():
    envelope = make_envelope("stop", {"reason": "test"})
    envelope["source"] = "aegentix-m4l"
    ok, errors = validate_envelope(envelope)
    assert not ok
    assert any("source" in e for e in errors)


def test_unsupported_command_fails():
    envelope = make_envelope("transport", {})
    envelope["command"]["name"] = "unsupported"
    ok, errors = validate_envelope(envelope)
    assert not ok
    assert any("not supported" in e for e in errors)


def test_make_envelope_rejects_unknown_command():
    try:
        make_envelope("unknown", {})
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_all_commands_are_supported_by_schema():
    for command in COMMANDS:
        envelope = make_envelope(command, {})
        ok, errors = validate_envelope(envelope)
        assert ok, (command, errors)


def test_bridge_adapter_defaults_to_blocked():
    adapter = MaxForLiveBridgeAdapter()
    assert adapter.verify().availability.value != "VERIFIED"


def test_bridge_adapter_requires_evidence():
    adapter = MaxForLiveBridgeAdapter(bridge_verified=True, evidence=None)
    assert adapter.verify().availability.value != "VERIFIED"


def test_bridge_adapter_accepts_verified_evidence():
    adapter = MaxForLiveBridgeAdapter(bridge_verified=True, evidence="sn-123")
    result = adapter.verify()
    assert result.availability.value == "VERIFIED"