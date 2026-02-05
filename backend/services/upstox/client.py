"""
Production-Grade Upstox API Trading Client

This module provides a robust, fault-tolerant trading client for the Upstox API.
Built using raw HTTP requests (NO SDK) for full control over error handling and data parsing.

Reference: docs/Upstox.md - Complete Upstox API Documentation

Key Features:
- Defensive JSON parsing (never assumes keys exist)
- Comprehensive error handling with custom exceptions
- Rate limiting with exponential backoff
- JWT Bearer token management
- Type hints and comprehensive docstrings
- Logging (no print statements)
- Environment-based configuration

Author: Senior Python Backend Engineer
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class UpstoxAPIError(Exception):
    """Base exception for all Upstox API errors"""
    pass


class AuthenticationError(UpstoxAPIError):
    """Raised when authentication fails (401)"""
    pass


class RateLimitError(UpstoxAPIError):
    """Raised when rate limit is exceeded (429)"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class InvalidResponseError(UpstoxAPIError):
    """Raised when response is not valid JSON or has unexpected format"""
    pass


class InstrumentNotFoundError(UpstoxAPIError):
    """Raised when instrument key cannot be found"""
    pass


# ============================================================================
# Helper Functions for Defensive JSON Parsing
# ============================================================================

def safe_get(data: Any, *keys: str, default: Any = None) -> Any:
    """
    Safely navigate nested dictionaries without assuming keys exist.
    
    Args:
        data: The dictionary or nested structure to navigate
        *keys: Variable number of keys to navigate through
        default: Default value to return if key doesn't exist
    
    Returns:
        The value at the specified path or default
        
    Example:
        >>> data = {'data': {'ltp': 100.5}}
        >>> safe_get(data, 'data', 'ltp', default=0)
        100.5
        >>> safe_get(data, 'data', 'missing', default=0)
        0
    """
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result if result is not None else default


def parse_json_safely(response: requests.Response) -> Dict[str, Any]:
    """
    Safely parse JSON from response, handling HTML/non-JSON responses.
    
    Args:
        response: The requests Response object
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        InvalidResponseError: If response is not valid JSON
        
    Example:
        This handles cases where proxies return HTML errors instead of JSON
    """
    try:
        return response.json()
    except ValueError as e:
        # Common issue: Proxy returns HTML error page instead of JSON
        logger.error(f"Invalid JSON response: {response.text[:200]}")
        raise InvalidResponseError(
            f"Expected JSON but got: {response.text[:100]}..."
        ) from e


# ============================================================================
# Main Upstox Client
# ============================================================================

class UpstoxClient:
    """
    Production-grade Upstox API client using raw HTTP requests.
    
    Attributes:
        BASE_URL: Base URL for Upstox API v2
        session: Requests session with retry configuration
        
    Example:
        >>> client = UpstoxClient(api_key="your_key", access_token="token")
        >>> profile = client.get_profile()
        >>> print(profile['user_name'])
    """
    
    # Base URL as per Upstox API documentation
    # Reference: docs/Upstox.md - All endpoints use this base
    BASE_URL = "https://api.upstox.com/v2"
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        access_token: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        """
        Initialize Upstox client with credentials.
        
        Args:
            api_key: Upstox API key (loaded from UPSTOX_API_KEY env var if not provided)
            access_token: JWT access token (loaded from UPSTOX_ACCESS_TOKEN if not provided)
            redirect_uri: OAuth redirect URI (loaded from UPSTOX_REDIRECT_URI if not provided)
            
        Note:
            Credentials should be loaded from environment variables for security.
            Never hardcode credentials in source code.
        """
        self.api_key = api_key or os.getenv('UPSTOX_API_KEY')
        self.access_token = access_token or os.getenv('UPSTOX_ACCESS_TOKEN')
        self.redirect_uri = redirect_uri or os.getenv('UPSTOX_REDIRECT_URI')
        
        # Initialize session with retry strategy
        self.session = self._create_session()
        
        logger.info("UpstoxClient initialized")
        logger.debug(f"Base URL: {self.BASE_URL}")
        
    def _create_session(self) -> requests.Session:
        """
        Create requests session with automatic retry logic.
        
        Returns:
            Configured requests.Session object
            
        Note:
            Implements exponential backoff for transient failures (502, 503, 504)
        """
        session = requests.Session()
        
        # Configure retry strategy - handles transient failures
        retry_strategy = Retry(
            total=3,
            status_forcelist=[502, 503, 504],  # Retry on server errors
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # Safe methods only
            backoff_factor=1  # 1, 2, 4 seconds between retries
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API request with JWT Bearer token.
        
        Returns:
            Dictionary of HTTP headers
            
        Raises:
            AuthenticationError: If access token is not available
            
        Note:
            JWT Bearer token format as per Upstox API documentation
        """
        if not self.access_token:
            raise AuthenticationError(
                "No access token available. Please authenticate first."
            )
        
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response with comprehensive error checking.
        
        Args:
            response: The requests Response object
            
        Returns:
            Parsed JSON response data
            
        Raises:
            AuthenticationError: On 401 status
            RateLimitError: On 429 status
            InvalidResponseError: On malformed JSON
            UpstoxAPIError: On other errors
        """
        # Log request details
        logger.info(f"API Request: {response.request.method} {response.url}")
        logger.info(f"Response Status: {response.status_code}")
        
        # Handle authentication failure
        if response.status_code == 401:
            logger.error("Authentication failed - Invalid or expired token")
            raise AuthenticationError("Authentication failed. Token may be expired.")
        
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            retry_seconds = int(retry_after) if retry_after else 60
            logger.warning(f"Rate limit exceeded. Retry after {retry_seconds} seconds")
            raise RateLimitError(
                f"Rate limit exceeded. Retry after {retry_seconds} seconds",
                retry_after=retry_seconds
            )
        
        # Handle success
        if response.status_code == 200:
            data = parse_json_safely(response)
            logger.debug(f"Response data keys: {list(data.keys())}")
            return data
        
        # Handle other errors
        logger.error(f"API Error {response.status_code}: {response.text}")
        raise UpstoxAPIError(
            f"API request failed with status {response.status_code}: {response.text}"
        )
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Upstox API with error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (will be appended to BASE_URL)
            params: URL parameters
            data: Request body data
            timeout: Request timeout in seconds
            
        Returns:
            Parsed API response
            
        Raises:
            Various UpstoxAPIError subclasses based on response
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=timeout
            )
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {timeout} seconds")
            raise UpstoxAPIError(f"Request timeout after {timeout} seconds")
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise UpstoxAPIError(f"Connection error: {e}")
    
    # ========================================================================
    # User Profile & Account APIs
    # ========================================================================
    
    def get_profile(self) -> Dict[str, Any]:
        """
        Get user profile information.
        
        Returns:
            User profile data including name, email, exchanges, etc.
            
        Raises:
            AuthenticationError: If authentication fails
            UpstoxAPIError: For other API errors
            
        Example:
            >>> client = UpstoxClient(access_token="your_token")
            >>> profile = client.get_profile()
            >>> print(f"User: {profile.get('user_name')}")
            >>> print(f"Email: {profile.get('email')}")
            
        Reference:
            docs/Upstox.md - GET /user/profile
        """
        logger.info("Fetching user profile")
        response = self._make_request("GET", "/user/profile")
        
        # Defensive parsing - never assume keys exist
        profile_data = safe_get(response, 'data', default={})
        
        user_name = safe_get(profile_data, 'user_name', default='Unknown')
        logger.info(f"Profile fetched for user: {user_name}")
        
        return profile_data
    
    def get_funds_and_margin(self) -> Dict[str, Any]:
        """
        Get user's fund and margin information.
        
        Returns:
            Dictionary containing fund and margin details
            
        Reference:
            docs/Upstox.md - GET /user/get-funds-and-margin
        """
        logger.info("Fetching funds and margin")
        response = self._make_request("GET", "/user/get-funds-and-margin")
        return safe_get(response, 'data', default={})
    
    # ========================================================================
    # Portfolio APIs
    # ========================================================================
    
    def get_holdings(self) -> List[Dict[str, Any]]:
        """
        Get user's long-term holdings.
        
        Returns:
            List of holdings with details
            
        Example:
            >>> holdings = client.get_holdings()
            >>> for holding in holdings:
            ...     print(f"{holding.get('tradingsymbol')}: {holding.get('quantity')}")
            
        Reference:
            docs/Upstox.md - GET /portfolio/long-term-holdings
        """
        logger.info("Fetching holdings")
        response = self._make_request("GET", "/portfolio/long-term-holdings")
        holdings = safe_get(response, 'data', default=[])
        logger.info(f"Fetched {len(holdings)} holdings")
        return holdings
    
    def get_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get user's open positions.
        
        Returns:
            Dictionary with 'day' and 'net' position lists
            
        Example:
            >>> positions = client.get_positions()
            >>> day_positions = positions.get('day', [])
            >>> net_positions = positions.get('net', [])
            
        Reference:
            docs/Upstox.md - GET /portfolio/short-term-positions
        """
        logger.info("Fetching positions")
        response = self._make_request("GET", "/portfolio/short-term-positions")
        positions = safe_get(response, 'data', default={})
        
        day_count = len(safe_get(positions, 'day', default=[]))
        net_count = len(safe_get(positions, 'net', default=[]))
        logger.info(f"Fetched {day_count} day positions, {net_count} net positions")
        
        return positions
    
    # ========================================================================
    # Market Data APIs
    # ========================================================================
    
    def get_market_quote(self, instrument_key: str) -> Dict[str, Any]:
        """
        Get live market quote for a single instrument.
        
        Args:
            instrument_key: Upstox instrument key (format: NSE_EQ|INE...)
            
        Returns:
            Market quote data with last price, volume, etc.
            
        Example:
            >>> quote = client.get_market_quote("NSE_EQ|INE669E01016")
            >>> ltp = safe_get(quote, 'last_price', default=0)
            >>> print(f"LTP: {ltp}")
            
        Note:
            Upstox uses instrument keys in format: EXCHANGE_SEGMENT|ISIN
            Example: NSE_EQ|INE669E01016 for Infy on NSE
            
        Reference:
            docs/Upstox.md - GET /market-quote/quotes
        """
        logger.info(f"Fetching market quote for {instrument_key}")
        
        response = self._make_request(
            "GET",
            "/market-quote/quotes",
            params={"instrument_key": instrument_key}
        )
        
        # Response format: {'data': {instrument_key: {quote_data}}}
        all_quotes = safe_get(response, 'data', default={})
        quote = safe_get(all_quotes, instrument_key, default={})
        
        ltp = safe_get(quote, 'last_price', default=0)
        logger.info(f"Quote fetched - LTP: {ltp}")
        
        return quote
    
    def get_historical_candles(
        self,
        instrument_key: str,
        interval: str,
        from_date: str,
        to_date: str
    ) -> List[Dict[str, Any]]:
        """
        Get historical candle data.
        
        Args:
            instrument_key: Upstox instrument key (format: NSE_EQ|INE...)
            interval: Candle interval (1minute, 30minute, day, week, month)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            
        Returns:
            List of candles with OHLCV data
            
        Example:
            >>> candles = client.get_historical_candles(
            ...     "NSE_EQ|INE669E01016",
            ...     "day",
            ...     "2024-01-01",
            ...     "2024-01-31"
            ... )
            
        Reference:
            docs/Upstox.md - GET /historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
        """
        endpoint = f"/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        logger.info(f"Fetching historical candles: {instrument_key} {interval}")
        
        response = self._make_request("GET", endpoint)
        candles = safe_get(response, 'data', 'candles', default=[])
        logger.info(f"Fetched {len(candles)} candles")
        
        return candles


# ============================================================================
# Factory Function
# ============================================================================

def create_client(
    api_key: Optional[str] = None,
    access_token: Optional[str] = None
) -> UpstoxClient:
    """
    Factory function to create UpstoxClient instance.
    
    Args:
        api_key: API key (optional, loaded from env)
        access_token: Access token (optional, loaded from env)
        
    Returns:
        Configured UpstoxClient instance
        
    Example:
        >>> from backend.services.upstox.client import create_client
        >>> client = create_client()
        >>> profile = client.get_profile()
    """
    return UpstoxClient(api_key=api_key, access_token=access_token)
