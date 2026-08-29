import pytest

from cyberdaw.gate import GateState, ProductionGate
from cyberdaw.cli import build_gate


def test_missing_evidence_fails_closed():
    gate = ProductionGate()
    assert gate.state is GateState.PRODUCTION_BLOCKED
    assert not gate.production_ready
    assert set(gate.production_blockers())


def test_trial_never_unlocks_production():
    gate = build_gate()
    assert gate.state is GateState.PRODUCTION_BLOCKED
    assert "ableton_production" in gate.production_blockers()
    assert "maxforlive_bridge" in gate.production_blockers()


def test_complete_evidence_unlocks_live_pa():
    gate = ProductionGate()
    for name in gate.checks():
        gate.set_check(name, True, "test evidence")
    assert gate.state is GateState.LIVE_PA_READY


def test_emergency_stop_overrides_ready():
    gate = ProductionGate()
    for name in gate.checks():
        gate.set_check(name, True, "test evidence")
    gate.emergency_stop("test")
    assert gate.state is GateState.EMERGENCY_STOP
    assert not gate.production_ready


def test_reset_does_not_fabricate_missing_evidence():
    gate = ProductionGate()
    for name in gate.checks():
        gate.set_check(name, True)
    gate.emergency_stop()
    gate.reset_emergency()
    assert gate.state is GateState.LIVE_PA_READY
    gate.set_check("watchdog", False)
    assert gate.state is GateState.PRODUCTION_BLOCKED
