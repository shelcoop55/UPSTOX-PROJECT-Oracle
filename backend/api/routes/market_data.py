"""
Market data API endpoints
Handles quotes, OHLC data, and option chains
"""

from flask import Blueprint, jsonify
from backend.utils.logging.config import get_logger

logger = get_logger(__name__)

market_data_bp = Blueprint('market_data', __name__, url_prefix='/api/market-data')

@market_data_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'market_data'}), 200

__all__ = ['market_data_bp']
