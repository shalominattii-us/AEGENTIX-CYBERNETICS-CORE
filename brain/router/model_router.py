import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "brain" / "router" / "model_registry.json"


def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8-sig"))


def route(task_type):
    registry = load_registry()

    models = registry.get("models", [])

    if not models:
        return {
            "status": "NO_MODEL_REGISTERED",
            "task_type": task_type,
            "models": []
        }

    return {
        "status": "ROUTED",
        "task_type": task_type,
        "models": models
    }


if __name__ == "__main__":
    import sys

    task = sys.argv[1] if len(sys.argv) > 1 else "general"

    print(json.dumps(route(task), indent=2))

