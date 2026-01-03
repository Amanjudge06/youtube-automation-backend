"""
Trending Topics Service
Fetches real-time and daily trending topics using SERP API with detailed breakdown
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)


class TrendsService:
    """Fetch trending topics from Google Trends via SERP API with daily breakdown and analysis"""
    
    def __init__(self):
        self.api_key = config.SERP_API_KEY
        self.base_url = "https://serpapi.com/search"
        self.region = config.TRENDING_CONFIG["region"]
        self.language = config.TRENDING_CONFIG["language"]
    
    def get_top_active_trending_topic(self) -> Optional[Dict]:
        """
        Get the single highest volume trending topic from past 24 hours with active status
        
        Returns:
            Single trending topic with highest volume and active status, or None
        """
        try:
            logger.info("Fetching top active trending topic from past 24 hours...")
            
            # Get all trending topics
            trending_topics = self.get_trending_topics()
            
            if not trending_topics:
                logger.warning("No trending topics found")
                return None
            
            # Pre-calculate velocity scores for all topics to prioritize by growth rate
            logger.info("Calculating velocity scores for trending topics...")
            
            for topic in trending_topics:
                # Get preliminary breakdown for velocity calculation
                quick_breakdown = self._quick_velocity_analysis(topic["query"])
                topic["preliminary_velocity"] = self._calculate_velocity_score(topic, quick_breakdown)
                
                volume = self._parse_volume(topic.get("search_volume", "0"))
                velocity = volume / quick_breakdown.get("time_window_hours", 24)
                logger.info(f"  {topic['query'][:50]}: {volume:,} vol, {velocity:,.0f}/h rate, {topic['preliminary_velocity']:.1f} score")
            
            # Sort by velocity score first (prioritizes growth rate), then by volume as tiebreaker
            trending_topics.sort(
                key=lambda x: (x.get("preliminary_velocity", 0), self._parse_volume(x.get("search_volume", "0"))), 
                reverse=True
            )

            # Analyze only top 3 topics for efficiency
            active_topics = []
            
            for i, topic in enumerate(trending_topics[:3]):
                logger.info(f"Analyzing topic {i+1}/3: {topic['query']} (Volume: {topic['search_volume']})")
                
                # Get enhanced breakdown analysis with research context
                breakdown = self._fetch_trend_breakdown(topic["query"])
                
                # Add additional research context to breakdown
                breakdown = self._enhance_breakdown_for_research(topic, breakdown)
                topic["breakdown"] = breakdown
                
                # Calculate velocity-based virality score
                topic["virality_score"] = self._calculate_velocity_score(topic, breakdown)
                
                # Relaxed criteria for "active" - consider stable topics with high news coverage
                direction = breakdown.get("trend_direction", "unknown")
                freshness = breakdown.get("content_freshness", "unknown")
                has_news = breakdown.get("has_news_coverage", False)
                news_count = breakdown.get("news_results_count", 0)
                
                is_active = (
                    direction == "rising" or 
                    freshness in ["very_fresh", "fresh"] or
                    has_news or
                    news_count >= 2 or
                    (direction == "stable" and self._parse_volume(topic.get("search_volume", "0")) >= 5000)  # High volume stable topics
                )
                
                if is_active:
                    topic["status"] = "active"
                    # Add category detection for active topics
                    topic["category"] = self._detect_topic_category(topic["query"])
                    active_topics.append(topic)
                    logger.info(f"✅ Active topic found: {topic['query']} (Volume: {topic['search_volume']}, Direction: {direction}, News: {has_news})")
                else:
                    topic["status"] = "inactive"
                    logger.info(f"❌ Topic not active: {topic['query']} (Direction: {direction}, News: {has_news})")
            
            # If no active topics found in top 3, take the highest volume one anyway
            if not active_topics:
                logger.warning("No active topics found in top 3. Taking highest volume topic as fallback...")
                fallback_topic = trending_topics[0]
                # Add category detection for fallback topic
                fallback_topic["category"] = self._detect_topic_category(fallback_topic["query"])
                breakdown = self._fetch_trend_breakdown(fallback_topic["query"])
                breakdown = self._enhance_breakdown_for_research(fallback_topic, breakdown)
                fallback_topic["breakdown"] = breakdown
                fallback_topic["virality_score"] = self._calculate_velocity_score(fallback_topic, breakdown)
                fallback_topic["status"] = "fallback_highest_volume"
                return fallback_topic
            
            # Return the top active topic (already sorted by velocity score)
            top_topic = active_topics[0]
            logger.info(f"🎯 Selected top active topic: {top_topic['query']} (Velocity Score: {top_topic.get('virality_score', 0):.1f})")
            return top_topic
            
        except Exception as e:
            logger.error(f"Error fetching top active trending topic: {e}")
            return None
    
    def get_daily_trending_topics(self) -> List[Dict]:
        """
        Fetch daily trending topics with detailed breakdown and analysis
        
        Returns:
            List of trending topics with comprehensive metadata
        """
        try:
            # Get basic trending data first 
            logger.info("Fetching basic trending topics...")
            basic_trends = self.get_trending_topics()
            
            if not basic_trends:
                logger.warning("No basic trends found")
                return []
            
            # Enhance with breakdown analysis for top trends
            logger.info("Enhancing trends with breakdown analysis...")
            enhanced_trends = self._enrich_trends_with_breakdown(basic_trends[:5])  # Only analyze top 5 for performance
            
            # Add remaining trends without breakdown
            remaining_trends = basic_trends[5:]
            for trend in remaining_trends:
                trend["breakdown"] = {}
                trend["virality_score"] = 25.0  # Default score for non-analyzed trends
            
            # Combine all trends
            all_trends = enhanced_trends + remaining_trends
            
            # Sort by virality score
            all_trends.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
            
            # Log the top trends with scores
            logger.info("=== TOP TRENDING TOPICS WITH BREAKDOWN ===")
            for i, trend in enumerate(all_trends[:5]):
                score = trend.get("virality_score", 0)
                direction = trend.get("breakdown", {}).get("trend_direction", "unknown")
                logger.info(f"{i+1}. {trend['query']} (Score: {score}, Direction: {direction})")
            
            return all_trends[:config.TRENDING_CONFIG["max_topics"]]
            
        except Exception as e:
            logger.error(f"Error fetching daily trending topics: {e}")
            # Fallback to basic trending
            return self.get_trending_topics()
    
    def _fetch_realtime_trends(self) -> List[Dict]:
        """Fetch realtime trending topics"""
        try:
            params = {
                "engine": "google_trends_trending_now",
                "geo": self.region,
                "api_key": self.api_key,
            }
            
            logger.info(f"Fetching realtime trends for region: {self.region}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            trending_searches = data.get("trending_searches", [])
            
            return self._format_trending_topics(trending_searches, "realtime")
            
        except Exception as e:
            logger.error(f"Error fetching realtime trends: {e}")
            return []
    
    def _fetch_daily_trends(self) -> List[Dict]:
        """Fetch daily trending topics using Google Trends interest over time"""
        try:
            # For daily trends, we'll use a different approach - get trending now and enhance with breakdown
            params = {
                "engine": "google_trends_trending_now", 
                "geo": self.region,
                "api_key": self.api_key,
            }
            
            logger.info(f"Fetching trending data for daily analysis in region: {self.region}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            trending_searches = data.get("trending_searches", [])
            
            return self._format_trending_topics(trending_searches, "daily")
            
        except Exception as e:
            logger.error(f"Error fetching daily trends: {e}")
            return []
    
    def _fetch_trend_breakdown(self, topic_query: str) -> Dict:
        """
        Fetch enhanced breakdown for a trending topic with time-based velocity metrics
        
        Args:
            topic_query: The trending topic to analyze
            
        Returns:
            Dictionary with trend breakdown data including velocity metrics
        """
        try:
            # Get basic metrics from Google search
            params = {
                "engine": "google",
                "q": topic_query,
                "gl": self.region.lower(),
                "api_key": self.api_key,
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Get basic metrics from search results
            search_results = data.get("organic_results", [])
            news_results = data.get("news_results", [])
            related_searches = data.get("related_searches", [])
            
            # Get related questions and people also ask
            people_also_ask = data.get("people_also_ask", [])
            
            # Fetch additional related queries using Google Trends if available
            related_queries = self._fetch_related_queries(topic_query)
            
            # Enhanced velocity-based trend analysis
            direction, velocity_metrics = self._estimate_trend_direction_with_velocity(search_results, news_results)
            
            # Calculate basic breakdown metrics with velocity data
            breakdown = {
                "search_results_count": len(search_results),
                "news_results_count": len(news_results),
                "has_news_coverage": len(news_results) > 0,
                "estimated_results": data.get("search_information", {}).get("total_results", 0),
                "trend_direction": direction,
                "content_freshness": self._analyze_content_freshness(search_results, news_results),
                "peak_popularity": min(len(search_results) * 10, 100),  # Simple estimation
                "stability": 0.5,  # Default middle value
                "related_searches": [item.get("query", "") for item in related_searches[:5]],
                "people_also_ask": [item.get("question", "") for item in people_also_ask[:5]],
                "trend_breakdown": related_queries,  # This is what the user specifically requested
                # Add velocity metrics for enhanced analysis
                **velocity_metrics
            }
            
            logger.info(f"Found {len(breakdown['trend_breakdown'])} related queries for '{topic_query}'")
            
            return breakdown
            
        except Exception as e:
            logger.warning(f"Could not fetch breakdown for '{topic_query}': {e}")
            return {
                "trend_direction": "unknown",
                "peak_popularity": 50,
                "stability": 0.5,
                "search_results_count": 0,
                "news_results_count": 0,
                "related_searches": [],
                "people_also_ask": [],
                "trend_breakdown": [],
            }
    
    def _fetch_related_queries(self, topic_query: str) -> List[str]:
        """
        Fetch related search queries for the trending topic
        
        Args:
            topic_query: The main trending topic
            
        Returns:
            List of related search queries
        """
        try:
            # Try to get related queries using Google autocomplete/suggestions
            autocomplete_params = {
                "engine": "google_autocomplete",
                "q": topic_query,
                "gl": self.region.lower(),
                "api_key": self.api_key,
            }
            
            response = requests.get(self.base_url, params=autocomplete_params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            suggestions = data.get("suggestions", [])
            
            # Extract query strings from suggestions
            related_queries = []
            for suggestion in suggestions[:8]:  # Get top 8 suggestions
                if isinstance(suggestion, dict):
                    query = suggestion.get("value", "")
                elif isinstance(suggestion, str):
                    query = suggestion
                else:
                    continue
                
                if query and query.lower() != topic_query.lower():
                    related_queries.append(query)
            
            # If we don't have enough, try Google Trends related queries
            if len(related_queries) < 3:
                trends_queries = self._fetch_google_trends_related(topic_query)
                related_queries.extend(trends_queries)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_queries = []
            for query in related_queries[:10]:  # Limit to 10
                query_lower = query.lower()
                if query_lower not in seen:
                    seen.add(query_lower)
                    unique_queries.append(query)
            
            logger.info(f"Fetched {len(unique_queries)} related queries for '{topic_query}'")
            return unique_queries
            
        except Exception as e:
            logger.warning(f"Could not fetch related queries for '{topic_query}': {e}")
            # Fallback: generate basic related queries
            return self._generate_fallback_related_queries(topic_query)
    
    def _fetch_google_trends_related(self, topic_query: str) -> List[str]:
        """
        Fetch related queries from Google Trends
        
        Args:
            topic_query: The main trending topic
            
        Returns:
            List of related queries from Google Trends
        """
        try:
            params = {
                "engine": "google_trends",
                "q": topic_query,
                "data_type": "related_queries",
                "geo": self.region,
                "api_key": self.api_key,
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            related_queries = data.get("related_queries", {})
            
            queries = []
            
            # Get rising queries
            rising = related_queries.get("rising", [])
            for item in rising[:5]:
                if isinstance(item, dict):
                    query = item.get("query", "")
                    if query:
                        queries.append(query)
            
            # Get top queries
            top = related_queries.get("top", [])
            for item in top[:5]:
                if isinstance(item, dict):
                    query = item.get("query", "")
                    if query and query not in queries:
                        queries.append(query)
            
            return queries[:8]  # Return top 8
            
        except Exception as e:
            logger.warning(f"Could not fetch Google Trends related queries: {e}")
            return []
    
    def _generate_fallback_related_queries(self, topic_query: str) -> List[str]:
        """
        Generate fallback related queries when API calls fail
        
        Args:
            topic_query: The main trending topic
            
        Returns:
            List of generated related queries
        """
        base_query = topic_query.lower()
        
        # Common search patterns
        patterns = [
            f"{topic_query} news",
            f"{topic_query} today",
            f"{topic_query} latest",
            f"what is {topic_query}",
            f"{topic_query} update",
            f"{topic_query} 2025",
            f"{topic_query} information",
            f"about {topic_query}"
        ]
        
        return patterns[:5]
    
    def _estimate_trend_direction_with_velocity(self, search_results: List[Dict], news_results: List[Dict]) -> tuple:
        """Estimate trend direction and calculate velocity metrics based on search and news results"""
        try:
            # Analyze news recency for velocity calculation
            news_recency_hours = []
            very_recent_count = 0  # Last 3 hours
            recent_count = 0       # Last 12 hours
            
            explosive_keywords = ["breaking", "urgent", "just in", "developing", "live"]
            explosive_mentions = 0
            
            for news in news_results[:10]:
                date_str = news.get("date", "").lower()
                title = news.get("title", "").lower()
                
                # Extract time information and convert to hours
                if "minute" in date_str and "ago" in date_str:
                    # Extract minutes and convert to hours
                    import re
                    match = re.search(r'(\d+)\s*minute', date_str)
                    if match:
                        minutes = int(match.group(1))
                        hours = minutes / 60
                        news_recency_hours.append(hours)
                        if hours <= 3:
                            very_recent_count += 1
                        if hours <= 12:
                            recent_count += 1
                elif "hour" in date_str and "ago" in date_str:
                    import re
                    match = re.search(r'(\d+)\s*hour', date_str)
                    if match:
                        hours = int(match.group(1))
                        news_recency_hours.append(hours)
                        if hours <= 3:
                            very_recent_count += 1
                        if hours <= 12:
                            recent_count += 1
                elif any(word in date_str for word in ["ago", "today"]):
                    news_recency_hours.append(6)  # Assume 6 hours for "today"
                    recent_count += 1
                
                # Check for explosive keywords
                if any(keyword in title for keyword in explosive_keywords):
                    explosive_mentions += 1
            
            # Check search results for trending intensity
            trending_keywords = ["breaking", "latest", "new", "now", "today", "trending"]
            viral_keywords = ["viral", "exploding", "everywhere", "massive", "huge"]
            
            trending_mentions = 0
            viral_mentions = 0
            
            for result in search_results[:8]:
                title = result.get("title", "").lower()
                if any(keyword in title for keyword in trending_keywords):
                    trending_mentions += 1
                if any(keyword in title for keyword in viral_keywords):
                    viral_mentions += 1
            
            # Determine direction with velocity context
            direction = "unknown"
            velocity_indicators = {
                "time_window_hours": 24,  # Default analysis window
                "news_recency_hours": news_recency_hours,
                "very_recent_activity": very_recent_count,
                "recent_activity": recent_count
            }
            
            # Classify trend direction based on velocity signals
            if explosive_mentions >= 2 or very_recent_count >= 3:
                direction = "explosive"  # Very fast growth
                velocity_indicators["time_window_hours"] = 6  # Focus on 6-hour window
            elif recent_count >= 3 or (trending_mentions >= 2 and viral_mentions >= 1):
                direction = "rising"  # Fast growth
                velocity_indicators["time_window_hours"] = 12  # Focus on 12-hour window
            elif recent_count >= 1 or trending_mentions >= 1:
                direction = "stable"  # Steady interest
                velocity_indicators["time_window_hours"] = 24  # Full day analysis
            elif recent_count == 0 and trending_mentions == 0:
                direction = "declining"  # Losing momentum
                velocity_indicators["time_window_hours"] = 48  # Longer analysis window
            else:
                direction = "stable"
            
            return direction, velocity_indicators
            
        except Exception as e:
            logger.warning(f"Error estimating trend direction with velocity: {e}")
            return "unknown", {"time_window_hours": 24, "news_recency_hours": [], "very_recent_activity": 0, "recent_activity": 0}
    
    def _enhance_breakdown_for_research(self, topic: Dict, breakdown: Dict) -> Dict:
        """
        Enhance breakdown data with additional context useful for research
        
        Args:
            topic: Basic topic information 
            breakdown: Initial breakdown data
            
        Returns:
            Enhanced breakdown with research context
        """
        try:
            # Add research context fields
            enhanced_breakdown = breakdown.copy()
            
            # Extract query context clues
            query = topic.get("query", "").lower()
            
            # Detect topic category for better research targeting
            enhanced_breakdown["topic_category"] = self._detect_topic_category(query)
            
            # Suggest research angles based on topic characteristics
            enhanced_breakdown["research_angles"] = self._generate_research_angles(topic, breakdown)
            
            # Add volume context for research priority
            volume = topic.get("search_volume", "0")
            enhanced_breakdown["volume_tier"] = self._categorize_volume(volume)
            
            # Add timing context
            enhanced_breakdown["trend_timing"] = self._analyze_trend_timing(breakdown)
            
            # Suggest key research questions
            enhanced_breakdown["key_questions"] = self._generate_key_questions(query, breakdown)
            
            # Add geographical context if available
            enhanced_breakdown["geo_relevance"] = self._assess_geo_relevance(query)
            
            logger.info(f"Enhanced breakdown for research: {enhanced_breakdown.get('topic_category', 'unknown')} topic")
            
            return enhanced_breakdown
            
        except Exception as e:
            logger.warning(f"Error enhancing breakdown for research: {e}")
            return breakdown
    
    def _detect_topic_category(self, query: str) -> str:
        """Detect the category of the trending topic for targeted research"""
        query_lower = query.lower()
        
        # Celebrity/Entertainment
        if any(indicator in query_lower for indicator in ["actor", "actress", "singer", "celebrity", "star", "movie", "film", "show"]):
            return "entertainment"
        
        # Sports
        elif any(indicator in query_lower for indicator in ["vs", "match", "game", "player", "team", "sport", "cricket", "football", "tennis"]):
            return "sports"
        
        # Politics/Government
        elif any(indicator in query_lower for indicator in ["minister", "president", "politics", "election", "government", "policy"]):
            return "politics"
        
        # Technology/Science
        elif any(indicator in query_lower for indicator in ["ai", "tech", "science", "breakthrough", "discovery", "innovation", "comet", "space"]):
            return "technology"
        
        # Business/Finance
        elif any(indicator in query_lower for indicator in ["company", "stock", "market", "business", "ceo", "finance", "crypto"]):
            return "business"
        
        # News/Events
        elif any(indicator in query_lower for indicator in ["breaking", "news", "event", "announced", "died", "death"]):
            return "news"
        
        else:
            return "general"
    
    def _generate_research_angles(self, topic: Dict, breakdown: Dict) -> list:
        """Generate specific research angles based on topic characteristics"""
        query = topic.get("query", "").lower()
        category = self._detect_topic_category(query)
        direction = breakdown.get("trend_direction", "unknown")
        
        angles = []
        
        if category == "entertainment":
            angles = [
                "Recent projects and announcements",
                "Career milestones and achievements", 
                "Social media activity and fan reactions",
                "Industry news and collaborations"
            ]
        elif category == "sports":
            angles = [
                "Match results and performance",
                "Transfer news and team updates",
                "Player statistics and records",
                "Upcoming fixtures and tournaments"
            ]
        elif category == "politics":
            angles = [
                "Recent policy announcements",
                "Political developments and decisions",
                "Public statements and speeches",
                "Government appointments and changes"
            ]
        elif category == "technology":
            angles = [
                "Technical innovations and breakthroughs",
                "Product launches and updates",
                "Research findings and discoveries",
                "Industry impact and applications"
            ]
        else:
            angles = [
                "Recent news and developments",
                "Public reactions and discussions",
                "Background context and history",
                "Current relevance and significance"
            ]
        
        # Add direction-specific angles
        if direction == "rising":
            angles.append("Why the sudden surge in interest")
        elif direction == "stable":
            angles.append("Sustained public interest factors")
        
        return angles[:5]  # Limit to top 5 angles
    
    def _categorize_volume(self, volume_str: str) -> str:
        """Categorize search volume for research prioritization"""
        try:
            if isinstance(volume_str, str):
                volume_clean = volume_str.replace("+", "").replace(",", "")
                if "M" in volume_clean:
                    return "mega_viral"
                elif "K" in volume_clean:
                    num = float(volume_clean.replace("K", ""))
                    if num >= 50:
                        return "highly_viral"
                    elif num >= 10:
                        return "viral"
                    else:
                        return "trending"
                else:
                    return "emerging"
            return "unknown"
        except:
            return "unknown"
    
    def _analyze_trend_timing(self, breakdown: Dict) -> str:
        """Analyze timing characteristics for research focus"""
        direction = breakdown.get("trend_direction", "unknown")
        freshness = breakdown.get("content_freshness", "unknown")
        
        if direction == "rising" and freshness in ["very_fresh", "fresh"]:
            return "breaking_now"
        elif direction == "rising":
            return "building_momentum" 
        elif freshness == "very_fresh":
            return "fresh_development"
        elif direction == "stable":
            return "sustained_interest"
        else:
            return "general_trending"
    
    def _generate_key_questions(self, query: str, breakdown: Dict) -> list:
        """Generate key research questions for the topic"""
        category = self._detect_topic_category(query)
        timing = self._analyze_trend_timing(breakdown)
        
        base_questions = [
            f"Why is {query} trending right now?",
            f"What recent developments involve {query}?",
            f"What is the significance of {query} today?"
        ]
        
        if timing == "breaking_now":
            base_questions.append(f"What breaking news involves {query}?")
        elif timing == "building_momentum":
            base_questions.append(f"What is driving increasing interest in {query}?")
        
        if category == "entertainment":
            base_questions.append(f"What new projects or news involve {query}?")
        elif category == "sports":
            base_questions.append(f"What matches or sporting events involve {query}?")
        elif category == "politics":
            base_questions.append(f"What political developments involve {query}?")
        
        return base_questions[:5]
    
    def _assess_geo_relevance(self, query: str) -> str:
        """Assess geographical relevance of the topic"""
        query_lower = query.lower()
        
        # Australian context indicators
        if any(indicator in query_lower for indicator in ["australia", "australian", "sydney", "melbourne", "brisbane", "thunder", "heat"]):
            return "australia_focused"
        
        # International indicators  
        elif any(indicator in query_lower for indicator in ["international", "global", "world", "usa", "uk", "europe"]):
            return "international"
        
        # Entertainment often has global relevance
        elif self._detect_topic_category(query) == "entertainment":
            return "global_entertainment"
        
        else:
            return "regional_interest"
    
    def _analyze_content_freshness(self, search_results: List[Dict], news_results: List[Dict]) -> str:
        """Analyze how fresh/recent the content is"""
        try:
            fresh_content = 0
            total_content = len(search_results) + len(news_results)
            
            # Check news freshness
            for news in news_results:
                date_str = news.get("date", "").lower()
                if any(word in date_str for word in ["hour", "hours", "minutes", "ago"]):
                    fresh_content += 2  # News is weighted more
                elif "today" in date_str:
                    fresh_content += 1
            
            # Simple freshness score
            if total_content == 0:
                return "unknown"
            
            freshness_ratio = fresh_content / total_content
            if freshness_ratio > 0.3:
                return "very_fresh"
            elif freshness_ratio > 0.1:
                return "fresh"
            else:
                return "established"
                
        except Exception:
            return "unknown"
    
    def _enrich_trends_with_breakdown(self, trends: List[Dict]) -> List[Dict]:
        """Add detailed breakdown to trending topics"""
        enriched_trends = []
        
        for trend in trends:
            query = trend.get("query", "")
            if query:
                logger.info(f"Analyzing trend: {query}")
                breakdown = self._fetch_trend_breakdown(query)
                trend["breakdown"] = breakdown
                trend["virality_score"] = self._calculate_velocity_score(trend, breakdown)
                logger.info(f"Virality score for '{query}': {trend['virality_score']}")
            else:
                trend["breakdown"] = {}
                trend["virality_score"] = 25.0
            
            enriched_trends.append(trend)
        
        return enriched_trends
    
    def _format_trending_topics(self, trending_searches: List[Dict], frequency_type: str) -> List[Dict]:
        """Format trending topics with standardized structure"""
        topics = []
        
        for idx, item in enumerate(trending_searches[:config.TRENDING_CONFIG["max_topics"]]):
            topic = {
                "rank": idx + 1,
                "query": item.get("query", ""),
                "search_volume": item.get("search_volume", "N/A"),
                "articles": item.get("articles", []),
                "picture": item.get("picture", ""),
                "frequency_type": frequency_type,
                "timestamp": datetime.now().isoformat(),
                "formattedTrafficQuery": item.get("formatted_traffic", ""),
                "exploreLink": item.get("explore_link", ""),
            }
            topics.append(topic)
            logger.info(f"{frequency_type.capitalize()} Topic {idx + 1}: {topic['query']} (Volume: {topic['search_volume']})")
        
        return topics
    
    def _calculate_velocity_score(self, trend: Dict, breakdown: Dict) -> float:
        """
        Calculate trend velocity score based on growth rate over time
        This prioritizes topics gaining momentum quickly over static high-volume topics
        
        Args:
            trend: Basic trend information
            breakdown: Enhanced breakdown with time-based data
            
        Returns:
            Velocity score (0-100) where higher = faster growth rate
        """
        try:
            base_score = 0
            velocity_multiplier = 1.0
            
            # Parse current volume
            current_volume = self._parse_volume(trend.get("search_volume", "0"))
            
            # Get time-based metrics from breakdown
            time_window_hours = breakdown.get("time_window_hours", 24)  # Default 24h window
            news_recency = breakdown.get("news_recency_hours", [])  # Hours ago for news items
            content_age = breakdown.get("content_freshness", "unknown")
            
            # Calculate velocity (volume per hour)
            if time_window_hours > 0:
                velocity = current_volume / time_window_hours
                base_score = min(velocity / 1000, 40)  # Max 40 points from velocity
                
                logger.info(f"Topic '{trend.get('query')}': Volume {current_volume:,} in {time_window_hours}h = {velocity:,.0f}/hour")
            
            # Acceleration bonus - favor topics with very recent activity
            recent_activity_score = 0
            if news_recency:
                # Count news in last 6 hours (high acceleration)
                recent_6h = sum(1 for hours in news_recency if hours <= 6)
                # Count news in 6-12 hours (medium acceleration) 
                recent_12h = sum(1 for hours in news_recency if 6 < hours <= 12)
                
                recent_activity_score = min(recent_6h * 8 + recent_12h * 4, 25)
                velocity_multiplier += recent_6h * 0.2  # 20% boost per recent news
            
            # Freshness velocity boost
            freshness_boost = 0
            if content_age == "very_fresh":  # Content from last few hours
                freshness_boost = 20
                velocity_multiplier *= 1.3
            elif content_age == "fresh":  # Content from last day
                freshness_boost = 12
                velocity_multiplier *= 1.15
            elif content_age == "recent":  # Content from last few days
                freshness_boost = 6
                velocity_multiplier *= 1.05
            
            # Trend direction impact on velocity
            direction = breakdown.get("trend_direction", "")
            direction_boost = 0
            if direction == "rising":
                direction_boost = 15
                velocity_multiplier *= 1.25  # 25% boost for rising trends
            elif direction == "explosive":
                direction_boost = 25  
                velocity_multiplier *= 1.5   # 50% boost for explosive growth
            elif direction == "stable":
                direction_boost = 5
                velocity_multiplier *= 0.9   # Slight penalty for stable (not accelerating)
            
            # Calculate final velocity score
            final_score = (base_score + recent_activity_score + freshness_boost + direction_boost) * velocity_multiplier
            
            return min(round(final_score, 1), 100.0)
            
        except Exception as e:
            logger.warning(f"Error calculating velocity score: {e}")
            return 25.0  # Conservative default
    
    def _quick_velocity_analysis(self, topic_query: str) -> Dict:
        """
        Quick analysis to get velocity metrics without full breakdown
        
        Args:
            topic_query: The trending topic to analyze
            
        Returns:
            Dictionary with basic velocity metrics
        """
        try:
            # Get recent news to estimate velocity
            params = {
                "engine": "google",
                "q": f"{topic_query} news",
                "gl": self.region.lower(),
                "tbm": "nws",  # News search
                "api_key": self.api_key,
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_results = data.get("news_results", [])
            
            # Quick velocity estimation
            recent_hours = 24  # Default window
            very_recent_count = 0
            
            for news in news_results[:5]:
                date_str = news.get("date", "").lower()
                if any(term in date_str for term in ["minute", "hour", "ago"]):
                    very_recent_count += 1
                    if "minute" in date_str or ("hour" in date_str and any(h in date_str for h in ["1", "2", "3"])):
                        recent_hours = min(recent_hours, 6)  # Very recent activity
            
            return {
                "time_window_hours": recent_hours,
                "news_recency_hours": [6] * very_recent_count,  # Simplified
                "very_recent_activity": very_recent_count,
                "recent_activity": len(news_results),
                "content_freshness": "very_fresh" if very_recent_count >= 2 else ("fresh" if very_recent_count >= 1 else "established"),
                "trend_direction": "rising" if very_recent_count >= 2 else ("stable" if very_recent_count >= 1 else "unknown")
            }
            
        except Exception as e:
            logger.warning(f"Quick velocity analysis failed for '{topic_query}': {e}")
            return {
                "time_window_hours": 24,
                "news_recency_hours": [],
                "very_recent_activity": 0,
                "recent_activity": 0,
                "content_freshness": "unknown",
                "trend_direction": "unknown"
            }
    
    def _parse_volume(self, volume_str: str) -> int:
        """
        Parse volume string to numeric value
        
        Args:
            volume_str: Volume string like "500K+" or "1.2M+"
            
        Returns:
            Numeric volume value
        """
        try:
            if isinstance(volume_str, str):
                volume_clean = volume_str.replace("+", "").replace(",", "")
                if "M" in volume_clean:
                    return int(float(volume_clean.replace("M", "")) * 1000000)
                elif "K" in volume_clean:
                    return int(float(volume_clean.replace("K", "")) * 1000)
                elif volume_clean.isdigit():
                    return int(volume_clean)
            return 0
        except:
            return 0
    
    def _calculate_virality_score(self, trend: Dict, breakdown: Dict) -> float:
        """
        DEPRECATED: Use _calculate_velocity_score instead
        Calculate virality score based on velocity and momentum
        
        Args:
            trend: Basic trend information
            breakdown: Enhanced breakdown data
            
        Returns:
            Velocity-based virality score (0-100)
        """
        # Use the new velocity-based scoring
        return self._calculate_velocity_score(trend, breakdown)
    
    def get_trending_topics(self) -> List[Dict]:
        """
        Fetch basic trending topics (fallback method)
        
        Returns:
            List of trending topics with metadata
        """
        try:
            params = {
                "engine": "google_trends_trending_now",
                "geo": self.region,
                "api_key": self.api_key,
            }
            
            logger.info(f"Fetching basic trending topics for region: {self.region}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            trending_searches = data.get("trending_searches", [])
            
            if not trending_searches:
                logger.warning("No trending topics found")
                return []
            
            return self._format_trending_topics(trending_searches, "realtime")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trending topics: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_trending_topics: {e}")
            return []
    
    def get_google_news_trending(self) -> List[Dict]:
        """
        Alternative: Fetch trending topics from Google News
        
        Returns:
            List of trending news topics
        """
        try:
            params = {
                "engine": "google_news",
                "q": "trending",
                "gl": self.region.lower(),
                "hl": self.language,
                "api_key": self.api_key,
            }
            
            logger.info(f"Fetching trending news for region: {self.region}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            news_results = data.get("news_results", [])
            
            if not news_results:
                logger.warning("No news results found")
                return []
            
            topics = []
            for idx, item in enumerate(news_results[:config.TRENDING_CONFIG["max_topics"]]):
                topic = {
                    "rank": idx + 1,
                    "query": item.get("title", ""),
                    "source": item.get("source", {}).get("name", ""),
                    "date": item.get("date", ""),
                    "snippet": item.get("snippet", ""),
                    "thumbnail": item.get("thumbnail", ""),
                }
                topics.append(topic)
                logger.info(f"News {idx + 1}: {topic['query']}")
            
            return topics
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Google News: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_google_news_trending: {e}")
            return []
    
    def filter_topics(self, topics: List[Dict]) -> List[Dict]:
        """
        Filter out blacklisted topics
        
        Args:
            topics: List of topics to filter
            
        Returns:
            Filtered list of topics
        """
        blacklist = config.TOPIC_SELECTION["blacklist_keywords"]
        filtered = []
        
        for topic in topics:
            query = topic.get("query", "").lower()
            if not any(keyword in query for keyword in blacklist):
                filtered.append(topic)
            else:
                logger.info(f"Filtered out blacklisted topic: {topic['query']}")
        
        return filtered
    
    def select_best_topic(self, topics: List[Dict]) -> Optional[Dict]:
        """
        Select the best topic from the list using virality scoring and filtering
        
        Args:
            topics: List of topics to choose from
            
        Returns:
            Best topic or None
        """
        if not topics:
            logger.warning("No topics to select from")
            return None
        
        # Filter blacklisted topics
        filtered_topics = self.filter_topics(topics)
        
        if not filtered_topics:
            logger.warning("All topics were filtered out")
            return None
        
        # Sort by virality score if available
        if any(topic.get("virality_score") for topic in filtered_topics):
            filtered_topics.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
            best_topic = filtered_topics[0]
            
            logger.info(f"Selected topic by virality score: {best_topic['query']} (Score: {best_topic.get('virality_score', 0)})")
        else:
            # Fallback to ranking
            best_topic = filtered_topics[0]
            logger.info(f"Selected topic by rank: {best_topic['query']}")
        
        # Log additional details if available
        breakdown = best_topic.get("breakdown", {})
        if breakdown:
            direction = breakdown.get("trend_direction", "unknown")
            stability = breakdown.get("stability", 0)
            peak = breakdown.get("peak_popularity", 0)
            logger.info(f"Topic details - Direction: {direction}, Stability: {stability}, Peak: {peak}")
        
        return best_topic
    
    def get_trending_breakdown_report(self) -> Dict:
        """
        Generate a comprehensive report of current trending topics with breakdown
        
        Returns:
            Dictionary containing trending analysis report
        """
        try:
            trending_topics = self.get_daily_trending_topics()
            
            if not trending_topics:
                return {"status": "error", "message": "No trending topics found"}
            
            # Generate report
            report = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "region": self.region,
                "total_topics": len(trending_topics),
                "top_topics": [],
                "trend_analysis": {
                    "rising_trends": 0,
                    "falling_trends": 0, 
                    "stable_trends": 0,
                    "average_virality_score": 0,
                    "most_viral_topic": None,
                },
            }
            
            virality_scores = []
            
            for topic in trending_topics:
                breakdown = topic.get("breakdown", {})
                direction = breakdown.get("trend_direction", "unknown")
                
                # Count trend directions
                if direction == "rising":
                    report["trend_analysis"]["rising_trends"] += 1
                elif direction == "falling":
                    report["trend_analysis"]["falling_trends"] += 1
                elif direction == "stable":
                    report["trend_analysis"]["stable_trends"] += 1
                
                # Collect virality scores
                score = topic.get("virality_score", 0)
                if score > 0:
                    virality_scores.append(score)
                
                # Add to top topics (first 5)
                if len(report["top_topics"]) < 5:
                    topic_summary = {
                        "rank": topic.get("rank", 0),
                        "query": topic.get("query", ""),
                        "virality_score": score,
                        "trend_direction": direction,
                        "search_volume": topic.get("search_volume", "N/A"),
                        "stability": breakdown.get("stability", 0),
                        "peak_popularity": breakdown.get("peak_popularity", 0),
                    }
                    report["top_topics"].append(topic_summary)
            
            # Calculate average virality score
            if virality_scores:
                report["trend_analysis"]["average_virality_score"] = round(sum(virality_scores) / len(virality_scores), 1)
                
                # Find most viral topic
                max_score_topic = max(trending_topics, key=lambda x: x.get("virality_score", 0))
                report["trend_analysis"]["most_viral_topic"] = {
                    "query": max_score_topic.get("query", ""),
                    "virality_score": max_score_topic.get("virality_score", 0),
                }
            
            logger.info(f"Generated trending breakdown report: {report['total_topics']} topics analyzed")
            return report
        
        except Exception as e:
            logger.error(f"Error generating trending breakdown report: {e}")
            return {"status": "error", "message": str(e)}

    def _detect_topic_category(self, topic: str) -> str:
        """
        Detect the most likely Google Trends category for a given topic
        
        Args:
            topic: The topic string to categorize
            
        Returns:
            Category ID string (e.g., "17" for Sports)
        """
        topic_lower = topic.lower()
        
        # Sports (17)
        sports_keywords = [
            # Football/Soccer
            'united', 'manchester', 'liverpool', 'arsenal', 'chelsea', 'tottenham', 'newcastle',
            'real madrid', 'barcelona', 'bayern', 'psg', 'juventus', 'milan', 'inter',
            'premier league', 'champions league', 'world cup', 'euro', 'fifa', 'football', 'soccer',
            # American Football
            'nfl', 'chiefs', 'patriots', 'cowboys', 'steelers', 'packers', 'ravens',
            'bills', 'dolphins', 'jets', 'titans', 'jaguars', 'texans', 'browns',
            # Basketball
            'nba', 'lakers', 'warriors', 'celtics', 'heat', 'bulls', 'knicks',
            # Cricket 
            'cricket', 'test', 'odi', 't20', 'ipl', 'kohli', 'sharma', 'dhoni',
            # General sports terms
            'vs', 'match', 'game', 'season', 'playoffs', 'championship', 'tournament',
            'goal', 'score', 'win', 'defeat', 'victory', 'league', 'cup', 'final', 'sport'
        ]
        
        # Technology (18)
        tech_keywords = [
            'iphone', 'android', 'samsung', 'google', 'apple', 'microsoft', 'tesla',
            'phone', 'smartphone', 'tablet', 'laptop', 'computer', 'ai', 'artificial intelligence',
            'chatgpt', 'openai', 'crypto', 'bitcoin', 'blockchain', 'nft', 'metaverse',
            'tech', 'technology', 'software', 'app', 'update', 'release', 'launch'
        ]
        
        # Games (6)
        gaming_keywords = [
            'game', 'gaming', 'play', 'player', 'fortnite', 'minecraft', 'cod', 'call of duty',
            'apex', 'valorant', 'league of legends', 'dota', 'pubg', 'gta', 'cyberpunk',
            'elden ring', 'zelda', 'mario', 'pokemon', 'playstation', 'xbox', 'nintendo',
            'steam', 'epic', 'battle royale', 'mmo', 'fps', 'rpg', 'esports'
        ]
        
        # Entertainment (4)
        entertainment_keywords = [
            'movie', 'film', 'actor', 'actress', 'celebrity', 'hollywood', 'bollywood',
            'netflix', 'disney', 'marvel', 'dc', 'star wars', 'series', 'show', 'tv',
            'music', 'singer', 'artist', 'album', 'song', 'concert', 'tour',
            'award', 'oscar', 'grammy', 'golden globe', 'cannes', 'premiere'
        ]
        
        # Politics (14)
        politics_keywords = [
            'election', 'vote', 'president', 'minister', 'government', 'political',
            'parliament', 'congress', 'senate', 'policy', 'law', 'bill', 'campaign'
        ]
        
        # Health (7)
        health_keywords = [
            'health', 'medical', 'doctor', 'hospital', 'medicine', 'virus', 'covid',
            'vaccine', 'disease', 'treatment', 'therapy', 'fitness', 'diet'
        ]
        
        # Business and Finance (3)
        business_keywords = [
            'stock', 'market', 'business', 'company', 'finance', 'economy', 'investment',
            'bank', 'money', 'price', 'earnings', 'profit', 'revenue', 'ipo'
        ]
        
        # Check each category
        if any(keyword in topic_lower for keyword in sports_keywords):
            return "17"  # Sports
        elif any(keyword in topic_lower for keyword in tech_keywords):
            return "18"  # Technology
        elif any(keyword in topic_lower for keyword in gaming_keywords):
            return "6"   # Games
        elif any(keyword in topic_lower for keyword in entertainment_keywords):
            return "4"   # Entertainment
        elif any(keyword in topic_lower for keyword in politics_keywords):
            return "14"  # Politics
        elif any(keyword in topic_lower for keyword in health_keywords):
            return "7"   # Health
        elif any(keyword in topic_lower for keyword in business_keywords):
            return "3"   # Business and Finance
        else:
            return "11"  # Other (default)
