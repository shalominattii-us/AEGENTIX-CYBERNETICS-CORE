from __future__ import annotations
import json, os, urllib.request
from typing import Any, Dict, List, Optional

def chat(*, base_url: Optional[str]=None, model: str, messages: List[Dict[str, Any]], timeout: int=60, stream: bool=False) -> Dict[str, Any]:
    base = (base_url or os.environ.get('OLLAMA_BASE_URL') or 'http://127.0.0.1:11434').rstrip('/')
    payload = json.dumps({'model': model, 'messages': messages, 'stream': bool(stream)}).encode('utf-8')
    req = urllib.request.Request(base + '/api/chat', data=payload, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8', 'replace'))
