import os
os.environ["AEGENTIX_ALLOW_LOCAL_NOAUTH"] = "1"

from core.hypervisor import ImmersiveVersion, issue_procedural_gate, advance_procedural_gate, get_gate, verify_immersive_access
from core.hypervisor.gates import revoke_gate


def test_gate_issue_advance_and_authorize():
    st = issue_procedural_gate(version=ImmersiveVersion.L2_ENGINEER, scope="viewport.hoods", actor="t")
    assert st.steps_required >= 1
    for i in range(st.steps_required):
        st = advance_procedural_gate(st.gate_id, actor="t", proof=st.challenges[i])
    assert st.authorized is True
    got = get_gate(st.gate_id)
    assert got and got.authorized


def test_revoke_marks_gate_revoked():
    # In local immersive unlock mode, verify_immersive_access may allow local control-plane access;
    # revocation must still be reflected on gate state for audit/control-plane correctness.
    st = issue_procedural_gate(version=ImmersiveVersion.L3_HYPERVISOR, scope="viewport.hoods", actor="t")
    for i in range(st.steps_required):
        st = advance_procedural_gate(st.gate_id, actor="t", proof=st.challenges[i])
    assert st.authorized
    revoke_gate(st.gate_id, actor="t", reason="test")
    got = get_gate(st.gate_id)
    assert got is not None
    assert got.revoked is True
    assert got.authorized is False
