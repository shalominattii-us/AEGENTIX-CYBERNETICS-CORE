import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_governance():
    path = ROOT / "governance" / "policies" / "default.json"
    return json.loads(path.read_text(encoding="utf-8-sig"))


def create_plan(objective):
    governance = load_governance()

    return {
        "objective": objective,
        "status": "PROPOSED",
        "steps": [
            {
                "id": "discover",
                "action": "DISCOVER",
                "status": "PENDING"
            },
            {
                "id": "plan",
                "action": "PLAN",
                "status": "PENDING"
            },
            {
                "id": "execute",
                "action": "EXECUTE",
                "status": "BLOCKED"
                if not governance["allow_autonomous_execution"]
                else "PENDING"
            },
            {
                "id": "verify",
                "action": "VERIFY",
                "status": "PENDING"
            },
            {
                "id": "report",
                "action": "REPORT",
                "status": "PENDING"
            }
        ],
        "governance": governance
    }


if __name__ == "__main__":
    import sys

    objective = " ".join(sys.argv[1:]).strip()

    if not objective:
        print("Usage: python planner.py <objective>")
        raise SystemExit(1)

    print(json.dumps(create_plan(objective), indent=2))

