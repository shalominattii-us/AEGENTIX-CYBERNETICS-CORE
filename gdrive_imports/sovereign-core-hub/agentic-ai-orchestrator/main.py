import os, json, yaml
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get('PORT', 8844))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({'status':'healthy','service':'agentic-ai'}).encode())
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
        self.wfile.write(json.dumps({'status':'received'}).encode())
    def log_message(self, format, *args): pass

if __name__ == '__main__':
    print(f'[Agentic AI] Orchestrator on port {PORT}')
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()