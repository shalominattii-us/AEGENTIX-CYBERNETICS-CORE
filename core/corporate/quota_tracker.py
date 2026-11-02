# Quota Tracker
from __future__ import annotations

from typing import Dict, Any, List
import time


class QuotaTracker:
    def __init__(self):
        self.quotas = []

    def add_quota(self, quota: Dict[str, Any]):
        quota['created_at'] = time.time()
        quota['status'] = quota.get('status', 'pending')
        self.quotas.append(quota)
        return quota

    def get_pending(self):
        return [q for q in self.quotas if q.get('status') == 'pending']

    def fulfill(self, quota_id: str):
        for q in self.quotas:
            if q.get('id') == quota_id:
                q['status'] = 'fulfilled'
                q['fulfilled_at'] = time.time()
        return True
