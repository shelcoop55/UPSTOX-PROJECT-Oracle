"""
Admin API endpoints
"""

from flask import Blueprint, jsonify
from backend.utils.logging.config import get_logger

logger = get_logger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'admin'}), 200

__all__ = ['admin_bp']
