"""
Data extraction services for YouTube
"""
import re
from googleapiclient.discovery import build
from config import Config
import logging

logger = logging.getLogger(__name__)

class DataExtractor:
    """Handles YouTube data extraction"""
    
    def __init__(self):
        if not Config.YOUTUBE_API_KEY:
            raise ValueError("YouTube API key not configured")
        
        self.youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_video_metadata(self, video_id):
        """Fetch video metadata from YouTube API"""
        try:
            request = self.youtube.videos().list(
                part='snippet,statistics',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                raise ValueError(f"Video not found: {video_id}")
            
            video = response['items'][0]
            snippet = video['snippet']
            statistics = video['statistics']
            
            return {
                'id': video_id,
                'title': snippet['title'],
                'channel': snippet['channelTitle'],
                'description': snippet.get('description', ''),
                'published_at': snippet['publishedAt'],
                'thumbnail': snippet['thumbnails']['high']['url'],
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0))
            }
            
        except Exception as e:
            logger.error(f"Error fetching video metadata: {e}")
            raise
    
    def get_video_comments(self, video_id, max_comments=500):
        """Fetch comments from YouTube API"""
        try:
            comments = []
            next_page_token = None
            
            while len(comments) < max_comments:
                request = self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=min(100, max_comments - len(comments)),
                    pageToken=next_page_token,
                    order='relevance'
                )
                
                response = request.execute()
                
                for item in response['items']:
                    comment_data = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'text': comment_data['textDisplay'],
                        'author': comment_data['authorDisplayName'],
                        'published_at': comment_data['publishedAt'],
                        'like_count': comment_data.get('likeCount', 0),
                        'reply_count': item['snippet']['totalReplyCount']
                    })
                
                next_page_token = response.get('nextPageToken')
                
                if not next_page_token:
                    break
            
            logger.info(f"Fetched {len(comments)} comments for video {video_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            raise