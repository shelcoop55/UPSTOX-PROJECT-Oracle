"""Deprecated compatibility alias for the unified live API client."""

from scripts.upstox_live_api import UpstoxLiveAPI

# Backward compatibility: keep the name but use the unified class.
SimpleUpstoxAPI = UpstoxLiveAPI
