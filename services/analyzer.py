"""
AI-powered semantic analysis using Google Gemini
"""
import json
import time
import re
import google.generativeai as genai
from config import Config
import logging

logger = logging.getLogger(__name__)

class SemanticAnalyzer:
    """Handles AI-powered semantic analysis using Gemini"""
    
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")
        
        # Configure the API
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Initialize the model
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        self.last_call_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        if time_since_last < Config.MIN_SECONDS_BETWEEN_GEMINI_CALLS:
            sleep_time = Config.MIN_SECONDS_BETWEEN_GEMINI_CALLS - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()
    
    def _call_gemini(self, prompt, text):
        """Make API call to Gemini"""
        self._rate_limit()
        
        full_prompt = f"{prompt}\n\nText to analyze:\n{text}"
        
        try:
            response = self.model.generate_content(full_prompt)
            
            if not response.text:
                raise ValueError("No response from Gemini API")
            
            text_response = response.text
            
            # Clean markdown formatting if present
            text_response = re.sub(r'^```json\s*', '', text_response)
            text_response = re.sub(r'\s*```$', '', text_response)
            
            return text_response.strip()
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
    
    def analyze_text(self, text, analysis_type="general"):
        """Analyze text using Gemini"""
        try:
            if analysis_type == "ideas":
                prompt = Config.IDEA_EXTRACTION_PROMPT
            else:
                prompt = Config.ANALYSIS_PROMPT
            
            response = self._call_gemini(prompt, text)
            
            if analysis_type == "ideas":
                # Parse numbered list into array
                ideas = []
                for line in response.split('\n'):
                    line = line.strip()
                    if line and re.match(r'^\d+\.', line):
                        idea = re.sub(r'^\d+\.\s*', '', line)
                        ideas.append(idea)
                
                return {'ideas': ideas}
            else:
                # Parse JSON response
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.error(f"Response was: {response}")
            raise ValueError("Invalid JSON response from AI")
        except Exception as e:
            logger.error(f"Error in text analysis: {e}")
            raise
    
    def analyze_bulk_comments(self, comments):
        """Analyze comments in bulk"""
        try:
            # Prepare comments text
            comments_text = ""
            for idx, comment in enumerate(comments[:Config.MAX_COMMENTS_ANALYZE], 1):
                comments_text += f"Comment {idx}: {comment.get('text', '')}\n\n"
            
            # Call Gemini with bulk analysis prompt
            response = self._call_gemini(Config.BULK_ANALYSIS_PROMPT, comments_text)
            
            # Parse JSON response
            analysis = json.loads(response)
            
            # Validate structure
            required_keys = ['overall_sentiment', 'top_entities', 'key_themes', 
                           'emotion_analysis', 'engagement_insights']
            
            for key in required_keys:
                if key not in analysis:
                    logger.warning(f"Missing key in analysis: {key}")
                    analysis[key] = self._get_default_value(key)
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing bulk analysis response: {e}")
            logger.error(f"Response was: {response}")
            raise ValueError("Invalid JSON response from AI")
        except Exception as e:
            logger.error(f"Error in bulk analysis: {e}")
            raise
    
    def _get_default_value(self, key):
        """Get default value for missing analysis keys"""
        defaults = {
            'overall_sentiment': {
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'average_score': 0
            },
            'top_entities': [],
            'key_themes': [],
            'emotion_analysis': {
                'joy': 0,
                'anger': 0,
                'sadness': 0,
                'fear': 0,
                'surprise': 0,
                'trust': 0,
                'anticipation': 0
            },
            'engagement_insights': {
                'constructive_feedback': 0,
                'criticism': 0,
                'suggestions': 0,
                'questions': 0,
                'praise': 0
            }
        }
        return defaults.get(key, {})