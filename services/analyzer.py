"""
Semantic analysis using Gemini API
"""
import requests
import json
import time
import logging
from config import Config

logger = logging.getLogger(__name__)

class SemanticAnalyzer:
    """Advanced semantic analysis using Gemini API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 120
        self._last_gemini_call_ts = 0.0
        
        if not Config.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")
    
    def _make_api_request(self, prompt):
        """Make a request to the Gemini API with error handling"""
        headers = {"Content-Type": "application/json"}
        params = {"key": Config.GEMINI_API_KEY}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192,
                "topP": 0.95,
                "topK": 40,
                "responseMimeType": "application/json"
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
            ]
        }
        
        # Rate limiting
        now = time.time()
        elapsed = now - self._last_gemini_call_ts
        if elapsed < Config.MIN_SECONDS_BETWEEN_GEMINI_CALLS:
            sleep_time = Config.MIN_SECONDS_BETWEEN_GEMINI_CALLS - elapsed
            time.sleep(sleep_time)
        
        self._last_gemini_call_ts = time.time()
        
        try:
            response = self.session.post(
                Config.GEMINI_API_ENDPOINT,
                headers=headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise ValueError("Gemini free-tier quota exceeded. Please wait ~60 seconds and try again.")
            
            error_details = e.response.text
            try:
                error_json = e.response.json()
                if 'error' in error_json and 'message' in error_json['error']:
                    error_details = error_json['error']['message']
            except json.JSONDecodeError:
                pass
            
            logger.error(f"Gemini API HTTP error: {e.response.status_code} - {error_details}")
            raise ValueError(f"Gemini API request failed: {error_details}")
            
        except Exception as e:
            logger.error(f"Unexpected error during API request: {e}")
            raise ValueError(f"An unexpected error occurred: {e}")
    
    def _extract_json_response(self, response_data):
        """Extract and parse JSON from API response"""
        try:
            if not response_data.get('candidates'):
                if response_data.get('promptFeedback', {}).get('blockReason'):
                    reason = response_data['promptFeedback']['blockReason']
                    raise ValueError(f"Gemini API blocked request: {reason}")
                raise ValueError("API response has no candidates")
            
            candidate = response_data["candidates"][0]
            finish_reason = candidate.get("finishReason")
            parts = candidate.get("content", {}).get("parts", [])
            
            if finish_reason == "SAFETY":
                raise ValueError("Gemini blocked response due to safety filtering")
            
            if not parts or not parts[0].get("text", "").strip():
                raise ValueError("Gemini returned empty response")
            
            content = parts[0]["text"].strip()
            parsed_json = json.loads(content)
            
            # Normalize entities
            if 'entities' in parsed_json and isinstance(parsed_json['entities'], list):
                parsed_json['entities'] = [
                    item.get('name') if isinstance(item, dict) else str(item)
                    for item in parsed_json['entities']
                ]
                parsed_json['entities'] = [e for e in parsed_json['entities'] if e]
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
            raise ValueError(f"Failed to decode JSON from API response: {e}")
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            raise ValueError(f"Error during JSON extraction: {e}")
    
    def analyze_bulk_comments(self, comments, progress_callback=None):
        """Analyze comments in bulk"""
        if not comments:
            return {}
        
        chunk_size = Config.BULK_CHUNK_SIZE
        total_chunks = (len(comments) + chunk_size - 1) // chunk_size
        
        aggregated_results = {
            "overall_sentiment": {"positive": 0, "neutral": 0, "negative": 0, "average_score": 0.0},
            "top_entities": {},
            "key_themes": {},
            "emotion_analysis": {
                "joy": 0, "anger": 0, "sadness": 0, "fear": 0,
                "surprise": 0, "trust": 0, "anticipation": 0
            },
            "engagement_insights": {
                "constructive_feedback": 0, "criticism": 0,
                "suggestions": 0, "questions": 0, "praise": 0
            }
        }
        
        total_score_sum = 0.0
        processed_comments_count = 0
        
        for i in range(0, len(comments), chunk_size):
            chunk = comments[i:i + chunk_size]
            chunk_texts = [
                f"Comment {idx+1}: {c.get('text', '').strip()}"
                for idx, c in enumerate(chunk) if c.get('text', '').strip()
            ]
            
            if not chunk_texts:
                continue
            
            prompt = Config.BULK_ANALYSIS_PROMPT + "\n".join(chunk_texts)
            
            try:
                if progress_callback:
                    progress_callback(i, len(comments), f"Analyzing chunk {i // chunk_size + 1}/{total_chunks}")
                
                response = self._make_api_request(prompt)
                result = self._extract_json_response(response)
                
                # Aggregate sentiment
                sentiment = result.get("overall_sentiment", {})
                aggregated_results["overall_sentiment"]["positive"] += sentiment.get("positive", 0)
                aggregated_results["overall_sentiment"]["neutral"] += sentiment.get("neutral", 0)
                aggregated_results["overall_sentiment"]["negative"] += sentiment.get("negative", 0)
                
                chunk_avg_score = float(sentiment.get("average_score", 0.0))
                total_score_sum += chunk_avg_score * len(chunk_texts)
                processed_comments_count += len(chunk_texts)
                
                # Aggregate entities
                for entity in result.get("top_entities", []):
                    name = str(entity.get("name", "")).strip().lower()
                    if name:
                        if name in aggregated_results["top_entities"]:
                            aggregated_results["top_entities"][name]["count"] += entity.get("count", 1)
                        else:
                            aggregated_results["top_entities"][name] = {
                                "name": str(entity.get("name")),
                                "count": entity.get("count", 1),
                                "type": entity.get("type", "OTHER")
                            }
                
                # Aggregate themes
                for theme_data in result.get("key_themes", []):
                    theme_name = str(theme_data.get("theme", "")).strip().lower()
                    if theme_name:
                        if theme_name in aggregated_results["key_themes"]:
                            aggregated_results["key_themes"][theme_name]["frequency"] += theme_data.get("frequency", 1)
                            existing_samples = set(aggregated_results["key_themes"][theme_name].get("sample_comments", []))
                            new_samples = [
                                str(c) for c in theme_data.get("sample_comments", [])
                                if str(c) not in existing_samples
                            ]
                            aggregated_results["key_themes"][theme_name]["sample_comments"].extend(new_samples)
                        else:
                            theme_data["sample_comments"] = [str(c) for c in theme_data.get("sample_comments", [])]
                            aggregated_results["key_themes"][theme_name] = theme_data
                
                # Aggregate emotions
                for emotion, count in result.get("emotion_analysis", {}).items():
                    if emotion in aggregated_results["emotion_analysis"]:
                        aggregated_results["emotion_analysis"][emotion] += count
                
                # Aggregate engagement
                for insight, count in result.get("engagement_insights", {}).items():
                    if insight in aggregated_results["engagement_insights"]:
                        aggregated_results["engagement_insights"][insight] += count
                
                if i + len(chunk) < len(comments):
                    time.sleep(Config.RATE_LIMIT_DELAY)
                    
            except Exception as e:
                logger.error(f"Error processing chunk {i // chunk_size + 1}: {e}")
                processed_comments_count += len(chunk_texts)
                continue
        
        # Calculate average sentiment
        if processed_comments_count > 0:
            aggregated_results["overall_sentiment"]["average_score"] = total_score_sum / processed_comments_count
        
        # Sort entities and themes
        aggregated_results["top_entities"] = sorted(
            list(aggregated_results["top_entities"].values()),
            key=lambda x: x.get("count", 0),
            reverse=True
        )[:20]
        
        aggregated_results["key_themes"] = sorted(
            list(aggregated_results["key_themes"].values()),
            key=lambda x: x.get("frequency", 0),
            reverse=True
        )
        
        return aggregated_results
    
    def analyze_text(self, text, analysis_type="general"):
        """Analyze text for ideas or general analysis"""
        if not text.strip():
            return {}
        
        if analysis_type == "ideas":
            prompt = Config.IDEA_EXTRACTION_PROMPT + f"\n\nText: {text}"
            try:
                response = self._make_api_request(prompt)
                
                if response.get('promptFeedback', {}).get('blockReason'):
                    reason = response['promptFeedback']['blockReason']
                    raise ValueError(f"Request blocked: {reason}")
                
                content = response['candidates'][0]['content']['parts'][0]['text']
                import re
                ideas = [
                    re.sub(r'^\d+\.\s*', '', line).strip()
                    for line in content.split('\n')
                    if re.match(r'^\d+\.', line.strip())
                ]
                return {"ideas": ideas}
                
            except Exception as e:
                logger.error(f"Error extracting ideas: {e}")
                raise ValueError(f"Failed to extract ideas: {e}")
        else:
            prompt = Config.ANALYSIS_PROMPT + f"\n\nText: {text}"
            try:
                response = self._make_api_request(prompt)
                return self._extract_json_response(response)
            except Exception as e:
                logger.error(f"Error analyzing text: {e}")
                raise ValueError(f"Failed to analyze text: {e}")