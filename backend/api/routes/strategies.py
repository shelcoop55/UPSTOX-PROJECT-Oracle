"""
Strategies API endpoints
"""

from flask import Blueprint, jsonify
from backend.utils.logging.config import get_logger

logger = get_logger(__name__)

strategies_bp = Blueprint('strategies', __name__, url_prefix='/api/strategies')

@strategies_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'strategies'}), 200

__all__ = ['strategies_bp']
