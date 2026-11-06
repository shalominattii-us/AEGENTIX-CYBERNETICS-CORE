from core.gateway.router import ModelRouter, ModelRequest


def test_sensitive_request_never_routes_cloud():
    r = ModelRouter()
    d = r.route(ModelRequest(prompt="secret", prefer_cloud=True, security_clearance=4, task_type="routine"))
    assert d.profile.tier.startswith("edge")
    assert d.selected_model != "gemini"
    assert d.selected_model != "claude"


def test_offline_routes_local():
    r = ModelRouter()
    d = r.route(ModelRequest(prompt="x", offline_mode=True, task_type="planning"))
    assert d.profile.tier.startswith("edge")


def test_fast_task_routes_local_fast_model_when_non_sensitive():
    r = ModelRouter()
    d = r.route(ModelRequest(prompt="hello", task_type="routine", security_clearance=1))
    assert d.profile.tier.startswith("edge")
    assert d.selected_model in ("sparkx", "spark-x2.6-1.7b", "titan-c-native", "titan-local")
