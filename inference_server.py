import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import torch
from tokenizer import CybercoreByteTokenizer

MODEL_INSTANCE = None
TOKENIZER_INSTANCE = None

class InferenceServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    @torch.inference_mode()
    def do_POST(self):
        if self.path == "/v1/execute":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode('utf-8'))
            
            prompt = payload.get("prompt", "")
            max_tokens = payload.get("max_tokens", 32)
            
            input_ids = TOKENIZER_INSTANCE.encode(prompt, device="cuda").unsqueeze(0)
            
            for _ in range(max_tokens):
                with torch.amp.autocast(device_type='cuda', dtype=torch.bfloat16):
                    logits = MODEL_INSTANCE(input_ids)
                next_token_logits = logits[:, -1, :]
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
                input_ids = torch.cat([input_ids, next_token], dim=-1)
                if next_token.item() == 258:
                    break
            
            output_text = TOKENIZER_INSTANCE.decode(input_ids)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            response_payload = {"response": output_text}
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))

def launch_api(model, host="127.0.0.1", port=8080):
    global MODEL_INSTANCE, TOKENIZER_INSTANCE
    MODEL_INSTANCE = model
    TOKENIZER_INSTANCE = CybercoreByteTokenizer()
    server = HTTPServer((host, port), InferenceServerHandler)
    print(f"──> [INFRASTRUCTURE ONLINE]: Local API running at http://{host}:{port}/v1/execute")
    server.serve_forever()
