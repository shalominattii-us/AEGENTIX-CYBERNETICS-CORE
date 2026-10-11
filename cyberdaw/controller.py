"""AEGENTIX CyberDAW — Ableton Live OSC & Control Layer.

Enables direct programmatic dispatch of transport, scenes, clips, tempo,
and device parameters via standard Open Sound Control (OSC) over UDP
and Max-for-Live JSON envelopes.
"""

from __future__ import annotations

import json
import socket
import struct
import time
from dataclasses import dataclass
from typing import Any, Optional, Union

from .m4l_bridge import make_envelope, validate_envelope


def make_osc_string(s: str) -> bytes:
    """Pad string to 4-byte boundary with null bytes per OSC 1.0 spec."""
    encoded = s.encode("utf-8") + b"\x00"
    remainder = len(encoded) % 4
    if remainder != 0:
        encoded += b"\x00" * (4 - remainder)
    return encoded


def make_osc_message(address: str, *args: Union[int, float, str]) -> bytes:
    """Encodes a standard OSC 1.0 packet."""
    addr_bytes = make_osc_string(address)
    type_tags = ","
    payload = b""

    for arg in args:
        if isinstance(arg, int):
            type_tags += "i"
            payload += struct.pack(">i", arg)
        elif isinstance(arg, float):
            type_tags += "f"
            payload += struct.pack(">f", arg)
        elif isinstance(arg, str):
            type_tags += "s"
            payload += make_osc_string(arg)
        else:
            raise TypeError(f"Unsupported OSC type: {type(arg)}")

    tags_bytes = make_osc_string(type_tags)
    return addr_bytes + tags_bytes + payload


@dataclass
class AbletonController:
    """High-level controller for Ableton Live via OSC and M4L envelope dispatch."""
    host: str = "127.0.0.1"
    osc_port: int = 11000  # Default LiveOSC port
    mock_mode: bool = False

    def __post_init__(self):
        self._sent_packets: list[bytes] = []
        self._sent_envelopes: list[dict[str, Any]] = []

    def send_osc(self, address: str, *args: Union[int, float, str]) -> bytes:
        packet = make_osc_message(address, *args)
        self._sent_packets.append(packet)
        if not self.mock_mode:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(packet, (self.host, self.osc_port))
                sock.close()
            except Exception:
                pass
        return packet

    # ── High-Level Transport Controls ──────────────────────────────────────────

    def play(self) -> dict[str, Any]:
        """Start Ableton playback."""
        self.send_osc("/live/song/start_playing")
        env = make_envelope("transport", {"action": "play"})
        self._sent_envelopes.append(env)
        return env

    def stop(self, reason: str = "operator_stop") -> dict[str, Any]:
        """Stop Ableton playback."""
        self.send_osc("/live/song/stop_playing")
        env = make_envelope("stop", {"reason": reason})
        self._sent_envelopes.append(env)
        return env

    def record(self, action: str = "start", track: Optional[str] = None) -> dict[str, Any]:
        """Trigger session or arrangement recording."""
        self.send_osc("/live/song/record")
        env = make_envelope("record", {"action": action}, target=track)
        self._sent_envelopes.append(env)
        return env

    def set_tempo(self, bpm: float) -> dict[str, Any]:
        """Set master tempo in BPM."""
        self.send_osc("/live/song/set/tempo", float(bpm))
        env = make_envelope("tempo", {"bpm": float(bpm)})
        self._sent_envelopes.append(env)
        return env

    # ── Scene & Cue Management ────────────────────────────────────────────────

    def fire_scene(self, scene_index: int) -> dict[str, Any]:
        """Fire scene by 0-based index."""
        self.send_osc("/live/scene/fire", int(scene_index))
        env = make_envelope("scene", {"action": "fire", "scene_index": scene_index}, target=f"scene_{scene_index}")
        self._sent_envelopes.append(env)
        return env

    def fire_clip(self, track_index: int, clip_index: int) -> dict[str, Any]:
        """Fire a specific clip slot."""
        self.send_osc("/live/clip/fire", int(track_index), int(clip_index))
        env = make_envelope("clip", {"action": "fire", "track": track_index, "clip": clip_index})
        self._sent_envelopes.append(env)
        return env

    def set_parameter(self, track_index: int, device_index: int, parameter_index: int, value: float) -> dict[str, Any]:
        """Set a device parameter."""
        self.send_osc("/live/device/set/parameter_value", int(track_index), int(device_index), int(parameter_index), float(value))
        env = make_envelope("parameter", {
            "track": track_index,
            "device": device_index,
            "parameter": parameter_index,
            "value": float(value),
        })
        self._sent_envelopes.append(env)
        return env

    # ── Emergency Panic Button ────────────────────────────────────────────────

    def emergency_panic(self, reason: str = "EMERGENCY_PANIC_ENGAGED") -> dict[str, Any]:
        """Mutes all audio and immediately halts playback."""
        self.send_osc("/live/song/stop_playing")
        for t in range(8):
            self.send_osc("/live/track/set/volume", t, 0.0)
        env = make_envelope("stop", {"reason": reason, "mute_all": True})
        self._sent_envelopes.append(env)
        return env

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._sent_envelopes)
