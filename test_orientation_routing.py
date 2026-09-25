"""Verify the Ori Harness runtime routing live.

Hits the multi-llm-runtime local server (which already embeds
OpenRouter fallback in llm_runtime.py). The API contract is:

  POST /complete  body: {prompt, task_type, system, max_tokens, temperature}

The server does NOT expose orchestrator/model at the HTTP layer;
it resolves the backend internally (LM Studio -> Ollama -> OpenRouter)
and returns {ok, content, tokens, model, backend}.
"""

import json, os, sys, time, unittest
from pathlib import Path
import requests

BASE = "http://127.0.0.1:8000"


class TestRuntimeRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Give the server a moment if it was just started
        time.sleep(1)

    def _post_complete(self, **body):
        r = requests.post(f"{BASE}/complete", json=body, timeout=120)
        return r

    def test_health_endpoint(self):
        r = requests.get(f"{BASE}/health", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["service"], "AEGENTIS-AI")
        stats = data["stats"]
        self.assertIn("openrouter_available", stats)
        print(f"  health stats: {json.dumps(stats, indent=2)}")

    def test_oriented_completion(self):
        r = self._post_complete(
            prompt="SYSTEM_CHECK: Verify cognitive bus routing capability.",
            task_type="reasoning",
            system="You are the AEGENTIS Ori Harness verification agent.",
            max_tokens=256,
            temperature=0.2,
        )
        self.assertEqual(r.status_code, 200, f"Unexpected status {r.status_code}: {r.text}")
        data = r.json()
        self.assertTrue(data["ok"], f"Completion failed: {data.get('error')}")
        self.assertTrue(len(data["content"]) > 0, "Empty response")
        self.assertIn("backend", data)
        print(f"  backend : {data['backend']}")
        print(f"  model   : {data.get('model')}")
        print(f"  tokens  : {data.get('tokens')}")
        print(f"  ok      : {data['ok']}")
        print()
        print(f"=== ORI HARNESS RESPONSE ({data['backend']}) ===")
        print(data["content"])
        print("=== END ===")


if __name__ == "__main__":
    # Ensure OPENROUTER_API_KEY is reachable for the import chain
    env_path = Path("C:/Aegentix/.config/aegentix.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    tests = unittest.TestLoader().loadTestsFromTestCase(TestRuntimeRouting)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(tests)
    sys.exit(0 if result.wasSuccessful() else 1)
