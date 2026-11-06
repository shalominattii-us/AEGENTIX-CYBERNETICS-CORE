# AEGENTIX Model Housing

Source of truth: `config/models.registry.json` (providers, housed models, routing hints).

- `core/models/registry.py` loads registry into `ModelSpec`s and exports gateway-compatible profile dicts.
- `core/gateway/config.py` merges registry models with built-in defaults (backward compatible).
- Providers/adapters live under `core/models/providers/` (Ollama/OpenAI-compat/native/SHM stubs).

Security/SOC2 posture:
- Sensitive clearance/offline routes stay local/sovereign per router policy.
- Cloud providers require explicit API keys/env; never hardcode secrets.
- Inference endpoints are gateway/MCP auth-guarded (local ROG noauth is explicit loopback-only).
