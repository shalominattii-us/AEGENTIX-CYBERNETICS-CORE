from __future__ import annotations
from fastapi import APIRouter, Request, HTTPException
try:
    from core.gateway.security import authorize_request, audit_event
except Exception:
    def authorize_request(*a, **k): return (False,'unknown','security_unavailable')
    def audit_event(*a, **k): return None
try:
    from core.models.registry import get_model_registry
except Exception:
    get_model_registry = None
try:
    from core.gateway.config import MODEL_PROFILES
except Exception:
    MODEL_PROFILES = {}

router = APIRouter(prefix='/api/v1/models', tags=['models'])

def _auth(request: Request, scope: str):
    ok, actor, reason = authorize_request(request, scope=scope)
    if not ok:
        audit_event('models.auth.denied', actor=actor, outcome='denied', detail={'scope':scope,'reason':reason})
        raise HTTPException(status_code=401, detail='Unauthorized')
    return actor

@router.get('/registry')
async def registry(request: Request):
    actor=_auth(request,'models.read')
    reg = get_model_registry() if get_model_registry else None
    data = {'models': [m.__dict__ for m in (reg.list() if reg else [])], 'providers': (reg.providers() if reg else {}), 'routing': (reg.routing() if reg else {})}
    audit_event('models.registry', actor=actor, outcome='ok', detail={'count':len(data['models'])})
    return data

@router.get('/profiles')
async def profiles(request: Request):
    actor=_auth(request,'models.read')
    out = {}
    for k,v in (MODEL_PROFILES or {}).items():
        try:
            out[k] = {'name':v.name,'endpoint':v.endpoint,'tier':v.tier,'max_latency_ms':v.max_latency_ms,'security_clearance_min':v.security_clearance_min,'supports_streaming':v.supports_streaming,'context_window':v.context_window,'cost_per_million_tokens':v.cost_per_million_tokens}
        except Exception:
            out[k] = {'name':k}
    audit_event('models.profiles', actor=actor, outcome='ok', detail={'count':len(out)})
    return {'profiles': out}
