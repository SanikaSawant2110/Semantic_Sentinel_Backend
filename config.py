"""
Configuration file for Flask application
Uses environment variables for sensitive data
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # API Keys
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Gemini Configuration
    GEMINI_MODEL = "gemini-1.5-flash"
    GEMINI_API_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1/models/"
    f"{GEMINI_MODEL}:generateContent"
    )
    
    # Database
    DB_FILE = "semantic_sentinel.db"
    
    # Analysis Configuration
    SENTIMENT_THRESHOLDS = {
        'positive': 0.3,
        'neutral_lower': -0.3,
        'neutral_upper': 0.3,
        'negative': -0.3
    }
    
    # Processing Configuration
    MAX_COMMENTS_ANALYZE = 500
    BULK_CHUNK_SIZE = 10
    RATE_LIMIT_DELAY = 30
    MIN_SECONDS_BETWEEN_GEMINI_CALLS = 4.0
    
    # Prompts
    ANALYSIS_PROMPT = """
    Analyze the following text and return a JSON response with:
    1. sentiment_score: a float between -1 (very negative) and 1 (very positive)
    2. sentiment_label: one of "positive", "neutral", or "negative"
    3. entities: a list of important named entities (e.g., PERSON, ORGANIZATION, LOCATION, PRODUCT, EVENT)
    4. themes: a list of main topics or themes
    5. key_phrases: a list of significant phrases
    
    Ensure the response is *only* a valid JSON object. Do not include any markdown formatting like triple backticks.
    """
    
    BULK_ANALYSIS_PROMPT = """
    Analyze the following collection of YouTube comments and provide a comprehensive JSON analysis with:
    
    1. overall_sentiment: {
        "positive": count,
        "neutral": count,
        "negative": count,
        "average_score": float (-1 to 1)
    }
    
    2. top_entities: [
        {"name": "entity_name", "count": frequency, "type": "PERSON|ORGANIZATION|LOCATION|PRODUCT|EVENT|OTHER"}
    ]
    
    3. key_themes: [
        {"theme": "theme_name", "frequency": count, "sentiment": "positive|neutral|negative", "sample_comments": ["comment1", "comment2"]}
    ]
    
    4. emotion_analysis: {
        "joy": count,
        "anger": count,
        "sadness": count,
        "fear": count,
        "surprise": count,
        "trust": count,
        "anticipation": count
    }
    
    5. engagement_insights: {
        "constructive_feedback": count,
        "criticism": count,
        "suggestions": count,
        "questions": count,
        "praise": count
    }
    
    Return *only* a valid JSON object without any markdown formatting.
    
    Comments to analyze (each prefaced with 'Comment N:'):
    """
    
    IDEA_EXTRACTION_PROMPT = """
    Extract actionable insights and improvement suggestions from the following text.
    Focus on:
    - Specific suggestions for improvement
    - Common user requests or needs
    - Identified pain points or issues
    - Opportunities for enhancement
    
    Format the response as a numbered bulleted list. Each suggestion should start with a number followed by a period (e.g., "1. Improve X"). Do not include any additional commentary or introduction/conclusion text.
    """