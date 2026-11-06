"""Aether memory: append-only JSONL store + optional HTTP vector-memory bridge.

Gateway/stratus/jarvis compatible API:
- store(content, metadata=None, agent_id=None) -> id
- query(query, top_k=5)
- recent(n=10)
- count()
- checkpoint()
"""
from __future__ import annotations

import json
import os
import time
import uuid
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


class AetherMemory:
    def __init__(self, persistence_path: str = "data/aether_memory.jsonl", vector_memory_url: Optional[str] = None):
        self.persistence_path = Path(persistence_path)
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_memory_url = (vector_memory_url or os.environ.get("AEGENTIX_VECTOR_MEMORY_URL") or "").rstrip("/") or None
        self._items: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self.persistence_path.exists():
            return
        try:
            with self.persistence_path.open("r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self._items.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            pass

    def _append(self, item: Dict[str, Any]) -> None:
        try:
            with self.persistence_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass

    def store(self, content: Any, metadata: Optional[Dict[str, Any]] = None, agent_id: Optional[str] = None) -> str:
        item = {
            "id": str(uuid.uuid4()),
            "ts": time.time(),
            "agent_id": agent_id,
            "content": content,
            "metadata": metadata or {},
        }
        self._items.append(item)
        self._append(item)
        # Best-effort forward to vector-memory service if it accepts text (non-breaking).
        if self.vector_memory_url:
            try:
                payload = json.dumps({"text": json.dumps(content, ensure_ascii=False, default=str), "embedding": [], "metadata": {"agent_id": agent_id, **(metadata or {})}}).encode("utf-8")
                req = urllib.request.Request(self.vector_memory_url + "/store", data=payload, headers={"Content-Type": "application/json"}, method="POST")
                urllib.request.urlopen(req, timeout=1.5).read()
            except Exception:
                pass
        return item["id"]

    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q = (query or "").lower().strip()
        if not q:
            return self.recent(top_k)
        terms = [t for t in q.split() if t]
        try:
            from core.native_fast import score_terms as _native_score
        except Exception:
            _native_score = None
        scored = []
        for item in reversed(self._items):
            # Fast path: stringify once; native scorer avoids repeated Python substring scans for term sets.
            text = str(item.get("content", "")).lower()
            if not isinstance(item.get("content", ""), (str, bytes)):
                try:
                    text = json.dumps(item.get("content", ""), ensure_ascii=False, default=str).lower()
                except Exception:
                    pass
            score = None
            if _native_score is not None:
                try:
                    score = _native_score(text, terms, q)
                except Exception:
                    score = None
            if score is None:
                score = sum(1 for term in terms if term in text)
                if q in text:
                    score += 2
            score = int(score or 0)
            if score:
                scored.append((score, float(item.get("ts", 0) or 0), item))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [i for _, _, i in scored[: max(1, int(top_k))]]

    def recent(self, n: int = 10) -> List[Dict[str, Any]]:
        return list(reversed(self._items[-max(0, int(n)):]))

    def count(self) -> int:
        return len(self._items)

    def checkpoint(self) -> Dict[str, Any]:
        # Compact rewrite (dedupe by id, keep last) for durability.
        by_id: Dict[str, Dict[str, Any]] = {}
        for item in self._items:
            by_id[str(item.get("id"))] = item
        self._items = list(by_id.values())
        try:
            tmp = self.persistence_path.with_suffix(self.persistence_path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as fh:
                for item in self._items:
                    fh.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
            tmp.replace(self.persistence_path)
        except Exception:
            pass
        return {"ok": True, "count": self.count(), "path": str(self.persistence_path)}

    def stats(self) -> Dict[str, Any]:
        return {"count": self.count(), "path": str(self.persistence_path), "vector_memory_url": self.vector_memory_url}
