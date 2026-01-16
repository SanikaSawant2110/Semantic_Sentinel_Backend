"""
Data extraction services for YouTube API
"""
import requests
import logging
import re
from config import Config

logger = logging.getLogger(__name__)

class DataExtractor:
    """Handles YouTube data extraction"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|watch\?.*v=)|youtu\.be\/)([^"&?\/\s]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_metadata(self, video_id):
        """Fetch video metadata"""
        if not Config.YOUTUBE_API_KEY:
            raise ValueError("YouTube API key not configured")
        
        url = (
            f"https://www.googleapis.com/youtube/v3/videos"
            f"?part=snippet,statistics&id={video_id}&key={Config.YOUTUBE_API_KEY}"
        )
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('items'):
                raise ValueError("Video not found or invalid video ID")
            
            item = data['items'][0]
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            
            return {
                'id': video_id,
                'title': snippet.get('title', 'N/A'),
                'channel': snippet.get('channelTitle', 'N/A'),
                'description': snippet.get('description', 'No description available'),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'view_count': statistics.get('viewCount', 0),
                'like_count': statistics.get('likeCount', 0),
                'comment_count': statistics.get('commentCount', 0)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching metadata: {e}")
            raise ValueError(f"Error fetching video metadata: {e}")
    
    def get_video_comments(self, video_id, max_comments=500):
        """Fetch video comments with pagination"""
        if not Config.YOUTUBE_API_KEY:
            raise ValueError("YouTube API key not configured")
        
        comments = []
        next_page_token = None
        api_max_results = 100
        total_fetched = 0
        
        while total_fetched < max_comments:
            url = (
                f"https://www.googleapis.com/youtube/v3/commentThreads"
                f"?part=snippet&videoId={video_id}"
                f"&key={Config.YOUTUBE_API_KEY}"
                f"&maxResults={min(api_max_results, max_comments - total_fetched)}"
            )
            
            if next_page_token:
                url += f"&pageToken={next_page_token}"
            
            try:
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                if not items:
                    break
                
                for item in items:
                    if total_fetched >= max_comments:
                        break
                    
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'id': item['id'],
                        'author': comment.get('authorDisplayName', 'Unknown'),
                        'text': comment.get('textDisplay', ''),
                        'published_at': comment.get('publishedAt', ''),
                        'like_count': comment.get('likeCount', 0),
                        'reply_count': item['snippet'].get('totalReplyCount', 0)
                    })
                    total_fetched += 1
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token or total_fetched >= max_comments:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching comments: {e}")
                raise ValueError(f"Error fetching comments: {e}")
        
        logger.info(f"Fetched {len(comments)} comments for video {video_id}")
        return comments