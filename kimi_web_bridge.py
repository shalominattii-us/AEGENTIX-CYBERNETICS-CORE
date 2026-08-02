"""
AEGENTIX — PROPRIETARY IN-HOUSE KIMI WEB BRIDGE ENGINE
======================================================
Local in-house microservice handling Kimi Orb signal parsing, local telemetry,
and payload formatting for the AEGENTIX ecosystem.
"""

import sys
import time
import json
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 9230

class KimiWebBridgeHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        if self.path in ["/", "/health", "/api/kimi/status"]:
            response = {
                "status": "online",
                "service": "AEGENTIX Proprietary Kimi Web Bridge",
                "mode": "PROPRIETARY_IN_HOUSE",
                "port": PORT,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "endpoints": {
                    "health": "/health",
                    "bridge_status": "/api/kimi/status",
                    "bridge_post": "/api/kimi/bridge"
                }
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

    def do_POST(self):
        if self.path == "/api/kimi/bridge":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8')) if post_data else {}
            except Exception:
                payload = {}

            response = {
                "status": "processed",
                "bridge": "Kimi Orb Web Bridge",
                "received_payload": payload,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "result": "PAYLOAD_FORMATTED_FOR_LOCAL_REVIEW"
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

def run_bridge_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, KimiWebBridgeHandler)
    print("=" * 80)
    print(f"🚀 [AEGENTIX] PROPRIETARY KIMI WEB BRIDGE OPERATIONAL ON PORT {PORT}")
    print("=" * 80)
    print(f"[*] Health Check URL: http://localhost:{PORT}/health")
    print(f"[*] Bridge Endpoint:  http://localhost:{PORT}/api/kimi/bridge")
    print("-" * 80)
    httpd.serve_forever()

if __name__ == "__main__":
    run_bridge_server()
