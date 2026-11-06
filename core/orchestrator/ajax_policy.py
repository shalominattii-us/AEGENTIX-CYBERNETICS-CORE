"""AjaxPolicyEngine: config-driven, safe-by-default action policy."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional


class AjaxPolicyEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.external_blocked = str(os.environ.get("AEGENTIX_BLOCK_EXTERNAL_ACTIONS", "1")) not in ("0", "false", "False")
        self.financial_blocked = str(os.environ.get("AEGENTIX_BLOCK_FINANCIAL_ACTIONS", "1")) not in ("0", "false", "False")
        self.destructive_blocked = str(os.environ.get("AEGENTIX_BLOCK_DESTRUCTIVE_ACTIONS", "1")) not in ("0", "false", "False")

    def evaluate(self, action: str = "", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        a = (action or "").lower()
        reasons = []
        allowed = True
        if self.financial_blocked and any(k in a for k in ("pay", "transfer", "withdraw", "trade", "order", "purchase", "invoice")):
            allowed = False; reasons.append("financial_actions_blocked")
        if self.external_blocked and any(k in a for k in ("submit", "publish", "send_email", "post_public", "filing", "deploy_prod")) and not ctx.get("explicitly_authorized"):
            allowed = False; reasons.append("external_actions_blocked_without_authorization")
        if self.destructive_blocked and any(k in a for k in ("delete", "drop", "destroy", "wipe", "rm -rf", "format")) and not ctx.get("explicitly_authorized"):
            allowed = False; reasons.append("destructive_actions_blocked_without_authorization")
        return {"allowed": allowed, "action": action, "reasons": reasons, "policy": "ajax-sovereign-default", "context_scoped": bool(ctx)}

    def get_status(self) -> Dict[str, Any]:
        return {"status": "operational", "external_blocked": self.external_blocked, "financial_blocked": self.financial_blocked, "destructive_blocked": self.destructive_blocked}
