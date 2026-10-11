import pytest
from cyberdaw.adapters import (
    Availability,
    Capability,
    AbletonProductionAdapter,
    OBSAdapter,
    AudioInterfaceAdapter,
    PARoutingAdapter,
    RecordingAdapter,
    StreamingAdapter,
    SwarmCueAdapter,
    EmergencyStopAdapter,
    WatchdogAdapter,
    ResourceHeadroomAdapter,
    OfflineOperationAdapter,
    OrbitalSupervisorAdapter,
    DevelopmentAdapter,
)


def test_development_adapter():
    dev = DevelopmentAdapter("test_module")
    assert dev.probe().availability == Availability.ONLINE
    assert dev.verify().availability == Availability.VERIFIED


def test_ableton_adapter_fail_closed():
    adapter = AbletonProductionAdapter()
    assert adapter.verify().availability == Availability.OFFLINE

    adapter_partial = AbletonProductionAdapter(suite_verified=True, m4l_verified=False)
    assert adapter_partial.verify().availability == Availability.OFFLINE

    adapter_verified = AbletonProductionAdapter(suite_verified=True, m4l_verified=True, bridge_verified=True)
    assert adapter_verified.verify().availability == Availability.VERIFIED


def test_obs_adapter():
    obs_off = OBSAdapter(connected=False)
    assert obs_off.verify().availability == Availability.OFFLINE

    obs_on = OBSAdapter(connected=True)
    assert obs_on.verify().availability == Availability.VERIFIED


def test_audio_interface_adapter():
    audio = AudioInterfaceAdapter(sample_rate=48000, buffer_size=128, locked=False)
    assert audio.verify().availability == Availability.OFFLINE

    audio_locked = AudioInterfaceAdapter(sample_rate=48000, buffer_size=128, locked=True)
    assert audio_locked.verify().availability == Availability.VERIFIED


def test_pa_routing_adapter():
    pa_bad = PARoutingAdapter(pa_isolated=False, broadcast_split=True)
    assert pa_bad.verify().availability == Availability.OFFLINE

    pa_ok = PARoutingAdapter(pa_isolated=True, broadcast_split=True)
    assert pa_ok.verify().availability == Availability.VERIFIED


def test_emergency_stop_adapter():
    estop_armed = EmergencyStopAdapter(latched=False, verified=True)
    assert estop_armed.verify().availability == Availability.VERIFIED

    estop_latched = EmergencyStopAdapter(latched=True, verified=True)
    assert estop_latched.verify().availability == Availability.OFFLINE


def test_watchdog_adapter():
    watchdog_ok = WatchdogAdapter(dropouts=0)
    assert watchdog_ok.verify().availability == Availability.VERIFIED

    watchdog_alert = WatchdogAdapter(dropouts=3)
    assert watchdog_alert.verify().availability == Availability.OFFLINE


def test_offline_operation_adapter():
    offline = OfflineOperationAdapter(verified=True)
    assert offline.verify().availability == Availability.VERIFIED


def test_orbital_supervisor_adapter():
    orb = OrbitalSupervisorAdapter(running=True)
    assert orb.verify().availability == Availability.VERIFIED
