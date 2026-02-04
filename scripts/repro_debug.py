"""Minimal repro script for websocket blueprint import."""

import importlib
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    module = importlib.import_module("scripts.blueprints.websocket")
    print("Imported websocket blueprint:", getattr(module, "websocket_bp", None))


if __name__ == "__main__":
    main()
