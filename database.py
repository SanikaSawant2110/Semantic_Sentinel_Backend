"""
Database module for Semantic Sentinel
Handles SQLite database operations
"""
import sqlite3
import json
from datetime import datetime
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(Config.DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create analyses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            video_title TEXT,
            channel_name TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_comments_analyzed INTEGER,
            average_sentiment REAL,
            analysis_data TEXT,
            UNIQUE(video_id, analysis_date)
        )
    ''')
    
    # Create comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            comment_text TEXT,
            author TEXT,
            published_at TIMESTAMP,
            like_count INTEGER,
            reply_count INTEGER,
            sentiment_score REAL,
            FOREIGN KEY (analysis_id) REFERENCES analyses (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def store_analysis(video_data, analysis_result, comments):
    """Store analysis results in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert analysis record
        cursor.execute('''
            INSERT INTO analyses 
            (video_id, video_title, channel_name, total_comments_analyzed, average_sentiment, analysis_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            video_data.get('id'),
            video_data.get('title'),
            video_data.get('channel'),
            len(comments),
            analysis_result.get('overall_sentiment', {}).get('average_score', 0),
            json.dumps(analysis_result)
        ))
        
        analysis_id = cursor.lastrowid
        
        # Insert comments
        for comment in comments:
            cursor.execute('''
                INSERT INTO comments 
                (analysis_id, comment_text, author, published_at, like_count, reply_count, sentiment_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_id,
                comment.get('text'),
                comment.get('author'),
                comment.get('published_at'),
                comment.get('like_count', 0),
                comment.get('reply_count', 0),
                comment.get('sentiment_score')
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Analysis stored successfully with ID: {analysis_id}")
        
        return analysis_id
        
    except Exception as e:
        logger.error(f"Error storing analysis: {e}")
        raise

def get_analysis_history(limit=10):
    """Retrieve analysis history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
                video_id,
                video_title,
                channel_name,
                analysis_date,
                total_comments_analyzed,
                average_sentiment
            FROM analyses
            ORDER BY analysis_date DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'video_id': row['video_id'],
                'video_title': row['video_title'],
                'channel_name': row['channel_name'],
                'analysis_date': row['analysis_date'],
                'total_comments_analyzed': row['total_comments_analyzed'],
                'average_sentiment': row['average_sentiment']
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise

def get_analysis_by_id(analysis_id):
    """Retrieve specific analysis by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analyses WHERE id = ?
        ''', (analysis_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Get associated comments
        cursor.execute('''
            SELECT * FROM comments WHERE analysis_id = ?
        ''', (analysis_id,))
        
        comments = cursor.fetchall()
        conn.close()
        
        analysis = {
            'id': row['id'],
            'video_id': row['video_id'],
            'video_title': row['video_title'],
            'channel_name': row['channel_name'],
            'analysis_date': row['analysis_date'],
            'total_comments_analyzed': row['total_comments_analyzed'],
            'average_sentiment': row['average_sentiment'],
            'analysis_data': json.loads(row['analysis_data']),
            'comments': [dict(comment) for comment in comments]
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error fetching analysis: {e}")
        raise