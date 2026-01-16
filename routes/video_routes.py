"""
Routes for video information and comments
"""
from flask import Blueprint, request, jsonify
from services.extractors import DataExtractor
import logging

logger = logging.getLogger(__name__)
video_bp = Blueprint('video', __name__)
extractor = DataExtractor()

@video_bp.route('/extract-id', methods=['POST'])
def extract_video_id():
    """Extract video ID from URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        video_id = extractor.extract_video_id(url)
        
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        return jsonify({'video_id': video_id})
        
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
        return jsonify({'error': str(e)}), 500

@video_bp.route('/metadata/<video_id>', methods=['GET'])
def get_metadata(video_id):
    """Get video metadata"""
    try:
        metadata = extractor.get_video_metadata(video_id)
        return jsonify(metadata)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}")
        return jsonify({'error': str(e)}), 500

@video_bp.route('/comments/<video_id>', methods=['GET'])
def get_comments(video_id):
    """Get video comments"""
    try:
        max_comments = request.args.get('max_comments', 500, type=int)
        comments = extractor.get_video_comments(video_id, max_comments)
        
        return jsonify({
            'comments': comments,
            'count': len(comments)
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")
        return jsonify({'error': str(e)}), 500