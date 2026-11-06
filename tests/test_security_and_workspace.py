import os
os.environ["AEGENTIX_ALLOW_LOCAL_NOAUTH"] = "1"

import pytest
from fastapi.testclient import TestClient

from core.gateway.server import app
from core.llm_workspace.jobs import _safe_under_root


def test_llm_workspace_api_status_local_noauth():
    c = TestClient(app)
    r = c.get("/api/v1/llm-workspace/status")
    assert r.status_code == 200
    body = r.json()
    assert "ok" in body


def test_workspace_path_escape_blocked():
    # _safe_under_root should reject absolute/relative escapes outside workspace root
    with pytest.raises(Exception):
        _safe_under_root("C:/Windows/System32/drivers/etc/hosts")
