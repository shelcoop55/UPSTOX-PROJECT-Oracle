"""
Analytics API endpoints
"""

from flask import Blueprint, jsonify
from backend.utils.logging.config import get_logger

logger = get_logger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'analytics'}), 200

__all__ = ['analytics_bp']
