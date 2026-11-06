import os
os.environ["AEGENTIX_ALLOW_LOCAL_NOAUTH"] = "1"

from fastapi.testclient import TestClient
from core.gateway.server import app


def test_infer_sensitive_does_not_select_cloud():
    with TestClient(app) as c:
        r = c.post("/api/v1/infer", json={
            "prompt": "sensitive",
            "security_clearance": 4,
            "prefer_cloud": True,
            "task_type": "planning",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["latency_tier"].startswith("edge")
        assert body["model_selected"] not in ("gemini", "claude")
