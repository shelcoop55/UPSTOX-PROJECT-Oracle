"""Minimal repro for IdentityService import resolution."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.services.identity_service import IdentityService


def main():
    service = IdentityService()
    print("IdentityService import OK:", type(service).__name__)


if __name__ == "__main__":
    main()
