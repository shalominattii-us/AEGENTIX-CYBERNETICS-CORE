from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Aegentix")
BRAIN = ROOT / "brain"
BUS_PATH = BRAIN / "cognitive_bus.py"


class CognitiveBridgeError(RuntimeError):
    pass


def load_existing_bus():
    if not BUS_PATH.is_file():
        raise CognitiveBridgeError(
            f"Missing existing cognitive bus: {BUS_PATH}"
        )

    spec = importlib.util.spec_from_file_location(
        "aegentix_existing_cognitive_bus",
        str(BUS_PATH),
    )

    if spec is None or spec.loader is None:
        raise CognitiveBridgeError(
            "Unable to construct import specification."
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def load_state() -> Any:
    bus = load_existing_bus()

    fn = getattr(bus, "load_state", None)

    if not callable(fn):
        raise CognitiveBridgeError(
            "Existing cognitive_bus.py does not provide callable load_state()."
        )

    return fn()


def _invoke(fn, values: dict[str, Any]):
    signature = inspect.signature(fn)

    args = []
    kwargs = {}

    parameters = list(signature.parameters.values())

    for parameter in parameters:

        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        if parameter.name in values:
            kwargs[parameter.name] = values[parameter.name]

        elif parameter.default is inspect.Parameter.empty:
            raise CognitiveBridgeError(
                f"Cannot safely call {fn.__name__}(): "
                f"required parameter '{parameter.name}' is unknown."
            )

    return fn(*args, **kwargs)


def record_intent(
    source: str,
    intent: str,
    context: dict[str, Any] | None = None,
) -> Any:

    context = context or {}

    bus = load_existing_bus()

    payload = {
        "intent": intent,
        "context": context,
    }

    fn = getattr(bus, "record_intent", None)

    if callable(fn):

        return _invoke(
            fn,
            {
                "source": source,
                "intent": intent,
                "context": context,
                "payload": payload,
                "event_type": "COGNITIVE_INTENT",
            },
        )

    fn = getattr(bus, "append_event", None)

    if callable(fn):

        return _invoke(
            fn,
            {
                "source": source,
                "intent": intent,
                "context": context,
                "payload": payload,
                "event_type": "COGNITIVE_INTENT",
            },
        )

    raise CognitiveBridgeError(
        "No existing event-writing function was found."
    )


def health() -> dict[str, Any]:

    bus = load_existing_bus()

    return {
        "bridge": "PASS",
        "bus": str(BUS_PATH),
        "load_state": callable(
            getattr(bus, "load_state", None)
        ),
        "record_intent": callable(
            getattr(bus, "record_intent", None)
        ),
        "append_event": callable(
            getattr(bus, "append_event", None)
        ),
    }


if __name__ == "__main__":

    command = sys.argv[1] if len(sys.argv) > 1 else "health"

    if command == "health":

        print(
            json.dumps(
                health(),
                indent=2,
                sort_keys=True,
                default=str,
            )
        )

    elif command == "state":

        print(
            json.dumps(
                load_state(),
                indent=2,
                sort_keys=True,
                default=str,
            )
        )

    elif command == "intent":

        if len(sys.argv) < 4:
            raise SystemExit(
                "intent requires SOURCE and INTENT"
            )

        source = sys.argv[2]
        intent = sys.argv[3]

        context = {}

        if len(sys.argv) >= 5:
            context = json.loads(sys.argv[4])

        result = record_intent(
            source,
            intent,
            context,
        )

        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
                default=str,
            )
        )

    else:
        raise SystemExit(
            f"Unknown command: {command}"
        )