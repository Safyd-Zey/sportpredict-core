"""Smoke test of a running SportPredict API (standard library only).

Usage: python scripts/smoke_test.py http://host:port
Used by the Jenkins pipeline against the built container and the Kubernetes Service.
"""

import json
import sys
import time
import urllib.parse
import urllib.request


def get(base: str, path: str, **params) -> dict | list:
    url = f"{base}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.load(resp)


def wait_healthy(base: str, timeout_s: float = 60.0) -> dict:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            return get(base, "/health")
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)


def main(base: str) -> None:
    health = wait_healthy(base.rstrip("/"))
    assert health["status"] == "ok", health
    print(f"health: v{health['version']}, {health['matches']} matches up to {health['data_until']}")

    top = get(base, "/v1/ratings", top=3)
    assert len(top) == 3 and top[0]["rating"] >= top[1]["rating"], top
    print("top-3:", ", ".join(f"{r['team']} {r['rating']}" for r in top))

    pred = get(base, "/v1/predict", home=top[0]["team"], away=top[1]["team"])
    probs = pred["probabilities"]
    assert abs(sum(probs.values()) - 1.0) < 1e-3, probs
    print(f"{pred['home']} vs {pred['away']}: {probs}")
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000")
