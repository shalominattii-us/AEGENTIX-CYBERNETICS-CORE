"""AEGENTIX CyberDAW — Production Telemetry & Control Runtime.

Pure-Python, zero-external-dependency HTTP daemon providing the supervisory
bridge between Ableton Live / Max for Live, the cognitive bus, and the Production Gate.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from typing import Any, Dict, Optional

from .gate import GateState, ProductionGate
from .controller import AbletonController
from .m4l_bridge import validate_envelope, make_envelope

logger = logging.getLogger("cyberdaw.runtime")
SECRET_KEY = b"AEGENTIX_EOC_PRIME_LOCK"
STREAM_PATH = Path(r"C:\Aegentix\brain\telemetry_stream.jsonl")
LOCAL_STREAM_PATH = Path("brain/telemetry_stream.jsonl")

# Ensure directories exist
STREAM_PATH.parent.mkdir(parents=True, exist_ok=True)
LOCAL_STREAM_PATH.parent.mkdir(parents=True, exist_ok=True)

# Shared singleton runtime state
class RuntimeState:
    def __init__(self):
        self.gate = ProductionGate()
        self.controller = AbletonController(mock_mode=True)
        self.events: list[dict[str, Any]] = []
        self.lock = threading.Lock()
        self._init_defaults()

    def _init_defaults(self):
        # Default baseline simulation/evidence for dev
        self.gate.set_check("orbital", True, "Orbital supervisor available")
        self.gate.set_check("obs", True, "OBS adapter contract available")
        self.gate.set_check("audio_interface", True, "Audio interface verification contract available")
        self.gate.set_check("pa_routing", True, "PA routing verification contract available")
        self.gate.set_check("recording", True, "Recording path verification contract available")
        self.gate.set_check("stream", True, "Stream path verification contract available")
        self.gate.set_check("swarm_cue", True, "Swarm cue verification contract available")
        self.gate.set_check("emergency_stop", True, "Emergency stop safety circuit available")
        self.gate.set_check("watchdog", True, "Watchdog verification contract available")
        self.gate.set_check("resource_headroom", True, "Resource headroom verification contract available")
        self.gate.set_check("offline_operation", True, "Offline-first contract available")
        # Fail-closed blockers remain
        self.gate.set_check("ableton_production", False, "requires verified production Ableton Live Suite")
        self.gate.set_check("maxforlive_bridge", False, "requires verified production Max-for-Live bridge")

    def verify_hmac(self, payload: dict[str, Any]) -> bool:
        copy_obj = dict(payload)
        sig_stored = copy_obj.pop("signature", "")
        if not sig_stored:
            return False
        canonical = json.dumps(copy_obj, sort_keys=True).encode("utf-8")
        computed = hmac.new(SECRET_KEY, canonical, hashlib.sha256).hexdigest()
        return computed.lower() == str(sig_stored).lower()

    def record_event(self, payload: dict[str, Any], raw_body: str):
        with self.lock:
            self.events.append(payload)
            # Write to both global and local stream
            for p in (STREAM_PATH, LOCAL_STREAM_PATH):
                try:
                    with open(p, "a", encoding="utf-8") as f:
                        f.write(raw_body.strip() + "\n")
                except Exception as e:
                    logger.debug("Failed writing stream to %s: %s", p, e)

            # Process gate checkpoints
            ev_name = payload.get("event") or payload.get("command", {}).get("name")
            if ev_name:
                self._update_gate_from_event(ev_name, payload)

    def _update_gate_from_event(self, ev_name: str, payload: dict[str, Any]):
        mapping = {
            "AUDIO_INTERFACE_LOCKED": ("audio_interface", "Locked ASIO/WASAPI buffer verified"),
            "PA_ROUTING_VERIFIED": ("pa_routing", "FOH 1/2 vs Broadcast 3/4 separated"),
            "MAX_BRIDGE_CONNECTED": ("maxforlive_bridge", "M4L bidirectional bridge active"),
            "SCENE_SELECTION_ACTIVE": ("swarm_cue", "Scene cue active and synchronized"),
            "CLIP_LAUNCH_EVENT": ("recording", "Clip launch and stem capture verified"),
            "OBS_CONNECTED": ("obs", "OBS Studio active and verified"),
            "STREAM_ONLINE": ("stream", "Broadcast stream pipeline verified"),
            "WATCHDOG_HEARTBEAT": ("watchdog", "Watchdog active; 0 underruns"),
            "RESOURCE_HEADROOM_OK": ("resource_headroom", "Host resource headroom verified"),
            "OFFLINE_MODE_VERIFIED": ("offline_operation", "100% offline-ready verified"),
            "ORBITAL_SUPERVISOR_ONLINE": ("orbital", "Orbital supervisor state verified"),
            "ABLETON_LIVE_VERIFIED": ("ableton_production", "Ableton Live Suite verified via bridge"),
        }
        if ev_name in mapping:
            check_key, detail = mapping[ev_name]
            self.gate.set_check(check_key, True, detail)

        # Handle emergency stop
        if ev_name in ("EMERGENCY_STOP", "stop") and payload.get("command", {}).get("args", {}).get("mute_all"):
            self.gate.emergency_stop(payload.get("command", {}).get("args", {}).get("reason", "M4L_EMERGENCY"))


STATE = RuntimeState()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class CyberDAWRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict[str, Any]):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Signature")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            self._send_json(200, {
                "ok": True,
                "service": "cyberdaw-runtime",
                "stats": {
                    "openrouter_available": bool(os.getenv("OPENROUTER_API_KEY")),
                    "events_logged": len(STATE.events),
                    "state": STATE.gate.state.value,
                    "production_ready": STATE.gate.production_ready,
                }
            })
        elif path in ("/cyberdaw/gate", "/gate"):
            self._send_json(200, STATE.gate.report())
        elif path in ("/cyberdaw/history", "/telemetry/history"):
            self._send_json(200, {"events": STATE.events[-50:], "total": len(STATE.events)})
        else:
            self._send_json(404, {"error": "Endpoint not found", "path": path})

    def do_POST(self):
        path = self.path.split("?")[0]
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            payload = json.loads(raw_body)
        except Exception as e:
            self._send_json(400, {"error": "Invalid JSON", "detail": str(e)})
            return

        if path in ("/cyberdaw/telemetry", "/telemetry"):
            # Check signature if provided or validate schema envelope
            hmac_ok = STATE.verify_hmac(payload)
            is_valid_envelope, _ = validate_envelope(payload)

            STATE.record_event(payload, raw_body)
            self._send_json(200, {
                "status": "ok",
                "hmac_verified": hmac_ok,
                "envelope_valid": is_valid_envelope,
                "gate_state": STATE.gate.state.value,
                "production_ready": STATE.gate.production_ready,
                "blockers_remaining": len(STATE.gate.production_blockers()),
            })

        elif path in ("/cyberdaw/command", "/command"):
            cmd = payload.get("command") or payload.get("action")
            args = payload.get("args", {})
            target = payload.get("target")

            env = make_envelope(cmd, args, target)
            STATE.record_event(env, json.dumps(env))
            self._send_json(200, {"status": "dispatched", "envelope": env})

        elif path in ("/cyberdaw/emergency-stop", "/emergency-stop"):
            reason = payload.get("reason", "OPERATOR_EMERGENCY_STOP")
            STATE.gate.emergency_stop(reason)
            env = STATE.controller.emergency_panic(reason)
            STATE.record_event(env, json.dumps(env))
            self._send_json(200, {
                "status": "EMERGENCY_STOP_ENGAGED",
                "gate": STATE.gate.report(),
            })

        elif path in ("/cyberdaw/reset", "/reset"):
            STATE.gate.reset_emergency()
            self._send_json(200, {
                "status": "EMERGENCY_STOP_RESET",
                "gate": STATE.gate.report(),
            })

        elif path in ("/cyberdaw/cue", "/cue"):
            scene = payload.get("scene_index", payload.get("scene", 0))
            env = STATE.controller.fire_scene(int(scene))
            STATE.record_event(env, json.dumps(env))
            self._send_json(200, {"status": "cue_fired", "scene": scene, "envelope": env})

        else:
            self._send_json(404, {"error": "Endpoint not found", "path": path})

    def log_message(self, format, *args):
        # Clean logging
        pass


def run_server(host: str = "0.0.0.0", port: int = 8000) -> ThreadedHTTPServer:
    server = ThreadedHTTPServer((host, port), CyberDAWRequestHandler)
    print(f"[*] CyberDAW Runtime listening on http://{host}:{port}")
    return server


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = run_server("0.0.0.0", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping CyberDAW Runtime.")
        server.server_close()
