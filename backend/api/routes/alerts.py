"""
Alerts API endpoints
"""

from flask import Blueprint, jsonify
from backend.utils.logging.config import get_logger

logger = get_logger(__name__)

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alerts_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'alerts'}), 200

__all__ = ['alerts_bp']
