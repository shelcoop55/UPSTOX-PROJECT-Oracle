"""Minimal repro for /api/health route with trace_id handling."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.api_server import app


def main():
    with app.test_client() as client:
        resp = client.get("/api/health")
        print("status:", resp.status_code)
        print("x-trace-id:", resp.headers.get("X-Trace-ID"))
        print("body:", resp.json)


if __name__ == "__main__":
    main()
