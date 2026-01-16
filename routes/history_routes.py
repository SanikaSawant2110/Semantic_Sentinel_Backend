"""
Routes for analysis history
"""
from flask import Blueprint, request, jsonify
from database import get_analysis_history
import logging

logger = logging.getLogger(__name__)
history_bp = Blueprint('history', __name__)

@history_bp.route('/', methods=['GET'])
def get_history():
    """Get analysis history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = get_analysis_history(limit)
        
        return jsonify({
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({'error': str(e)}), 500