import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Safe local defaults for tests
os.environ.setdefault("AEGENTIX_ALLOW_LOCAL_NOAUTH", "1")
os.environ.setdefault("AEGENTIX_CHAT_SUGGEST_COMMANDS", "0")
os.environ.setdefault("AEGENTIX_CHAT_TOOL_COMMAND_SUGGESTIONS", "0")
