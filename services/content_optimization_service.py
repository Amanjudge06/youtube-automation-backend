"""
Content Optimization Service
Analyzes performance data and automatically adjusts content generation parameters
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import statistics
import config
from services.youtube_analytics_service import YouTubeAnalyticsService

logger = logging.getLogger(__name__)

class ContentOptimizationService:
    """Optimize content generation based on YouTube performance analytics"""
    
    def __init__(self):
        self.analytics_service = YouTubeAnalyticsService()
        self.optimization_history = []
        self.current_optimization_profile = self._load_optimization_profile()
    
    def _load_optimization_profile(self) -> Dict:
        """Load current optimization profile or create default"""
        try:
            with open("logs/optimization_profile.json", "r") as f:
                profile = json.load(f)
                logger.info("Loaded existing optimization profile")
                return profile
        except FileNotFoundError:
            logger.info("Creating new optimization profile")
            return self._create_default_profile()
        except Exception as e:
            logger.error(f"Error loading optimization profile: {e}")
            return self._create_default_profile()
    
    def _create_default_profile(self) -> Dict:
        """Create default optimization profile"""
        return {
            "script_optimization": {
                "hook_style": "question_based",  # question_based, shocking, curiosity
                "engagement_triggers": ["What do you think?", "Let me know below"],
                "tone_intensity": 0.7,  # 0.1 = calm, 1.0 = very energetic
                "controversy_level": 0.3,  # 0.1 = safe, 1.0 = controversial
                "call_to_action_frequency": "medium",  # low, medium, high
                "optimal_word_count": 120,
                "trending_keyword_weight": 0.8  # How much to prioritize trending keywords
            },
            "voiceover_optimization": {
                "speaking_rate": 1.0,  # 0.5 = slow, 1.5 = fast
                "energy_level": 0.7,  # 0.1 = monotone, 1.0 = very energetic
                "pause_frequency": 0.5,  # 0.1 = minimal pauses, 1.0 = many pauses
                "emotion_intensity": 0.6,  # 0.1 = neutral, 1.0 = very emotional
                "voice_variety": 0.7,  # 0.1 = consistent, 1.0 = varied intonation
                "optimal_duration": 60  # Target duration in seconds
            },
            "content_strategy": {
                "trend_velocity_weight": 0.9,  # Prioritize fast-growing trends
                "niche_focus": [],  # Specific content niches that perform well
                "optimal_posting_time": "auto",  # Will be determined by analytics
                "content_freshness_requirement": 6,  # Hours - how fresh content should be
                "controversy_tolerance": 0.4  # How much controversial content to include
            },
            "performance_targets": {
                "min_engagement_rate": 2.0,  # Minimum target engagement rate
                "target_view_count": 10000,  # Target views per video
                "target_watch_time": 45,  # Target watch time in seconds
                "growth_rate_target": 0.15  # 15% improvement per optimization cycle
            },
            "last_updated": datetime.now().isoformat(),
            "optimization_version": "1.0"
        }
    
    def analyze_and_optimize(self, channel_id: str = None) -> Dict:
        """
        Perform comprehensive analysis and optimization
        
        Args:
            channel_id: YouTube channel ID to analyze
            
        Returns:
            Dictionary with optimization results and new parameters
        """
        try:
            logger.info("Starting comprehensive content optimization analysis...")
            
            # Set channel for analysis
            if channel_id:
                self.analytics_service.set_channel_id(channel_id)
            
            # Get performance data
            performance_data = self.analytics_service.get_channel_performance(days=30)
            
            if not performance_data or performance_data.get("total_videos", 0) == 0:
                logger.warning("No performance data available for optimization")
                return {"status": "no_data", "message": "Insufficient data for optimization"}
            
            # Analyze current performance vs targets
            current_performance = self._analyze_current_performance(performance_data)
            
            # Generate optimizations
            optimizations = self._generate_optimizations(performance_data, current_performance)
            
            # Update optimization profile
            self._update_optimization_profile(optimizations)
            
            # Save optimization results
            optimization_result = {
                "timestamp": datetime.now().isoformat(),
                "channel_analysis": performance_data,
                "current_performance": current_performance,
                "optimizations": optimizations,
                "new_profile": self.current_optimization_profile
            }
            
            self._save_optimization_results(optimization_result)
            
            logger.info("Content optimization analysis completed successfully")
            return {
                "status": "success",
                "optimizations": optimizations,
                "performance_summary": current_performance,
                "recommendations_count": len(optimizations.get("script_changes", [])) + len(optimizations.get("voiceover_changes", []))
            }
            
        except Exception as e:
            logger.error(f"Error in content optimization: {e}")
            return {"status": "error", "message": str(e)}
    
    def _analyze_current_performance(self, performance_data: Dict) -> Dict:
        """Analyze current performance against targets"""
        try:
            overall_metrics = performance_data.get("overall_metrics", {})
            targets = self.current_optimization_profile.get("performance_targets", {})
            
            current_performance = {
                "engagement_rate": overall_metrics.get("average_engagement_rate", 0),
                "average_views": overall_metrics.get("average_views", 0),
                "total_videos": performance_data.get("total_videos", 0),
                "performance_vs_targets": {}
            }
            
            # Compare against targets
            engagement_target = targets.get("min_engagement_rate", 2.0)
            view_target = targets.get("target_view_count", 10000)
            
            current_performance["performance_vs_targets"] = {
                "engagement_rate_ratio": current_performance["engagement_rate"] / engagement_target,
                "view_count_ratio": current_performance["average_views"] / view_target,
                "overall_performance_score": self._calculate_overall_score(current_performance, targets)
            }
            
            return current_performance
            
        except Exception as e:
            logger.error(f"Error analyzing current performance: {e}")
            return {}
    
    def _calculate_overall_score(self, current: Dict, targets: Dict) -> float:
        """Calculate overall performance score (0-1)"""
        try:
            engagement_ratio = min(current["engagement_rate"] / targets.get("min_engagement_rate", 2.0), 1.0)
            view_ratio = min(current["average_views"] / targets.get("target_view_count", 10000), 1.0)
            
            # Weighted average (engagement more important than raw views)
            overall_score = (engagement_ratio * 0.7) + (view_ratio * 0.3)
            
            return round(overall_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    def _generate_optimizations(self, performance_data: Dict, current_performance: Dict) -> Dict:
        """Generate specific optimizations based on performance analysis"""
        try:
            optimizations = {
                "script_changes": [],
                "voiceover_changes": [],
                "content_strategy_changes": [],
                "optimization_reasoning": []
            }
            
            overall_score = current_performance.get("performance_vs_targets", {}).get("overall_performance_score", 0)
            engagement_rate = current_performance.get("engagement_rate", 0)
            
            # Script optimizations
            if engagement_rate < 1.5:
                optimizations["script_changes"].append({
                    "parameter": "hook_style",
                    "current_value": self.current_optimization_profile["script_optimization"]["hook_style"],
                    "new_value": "shocking",
                    "reason": "Low engagement - switching to more attention-grabbing hooks",
                    "impact_estimate": "+25% engagement"
                })
                
                optimizations["script_changes"].append({
                    "parameter": "call_to_action_frequency",
                    "current_value": self.current_optimization_profile["script_optimization"]["call_to_action_frequency"],
                    "new_value": "high",
                    "reason": "Low engagement - increasing CTAs to boost interaction",
                    "impact_estimate": "+15% engagement"
                })
            
            elif engagement_rate < 2.5:
                optimizations["script_changes"].append({
                    "parameter": "controversy_level",
                    "current_value": self.current_optimization_profile["script_optimization"]["controversy_level"],
                    "new_value": min(0.7, self.current_optimization_profile["script_optimization"]["controversy_level"] + 0.2),
                    "reason": "Moderate engagement - adding more opinion-based content",
                    "impact_estimate": "+10% engagement"
                })
            
            # Analyze top-performing videos for patterns
            top_videos = [v for v in performance_data.get("videos", []) if v.get("performance_score", 0) > 60]
            
            if top_videos:
                # Optimal duration analysis
                top_durations = [v.get("duration", 60) for v in top_videos if "duration" in v]
                if top_durations:
                    optimal_duration = round(statistics.mean(top_durations))
                    current_target = self.current_optimization_profile["voiceover_optimization"]["optimal_duration"]
                    
                    if abs(optimal_duration - current_target) > 10:
                        optimizations["voiceover_changes"].append({
                            "parameter": "optimal_duration",
                            "current_value": current_target,
                            "new_value": optimal_duration,
                            "reason": f"Top videos average {optimal_duration}s - adjusting target duration",
                            "impact_estimate": "+20% retention"
                        })
            
            # Content strategy optimizations
            content_insights = performance_data.get("content_insights", {})
            title_patterns = content_insights.get("title_patterns", {})
            
            if title_patterns.get("effective_keywords"):
                top_keywords = [kw[0] for kw in title_patterns["effective_keywords"][:5]]
                optimizations["content_strategy_changes"].append({
                    "parameter": "niche_focus",
                    "current_value": self.current_optimization_profile["content_strategy"]["niche_focus"],
                    "new_value": top_keywords,
                    "reason": "Identified high-performing keyword patterns",
                    "impact_estimate": "+30% discoverability"
                })
            
            # Performance-based voiceover adjustments
            if overall_score < 0.5:
                optimizations["voiceover_changes"].append({
                    "parameter": "energy_level",
                    "current_value": self.current_optimization_profile["voiceover_optimization"]["energy_level"],
                    "new_value": min(0.9, self.current_optimization_profile["voiceover_optimization"]["energy_level"] + 0.2),
                    "reason": "Low overall performance - increasing energy to boost retention",
                    "impact_estimate": "+15% retention"
                })
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error generating optimizations: {e}")
            return {}
    
    def _update_optimization_profile(self, optimizations: Dict):
        """Update the current optimization profile with new parameters"""
        try:
            # Apply script changes
            for change in optimizations.get("script_changes", []):
                param = change["parameter"]
                new_value = change["new_value"]
                
                if param in self.current_optimization_profile["script_optimization"]:
                    self.current_optimization_profile["script_optimization"][param] = new_value
                    logger.info(f"Updated script parameter {param} to {new_value}")
            
            # Apply voiceover changes
            for change in optimizations.get("voiceover_changes", []):
                param = change["parameter"]
                new_value = change["new_value"]
                
                if param in self.current_optimization_profile["voiceover_optimization"]:
                    self.current_optimization_profile["voiceover_optimization"][param] = new_value
                    logger.info(f"Updated voiceover parameter {param} to {new_value}")
            
            # Apply content strategy changes
            for change in optimizations.get("content_strategy_changes", []):
                param = change["parameter"]
                new_value = change["new_value"]
                
                if param in self.current_optimization_profile["content_strategy"]:
                    self.current_optimization_profile["content_strategy"][param] = new_value
                    logger.info(f"Updated content strategy parameter {param} to {new_value}")
            
            # Update metadata
            self.current_optimization_profile["last_updated"] = datetime.now().isoformat()
            
            # Save updated profile
            self._save_optimization_profile()
            
        except Exception as e:
            logger.error(f"Error updating optimization profile: {e}")
    
    def _save_optimization_profile(self):
        """Save the current optimization profile"""
        try:
            with open("logs/optimization_profile.json", "w") as f:
                json.dump(self.current_optimization_profile, f, indent=2, default=str)
            logger.info("Optimization profile saved successfully")
        except Exception as e:
            logger.error(f"Error saving optimization profile: {e}")
    
    def _save_optimization_results(self, results: Dict):
        """Save optimization analysis results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"logs/optimization_analysis_{timestamp}.json"
            
            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Optimization results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving optimization results: {e}")
    
    def _save_optimization_profile(self, profile: Dict):
        """Save optimization profile to disk"""
        try:
            import os
            os.makedirs("logs", exist_ok=True)
            
            profile["last_updated"] = datetime.now().isoformat()
            
            with open("logs/optimization_profile.json", "w") as f:
                json.dump(profile, f, indent=2)
            
            # Update current profile in memory
            self.current_optimization_profile = profile
            logger.info("Optimization profile saved successfully")
        except Exception as e:
            logger.error(f"Error saving optimization profile: {e}")
            raise
    
    def get_optimized_script_config(self) -> Dict:
        """Get optimized configuration for script generation"""
        try:
            script_config = self.current_optimization_profile["script_optimization"].copy()
            
            # Convert optimization profile to script generation parameters
            optimized_config = {
                "temperature": 0.5 + (script_config["tone_intensity"] * 0.4),  # 0.5-0.9 range
                "max_tokens": int(script_config["optimal_word_count"] * 4),  # ~4 tokens per word
                "tone": self._get_tone_description(script_config),
                "hook_style": script_config["hook_style"],
                "engagement_elements": script_config["engagement_triggers"],
                "controversy_level": script_config["controversy_level"],
                "trending_weight": script_config["trending_keyword_weight"]
            }
            
            logger.info("Generated optimized script configuration")
            return optimized_config
            
        except Exception as e:
            logger.error(f"Error generating optimized script config: {e}")
            return config.SCRIPT_CONFIG  # Fallback to default
    
    def get_optimized_voiceover_config(self) -> Dict:
        """Get optimized configuration for voiceover generation"""
        try:
            voiceover_config = self.current_optimization_profile["voiceover_optimization"].copy()
            
            # Convert to voiceover parameters
            optimized_config = {
                "voice_speed": voiceover_config["speaking_rate"],
                "energy_level": voiceover_config["energy_level"],
                "target_duration": voiceover_config["optimal_duration"],
                "emotion_intensity": voiceover_config["emotion_intensity"],
                "pause_frequency": voiceover_config["pause_frequency"],
                "voice_variety": voiceover_config["voice_variety"]
            }
            
            logger.info("Generated optimized voiceover configuration")
            return optimized_config
            
        except Exception as e:
            logger.error(f"Error generating optimized voiceover config: {e}")
            return config.VOICEOVER_CONFIG  # Fallback to default
    
    def _get_tone_description(self, script_config: Dict) -> str:
        """Convert optimization parameters to tone description"""
        intensity = script_config["tone_intensity"]
        controversy = script_config["controversy_level"]
        
        if intensity > 0.8:
            base_tone = "very energetic and exciting"
        elif intensity > 0.6:
            base_tone = "energetic and engaging"
        elif intensity > 0.4:
            base_tone = "upbeat and informative"
        else:
            base_tone = "calm and professional"
        
        if controversy > 0.6:
            base_tone += ", with thought-provoking opinions"
        elif controversy > 0.3:
            base_tone += ", with subtle debate points"
        
        return base_tone
    
    def get_optimization_summary(self) -> Dict:
        """Get a summary of current optimizations"""
        try:
            return {
                "status": "active",
                "last_updated": self.current_optimization_profile.get("last_updated"),
                "script_optimizations": {
                    "hook_style": self.current_optimization_profile["script_optimization"]["hook_style"],
                    "tone_intensity": self.current_optimization_profile["script_optimization"]["tone_intensity"],
                    "controversy_level": self.current_optimization_profile["script_optimization"]["controversy_level"]
                },
                "voiceover_optimizations": {
                    "energy_level": self.current_optimization_profile["voiceover_optimization"]["energy_level"],
                    "speaking_rate": self.current_optimization_profile["voiceover_optimization"]["speaking_rate"],
                    "optimal_duration": self.current_optimization_profile["voiceover_optimization"]["optimal_duration"]
                },
                "performance_targets": self.current_optimization_profile["performance_targets"],
                "optimization_history_count": len(self.optimization_history)
            }
        except Exception as e:
            logger.error(f"Error generating optimization summary: {e}")
            return {"status": "error", "message": str(e)}