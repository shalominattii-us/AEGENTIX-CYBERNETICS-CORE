"""Entry point for `python -m cyberdaw`.

Without this module Python refuses to execute the package and the
CyberDAW Integrity workflow's `python -m cyberdaw verify --json` step fails.
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
