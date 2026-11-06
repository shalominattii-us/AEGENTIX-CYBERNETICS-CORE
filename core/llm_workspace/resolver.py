from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_MANIFEST = Path(r"C:\AEGENTIX-CYBERNETICS-CORE\config\llm_workspace.json")

def load_workspace_manifest(path: Optional[str]=None) -> Dict[str, Any]:
    p = Path(path or os.environ.get("AEGENTIX_LLM_WORKSPACE_MANIFEST") or DEFAULT_MANIFEST)
    try:
        return json.loads(p.read_text(encoding='utf-8-sig'))
    except Exception:
        return {}

def _pick_existing(candidates):
    for c in candidates or []:
        try:
            if c and Path(c).exists():
                return str(Path(c))
        except Exception:
            pass
    return None

def resolve_llm_workspace(path: Optional[str]=None) -> Dict[str, Any]:
    m = load_workspace_manifest(path)
    ws = (m.get('workspace') or {})
    root = os.environ.get('AEGENTIX_LLM_WORKSPACE_ROOT') or _pick_existing(ws.get('root_candidates') or [])
    py = os.environ.get('AEGENTIX_LLM_WORKSPACE_PYTHON') or _pick_existing(ws.get('python_candidates') or [])
    entry = None
    if root:
        ep = ((ws.get('entrypoints') or {}).get('train')) or 'src/main.py'
        cand = Path(root) / ep
        entry = str(cand) if cand.exists() else None
    return {
        'ok': bool(root),
        'component_id': m.get('component_id'),
        'workspace_root': root,
        'python': py,
        'entrypoint': entry,
        'manifest': str(Path(path or os.environ.get('AEGENTIX_LLM_WORKSPACE_MANIFEST') or DEFAULT_MANIFEST)),
        'integration': m.get('integration') or {},
        'related': m.get('related') or {},
        'errors': [] if root else ['workspace_root_not_found'],
    }
