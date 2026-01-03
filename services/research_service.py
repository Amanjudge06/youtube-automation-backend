"""
Topic Research Service
Uses Perplexity API to research trending topics and understand why they're trending
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class ResearchService:
    """Research trending topics using Perplexity API to understand current relevance"""
    
    def __init__(self):
        self.api_key = config.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = config.RESEARCH_CONFIG["model"]
        self.temperature = config.RESEARCH_CONFIG["temperature"]
        self.max_tokens = config.RESEARCH_CONFIG["max_tokens"]
    
    def research_trending_topic(self, topic_query: str, breakdown_data: Dict = None) -> Optional[Dict]:
        """
        Research why a topic is trending today using Perplexity API with enhanced context
        
        Args:
            topic_query: The trending topic to research
            breakdown_data: Enhanced breakdown data from trends service
            
        Returns:
            Dictionary containing research findings
        """
        try:
            if not self.api_key or self.api_key == "pplx-YOUR_API_KEY_HERE":
                logger.warning("Perplexity API key not configured, skipping research")
                return self._create_fallback_research(topic_query)
            
            logger.info(f"Researching trending topic: {topic_query}")
            if breakdown_data:
                logger.info(f"   Using enhanced breakdown: {breakdown_data.get('topic_category', 'unknown')} category")
                logger.info(f"   Trend timing: {breakdown_data.get('trend_timing', 'unknown')}")
                logger.info(f"   Volume tier: {breakdown_data.get('volume_tier', 'unknown')}")
            
            # Create specific research prompt based on topic type
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Detect if this is likely a sports-related topic
            sports_indicators = ['colts', '49ers', 'niners', 'chiefs', 'patriots', 'cowboys', 'lakers', 'warriors', 'nba', 'nfl', 'monday night football', 'game', 'quarterback', 'touchdown', 'scored']
            is_sports_topic = any(indicator in topic_query.lower() for indicator in sports_indicators)
            
            if is_sports_topic:
                research_prompt = f"""What recent football/sports game or event involving '{topic_query}' happened in the last 24-48 hours (as of {current_date})? 
                
Provide specific details about:
- Which teams played and who won
- Final score and key plays
- Individual player performances (touchdowns, yards, etc.)
- When and where the game was played (Monday Night Football, prime time, etc.)
- Why this game/event is significant or trending
- Any standout performances, records, or storylines

Focus on recent game results, player statistics, and why this is currently trending in sports news."""
            else:
                research_prompt = f"What recent news has come out about '{topic_query}' in the last 24-48 hours (as of {current_date})? Why is this person or topic trending right now? Please provide specific recent events, developments, or news that caused this trend."
            
            # Make API call to Perplexity
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant that provides comprehensive, up-to-date information about trending topics. For sports topics, focus on recent games, scores, player performances, and specific game details. For other topics, provide recent news and developments. Always include specific facts, numbers, and recent events that explain why something is trending."
                    },
                    {
                        "role": "user", 
                        "content": research_prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not content:
                logger.warning("Empty response from Perplexity API")
                return self._create_fallback_research(topic_query)
            
            # Parse and structure the research data
            is_sports = self._is_sports_topic(topic_query)
            research_data = self._parse_research_response(content, topic_query, is_sports=is_sports)
            
            logger.info(f"✅ Research completed for '{topic_query}'")
            logger.info(f"   📄 Summary length: {len(research_data.get('summary', ''))}")
            logger.info(f"   🔍 Key points found: {len(research_data.get('key_points', []))}")
            logger.info(f"   📰 Sources mentioned: {research_data.get('source_count', 0)}")
            
            return research_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Perplexity API: {e}")
            return self._create_fallback_research(topic_query)
        except Exception as e:
            logger.error(f"Unexpected error in research: {e}")
            return self._create_fallback_research(topic_query)
    
    def _is_sports_topic(self, topic: str) -> bool:
        """Determine if a topic is sports-related"""
        sports_keywords = [
            # NFL teams
            'colts', '49ers', 'niners', 'chiefs', 'patriots', 'cowboys', 'steelers', 'packers',
            'ravens', 'bills', 'dolphins', 'jets', 'titans', 'jaguars', 'texans', 'browns',
            'bengals', 'broncos', 'raiders', 'chargers', 'rams', 'cardinals', 'seahawks',
            'saints', 'falcons', 'panthers', 'buccaneers', 'bears', 'lions', 'vikings',
            'eagles', 'giants', 'redskins', 'commanders', 'football',
            
            # NBA teams
            'lakers', 'warriors', 'celtics', 'heat', 'knicks', 'nets', 'sixers', 'raptors',
            'bucks', 'bulls', 'cavaliers', 'pistons', 'pacers', 'hawks', 'hornets', 'magic',
            'wizards', 'nuggets', 'timberwolves', 'thunder', 'blazers', 'jazz', 'suns',
            'kings', 'clippers', 'mavericks', 'rockets', 'spurs', 'grizzlies', 'pelicans',
            'basketball',
            
            # Sports terms
            'monday night football', 'nfl', 'nba', 'quarterback', 'touchdown', 'game',
            'season', 'playoffs', 'championship', 'draft', 'trade', 'injury report',
            'mvp', 'rookie', 'coach', 'stadium', 'field goal', 'interception',
            'rushing', 'passing', 'yards', 'points', 'score', 'win', 'loss'
        ]
        
        return any(keyword in topic.lower() for keyword in sports_keywords)

    def _parse_research_response(self, content: str, topic: str, is_sports: bool = False) -> Dict:
        """Parse the research response into structured data"""
        try:
            # Split content into sections
            lines = content.split('\n')
            sections = {}
            current_section = "summary"
            current_content = []
            
            # Different section headers for sports vs general content
            if is_sports:
                section_headers = ["RECENT GAME", "STANDOUT PERFORMANCES", "GAME SIGNIFICANCE", "TRENDING FACTORS"]
            else:
                section_headers = ["WHY IS IT TRENDING", "CURRENT CONTEXT", "RECENT DEVELOPMENTS", "KEY FACTS", "CURRENT STATUS"]
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                if any(header in line.upper() for header in section_headers):
                    if current_content:
                        sections[current_section] = ' '.join(current_content)
                    
                    if is_sports:
                        if "RECENT GAME" in line.upper():
                            current_section = "game_details"
                        elif "STANDOUT PERFORMANCES" in line.upper():
                            current_section = "player_stats"
                        elif "GAME SIGNIFICANCE" in line.upper():
                            current_section = "game_importance"
                        elif "TRENDING FACTORS" in line.upper():
                            current_section = "trending_reason"
                    else:
                        if "WHY IS IT TRENDING" in line.upper():
                            current_section = "trending_reason"
                        elif "CURRENT CONTEXT" in line.upper():
                            current_section = "background"
                        elif "RECENT DEVELOPMENTS" in line.upper():
                            current_section = "recent_news"
                        elif "KEY FACTS" in line.upper():
                            current_section = "key_facts"
                        elif "CURRENT STATUS" in line.upper():
                            current_section = "current_status"
                    
                    current_content = []
                else:
                    current_content.append(line)
            
            # Add the last section
            if current_content:
                sections[current_section] = ' '.join(current_content)
            
            # Extract key points with sports-specific focus
            key_points = []
            if is_sports:
                # Look for game scores, player stats, team names
                for section_content in sections.values():
                    for line in section_content.split('.'):
                        line = line.strip()
                        if len(line) > 15 and len(line) < 200:
                            # Sports-specific key point indicators
                            if any(indicator in line.lower() for indicator in ['scored', 'touchdown', 'yards', 'points', 'quarter', 'final score', 'won', 'beat', 'defeated']):
                                key_points.append(line.strip())
            else:
                # General key points extraction
                for section_content in sections.values():
                    for line in section_content.split('.'):
                        line = line.strip()
                        if len(line) > 20 and len(line) < 200:
                            if any(char in line for char in ['-', '•', '*']) or line[0].isdigit():
                                key_points.append(line.replace('-', '').replace('•', '').replace('*', '').strip())
            
            # Count potential sources (look for references to news outlets, dates, etc.)
            source_indicators = ['according to', 'reported by', 'announced', 'statement', 'news', 'said', 'confirmed']
            source_count = sum(1 for indicator in source_indicators if indicator.lower() in content.lower())
            
            research_data = {
                "topic": topic,
                "research_timestamp": datetime.now().isoformat(),
                "summary": sections.get("summary", content[:500] + "..." if len(content) > 500 else content),
                "trending_reason": sections.get("trending_reason", ""),
                "background": sections.get("background", ""),
                "recent_news": sections.get("recent_news", ""),
                "key_facts": sections.get("key_facts", ""),
                "current_status": sections.get("current_status", ""),
                "game_details": sections.get("game_details", "") if is_sports else "",
                "player_stats": sections.get("player_stats", "") if is_sports else "",
                "game_importance": sections.get("game_importance", "") if is_sports else "",
                "key_points": key_points[:10],  # Top 10 key points
                "source_count": source_count,
                "full_content": content,
                "full_research": content,  # Add this field for script generator compatibility
                "content_length": len(content),
            }
            
            return research_data
            
        except Exception as e:
            logger.warning(f"Error parsing research response: {e}")
            return self._create_fallback_research(topic, content)
    
    def _create_fallback_research(self, topic: str, content: str = None) -> Dict:
        """Create fallback research data when API is unavailable"""
        logger.info(f"Creating fallback research for: {topic}")
        
        return {
            "topic": topic,
            "research_timestamp": datetime.now().isoformat(),
            "summary": content if content else f"'{topic}' is currently trending. This topic has gained significant attention and search volume recently.",
            "trending_reason": f"'{topic}' is trending due to increased search interest and online activity.",
            "background": f"Background information about '{topic}' - this topic has captured public attention.",
            "recent_news": "Recent developments have contributed to the trending status of this topic.",
            "key_facts": f"Key information about '{topic}' includes its current prominence in search trends.",
            "current_status": "This topic continues to maintain high interest and engagement levels.",
            "key_points": [
                f"'{topic}' is currently trending with high search volume",
                "The topic has gained significant online attention",
                "Multiple factors may contribute to its trending status",
                "Public interest in this topic remains elevated"
            ],
            "source_count": 0,
            "full_content": content if content else f"Fallback research summary for trending topic: {topic}",
            "full_research": content if content else f"Fallback research summary for trending topic: {topic}",
            "content_length": len(content) if content else 0,
            "fallback": True
        }
    
    def get_research_summary(self, research_data: Dict) -> str:
        """Get a concise summary of research findings for script generation"""
        if not research_data:
            return ""
        
        summary_parts = []
        
        # Trending reason
        if research_data.get("trending_reason"):
            summary_parts.append(f"TRENDING REASON: {research_data['trending_reason']}")
        
        # Recent news
        if research_data.get("recent_news"):
            summary_parts.append(f"RECENT NEWS: {research_data['recent_news']}")
        
        # Key facts
        if research_data.get("key_facts"):
            summary_parts.append(f"KEY FACTS: {research_data['key_facts']}")
        
        # Key points
        key_points = research_data.get("key_points", [])
        if key_points:
            summary_parts.append(f"KEY POINTS: {'; '.join(key_points[:5])}")  # Top 5 points
        
        return "\n\n".join(summary_parts)