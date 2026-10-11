import pytest
from cyberdaw.controller import AbletonController, make_osc_message, make_osc_string


def test_make_osc_string():
    raw = make_osc_string("test")
    assert len(raw) % 4 == 0
    assert raw.startswith(b"test\x00")


def test_make_osc_message():
    msg = make_osc_message("/live/song/set/tempo", 132.5)
    assert msg.startswith(b"/live/song/set/tempo\x00")
    assert b",f\x00" in msg


def test_controller_play_and_stop():
    ctrl = AbletonController(mock_mode=True)
    env_play = ctrl.play()
    assert env_play["command"]["name"] == "transport"
    assert env_play["command"]["args"]["action"] == "play"

    env_stop = ctrl.stop(reason="user_stop")
    assert env_stop["command"]["name"] == "stop"
    assert env_stop["command"]["args"]["reason"] == "user_stop"


def test_controller_tempo_and_scenes():
    ctrl = AbletonController(mock_mode=True)
    env_tempo = ctrl.set_tempo(140.0)
    assert env_tempo["command"]["name"] == "tempo"
    assert env_tempo["command"]["args"]["bpm"] == 140.0

    env_scene = ctrl.fire_scene(3)
    assert env_scene["command"]["name"] == "scene"
    assert env_scene["command"]["args"]["scene_index"] == 3


def test_controller_emergency_panic():
    ctrl = AbletonController(mock_mode=True)
    env_panic = ctrl.emergency_panic("TEST_PANIC")
    assert env_panic["command"]["name"] == "stop"
    assert env_panic["command"]["args"]["mute_all"] is True
    assert env_panic["command"]["args"]["reason"] == "TEST_PANIC"
