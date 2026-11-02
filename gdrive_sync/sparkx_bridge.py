#!/usr/bin/env python3
"""
AEGENTIX SparkX Google Drive Sync Bridge Daemon
Watches AEGENTIX_CORE folder and pipes context to local SparkX endpoint via Ollama.
"""

import json
import time
import os
import urllib.request
from pathlib import Path
from datetime import datetime

GDRIVE_ROOT = r"C:\Aegentix\gdrive_sync\AEGENTIX_CORE"
OLLAMA_ENDPOINT = "http://127.0.0.1:11434/api/chat"
SPARKX_MODEL = "SparkLLM/Spark-X2.6-1.7B:latest"
POLL_INTERVAL = 5  # seconds


def read_file(path):
    full = os.path.join(GDRIVE_ROOT, path)
    if not os.path.exists(full):
        return None
    with open(full, encoding="utf-8") as f:
        return f.read()


def read_json(path):
    content = read_file(path)
    if content is None:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def write_json(path, data):
    full = os.path.join(GDRIVE_ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def append_log(path, entry):
    full = os.path.join(GDRIVE_ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {entry}\n")


def build_context():
    system_prompt = read_file("config/system_prompt.md") or ""
    tool_schemas = read_file("config/tool_schemas.json") or "{}"
    current_state = read_json("memory/current_state.json") or {}
    inbound = read_json("sync/inbound_queue.json") or {"queue": []}

    context = {
        "system_prompt": system_prompt,
        "tool_schemas": tool_schemas,
        "current_state": current_state,
        "inbound_queue": inbound.get("queue", []),
    }
    return context


def process_inbound_item(item):
    context = build_context()
    prompt = f"""{context['system_prompt']}

## Current State
{json.dumps(context['current_state'], indent=2)}

## Tool Schemas
{context['tool_schemas']}

## Task
{json.dumps(item, indent=2)}

Process this task using structured tool-use. Return JSON result only."""

    payload = {
        "model": SPARKX_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }

    try:
        req = urllib.request.Request(
            OLLAMA_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {"content": result.get("message", {}).get("content", ""), "raw": result}
    except Exception as e:
        return {"error": str(e)}


def run_daemon():
    print("[SparkX Bridge] Daemon started")
    append_log("memory/event_lineage.log", "Bridge daemon started")

    while True:
        try:
            inbound = read_json("sync/inbound_queue.json") or {"queue": [], "processed_count": 0}
            queue = inbound.get("queue", [])

            if queue:
                item = queue.pop(0)
                append_log("memory/event_lineage.log", f"Processing item: {item.get('id', 'unknown')}")

                result = process_inbound_item(item)

                # Write result to outbound
                outbound = read_json("sync/outbound_results.json") or {"results": [], "total_results": 0}
                outbound["results"].append({
                    "input": item,
                    "output": result,
                    "timestamp": datetime.now().isoformat(),
                })
                outbound["total_results"] = len(outbound["results"])
                outbound["last_written"] = datetime.now().isoformat()
                write_json("sync/outbound_results.json", outbound)

                # Update state
                state = read_json("memory/current_state.json") or {}
                state["last_execution"] = datetime.now().isoformat()
                state["status"] = "active"
                write_json("memory/current_state.json", state)

                # Update inbound queue
                inbound["queue"] = queue
                inbound["processed_count"] = inbound.get("processed_count", 0) + 1
                inbound["last_processed"] = datetime.now().isoformat()
                write_json("sync/inbound_queue.json", inbound)

                append_log("memory/event_lineage.log", f"Completed item: {item.get('id', 'unknown')}")

            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("[SparkX Bridge] Daemon stopped")
            append_log("memory/event_lineage.log", "Bridge daemon stopped")
            break
        except Exception as e:
            print(f"[SparkX Bridge] Error: {e}")
            append_log("memory/event_lineage.log", f"Error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_daemon()
