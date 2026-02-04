"""Shared mixin for building auth headers with optional token."""

from typing import Dict


class OptionalAuthHeadersMixin:
    """Mixin that returns JSON headers and adds Authorization if token exists."""

    def _get_headers(self) -> Dict[str, str]:
        token = self.auth_manager.get_valid_token()
        if not token:
            return {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
