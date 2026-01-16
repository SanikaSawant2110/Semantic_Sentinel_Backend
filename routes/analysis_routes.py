"""
Routes for AI analysis
"""
from flask import Blueprint, request, jsonify
from services.analyzer import SemanticAnalyzer
from database import store_analysis
import logging

logger = logging.getLogger(__name__)
analysis_bp = Blueprint('analysis', __name__)
analyzer = SemanticAnalyzer()

@analysis_bp.route('/bulk-comments', methods=['POST'])
def analyze_bulk_comments():
    """Analyze comments in bulk"""
    try:
        data = request.get_json()
        comments = data.get('comments', [])
        video_data = data.get('video_data', {})
        save_to_db = data.get('save_to_db', True)
        
        if not comments:
            return jsonify({'error': 'Comments are required'}), 400
        
        # Analyze comments
        analysis_result = analyzer.analyze_bulk_comments(comments)
        
        # Save to database if requested
        if save_to_db and video_data:
            store_analysis(video_data, analysis_result, comments)
        
        return jsonify({
            'analysis': analysis_result,
            'comments_analyzed': len(comments)
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error analyzing comments: {e}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/ideas', methods=['POST'])
def extract_ideas():
    """Extract actionable ideas from text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        result = analyzer.analyze_text(text, analysis_type="ideas")
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error extracting ideas: {e}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/text', methods=['POST'])
def analyze_text():
    """Analyze text for sentiment and entities"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        result = analyzer.analyze_text(text)
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        return jsonify({'error': str(e)}), 500