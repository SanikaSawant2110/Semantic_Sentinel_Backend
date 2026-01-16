"""
Database management for Semantic Sentinel
Handles SQLite operations
"""
import sqlite3
import json
import logging
from config import Config
from datetime import datetime

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(Config.DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Video analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                video_title TEXT,
                channel_name TEXT,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_comments_analyzed INTEGER,
                average_sentiment REAL,
                analysis_data TEXT,
                source_type TEXT DEFAULT 'comments',
                UNIQUE(video_id, analysis_date, source_type)
            )
        ''')
        
        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                db_video_analysis_id INTEGER,
                video_id TEXT NOT NULL,
                comment_id TEXT UNIQUE,
                author TEXT,
                text TEXT,
                published_at TIMESTAMP,
                like_count INTEGER,
                reply_count INTEGER DEFAULT 0,
                sentiment_score REAL DEFAULT 0.0,
                FOREIGN KEY(db_video_analysis_id) REFERENCES video_analysis(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def store_analysis(video_data, analysis_result, comments=None):
    """Store complete analysis results"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        video_id = video_data.get('id')
        video_title = video_data.get('title')
        channel_name = video_data.get('channel')
        
        total_items = len(comments) if comments else 0
        avg_sentiment = analysis_result.get('overall_sentiment', {}).get('average_score', 0.0)
        
        cursor.execute('''
            INSERT INTO video_analysis 
            (video_id, video_title, channel_name, total_comments_analyzed, 
             average_sentiment, analysis_data, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_id,
            video_title,
            channel_name,
            total_items,
            avg_sentiment,
            json.dumps(analysis_result),
            'comments'
        ))
        
        db_analysis_id = cursor.lastrowid
        
        if comments:
            for comment in comments:
                comment_sentiment = 0.0
                try:
                    comment_sentiment = float(comment.get('sentiment_score', 0.0))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid sentiment score for comment {comment.get('id')}")
                
                cursor.execute('''
                    INSERT OR IGNORE INTO comments 
                    (db_video_analysis_id, video_id, comment_id, author, text, 
                     published_at, like_count, reply_count, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    db_analysis_id,
                    video_id,
                    comment.get('id'),
                    comment.get('author'),
                    comment.get('text'),
                    comment.get('published_at'),
                    comment.get('like_count', 0),
                    comment.get('reply_count', 0),
                    comment_sentiment
                ))
        
        conn.commit()
        conn.close()
        logger.info(f"Analysis for video {video_id} stored with ID {db_analysis_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing analysis: {e}")
        return False

def get_analysis_history(limit=10):
    """Retrieve recent analysis history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT video_id, video_title, channel_name, analysis_date, 
                   total_comments_analyzed, average_sentiment, source_type, analysis_data
            FROM video_analysis
            ORDER BY analysis_date DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        return []