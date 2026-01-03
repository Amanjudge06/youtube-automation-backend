"""
Main Orchestration Script
Automated YouTube Shorts Video Generation Pipeline

This script orchestrates the entire workflow:
1. Fetch trending topics
2. Generate script
3. Create voiceover
4. Fetch images
5. Assemble video
"""

import logging
import time
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from services.trends_service import TrendsService
from services.research_service import ResearchService
from services.script_generator import ScriptGenerator
from services.voiceover_service import VoiceoverService
from services.image_service import ImageService
from services.simple_video_service import test_ffmpeg_available, SimpleVideoService
from services.youtube_upload_service import YouTubeUploadService
from utils.helpers import (
    setup_logging,
    generate_filename,
    cleanup_temp_files,
    validate_api_keys,
    save_metadata,
    create_summary_report,
    ensure_directories
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def main(language="english", upload_to_youtube=False):
    """Main execution flow"""
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info(f"YouTube Shorts Automation - Starting Pipeline")
    if language != "english":
        logger.info(f"Language: {language.upper()}")
    logger.info("=" * 70)
    
    # Ensure directories exist
    ensure_directories()
    
    # Validate API keys
    if not validate_api_keys():
        logger.error("API keys validation failed. Please configure your API keys in config.py")
        sys.exit(1)
    
    # Check FFmpeg availability
    if not test_ffmpeg_available():
        logger.error("FFmpeg not found. Please install FFmpeg: brew install ffmpeg")
        sys.exit(1)
    
    try:
        # Step 1: Get Single Top Active Trending Topic
        logger.info("\n[STEP 1/6] Fetching top active trending topic from past 24 hours...")
        trends_service = TrendsService()
        
        # Get the single highest volume active topic with breakdown
        selected_topic = trends_service.get_top_active_trending_topic()
        
        if not selected_topic:
            logger.warning("No active trending topic found. Trying fallback methods...")
            
            # Fallback: Try daily trending topics
            trending_topics = trends_service.get_daily_trending_topics()
            if trending_topics:
                selected_topic = trends_service.select_best_topic(trending_topics)
            
            # Final fallback: Try basic trending
            if not selected_topic:
                trending_topics = trends_service.get_trending_topics()
                if trending_topics:
                    selected_topic = trends_service.select_best_topic(trending_topics)
        
        if not selected_topic:
            logger.error("Could not find any trending topic. Exiting.")
            sys.exit(1)
        
        # Display detailed topic information
        topic_query = selected_topic["query"]
        topic_category = selected_topic.get("category", "default")
        category_name = config.TRENDS_CATEGORIES.get(topic_category, "Other")
        breakdown = selected_topic.get("breakdown", {})
        
        logger.info(f"\n🎯 SELECTED TRENDING TOPIC:")
        logger.info(f"   📝 Topic: {topic_query}")
        logger.info(f"   🏷️ Category: {category_name} ({topic_category})")
        logger.info(f"   📊 Search Volume: {selected_topic.get('search_volume', 'N/A')}")
        logger.info(f"   🔥 Virality Score: {selected_topic.get('virality_score', 0)}")
        logger.info(f"   ⚡ Status: {selected_topic.get('status', 'unknown')}")
        logger.info(f"   📈 Trend Direction: {breakdown.get('trend_direction', 'unknown')}")
        logger.info(f"   🆕 Content Freshness: {breakdown.get('content_freshness', 'unknown')}")
        logger.info(f"   📰 News Coverage: {breakdown.get('has_news_coverage', False)}")
        logger.info(f"   🕐 Analysis Time: {selected_topic.get('analysis_timestamp', 'N/A')}")
        
        # Step 2: Research Topic with Perplexity using enhanced breakdown
        logger.info(f"\n[STEP 2/6] Researching why '{topic_query}' is trending...")
        research_service = ResearchService()
        research_data = research_service.research_trending_topic(topic_query, breakdown)
        
        if research_data and not research_data.get("fallback"):
            logger.info("✅ Perplexity research completed:")
            logger.info(f"   📄 Summary length: {research_data.get('content_length', 0)} characters")
            logger.info(f"   🔍 Key points: {len(research_data.get('key_points', []))}")
            logger.info(f"   📰 Sources referenced: {research_data.get('source_count', 0)}")
            if research_data.get("trending_reason"):
                logger.info(f"   🎯 Why trending: {research_data['trending_reason'][:100]}...")
        else:
            logger.warning("⚠️  Using fallback research (Perplexity API unavailable)")
        
        # Step 3: Generate Script with Research Data
        logger.info(f"\n[STEP 3/6] Generating script with research insights...")
        script_generator = ScriptGenerator(language=language)
        script_data = script_generator.generate_script(selected_topic, research_data)
        
        # Initialize YouTube service for SEO generation
        from services.youtube_upload_service import YouTubeUploadService
        youtube_service = YouTubeUploadService()
        
        logger.info(f"✅ Script generated: {script_data['title']}")
        logger.info(f"   Scenes: {len(script_data['scenes'])}")
        logger.info(f"   Script length: {len(script_data['script'])} characters")
        
        # Step 4: Generate Voiceover
        logger.info(f"\n[STEP 4/6] Generating voiceover...")
        voiceover_service = VoiceoverService()
        
        audio_filename = generate_filename(topic_query, "mp3")
        audio_path = config.TEMP_DIR / audio_filename
        
        success = voiceover_service.generate_voiceover(
            script_data["script"],
            audio_path
        )
        
        if not success:
            logger.error("Failed to generate voiceover. Exiting.")
            sys.exit(1)
        
        # Get audio duration
        audio_duration = voiceover_service.get_audio_duration(audio_path)
        logger.info(f"✅ Voiceover generated: {audio_duration:.2f} seconds")
        
        # Generate Subtitles
        logger.info("Generating subtitles...")
        subtitles_path = voiceover_service.generate_subtitles(audio_path)
        
        # Step 4: Fetch Images
        logger.info("\n[STEP 5/6] Fetching images...")
        image_service = ImageService()
        
        image_paths = image_service.fetch_images_for_scenes(
            topic_query,
            script_data,
            research_data=research_data
        )
        
        if not image_paths:
            logger.error("No images fetched. Exiting.")
            sys.exit(1)
        
        logger.info(f"✅ Downloaded {len(image_paths)} images")
        
        # Step 5: Assemble Video with Simple Optimized Service
        logger.info("\n[STEP 6/6] Assembling video with optimized pipeline...")
        
        video_filename = generate_filename(topic_query, "mp4")
        video_path = config.OUTPUT_DIR / video_filename
        
        # Use optimized simple video service
        video_service = SimpleVideoService()
        success = video_service.create_video_with_ffmpeg(
            image_paths=image_paths,
            audio_path=audio_path,
            output_path=video_path,
            audio_duration=audio_duration,
            script_data=script_data,
            subtitles_path=subtitles_path
        )
        
        if success:
            # Generate enhanced SEO metadata using trend breakdown
            logger.info("\n[BONUS STEP] Generating enhanced SEO metadata...")
            enhanced_metadata = {
                'topic': topic_query,
                'trend_breakdown': breakdown.get('related_queries', []),
                'category': category_name,
                'virality_score': selected_topic.get('virality_score', 0),
                'trend_direction': breakdown.get('trend_direction', 'stable')
            }
            
            # Generate SEO tags and description
            seo_tags = youtube_service._generate_seo_tags(enhanced_metadata, research_data)
            seo_description = youtube_service._create_seo_description(enhanced_metadata, research_data)
            
            logger.info(f"✅ Generated {len(seo_tags)} SEO tags using trend data")
            logger.info(f"✅ Generated {len(seo_description)} character description")
            
            # Save enhanced metadata
            enhanced_output_data = {
                'video_path': str(video_path),
                'thumbnail_path': str(video_path).replace('.mp4', '_thumbnail.jpg'),
                'title': script_data['title'],
                'description': script_data['description'],
                'tags': script_data.get('tags', []),
                'seo_tags': seo_tags[:50],  # Limit for display
                'seo_description_length': len(seo_description),
                'seo_description_preview': seo_description[:200] + '...',
                'trend_breakdown_used': len(breakdown.get('related_queries', [])),
                'enhancement_features': ['retention_optimization', 'topic_specific_images', 'enhanced_seo_tags', 'comprehensive_description']
            }
            
            enhanced_filename = generate_filename(topic_query, "json")
            enhanced_output_path = config.OUTPUT_DIR / enhanced_filename
            
            with open(enhanced_output_path, 'w') as f:
                json.dump(enhanced_output_data, f, indent=2)
            
            logger.info(f"✅ Enhanced metadata saved to: {enhanced_output_path}")
        
        if not success:
            logger.error("Failed to create video. Exiting.")
            sys.exit(1)
        
        logger.info(f"✅ Video created: {video_path}")
        
        # Save metadata including trend breakdown for better SEO
        metadata = {
            "topic": topic_query,
            "title": script_data["title"],
            "description": script_data["description"],
            "hashtags": script_data["hashtags"],
            "script": script_data["script"],
            "scenes": script_data["scenes"],
            "duration": audio_duration,
            "images_used": len(image_paths),
            "video_file": str(video_path),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            # Add trend breakdown for better SEO tag generation
            "trend_breakdown": selected_topic.get("breakdown", {}).get("trend_breakdown", []),
            "topic_category": selected_topic.get("category", "general"),
            "trend_direction": selected_topic.get("breakdown", {}).get("trend_direction", "unknown"),
            "virality_score": selected_topic.get("virality_score", 0),
        }
        save_metadata(video_path, metadata)
        
        # Optional: Upload to YouTube
        if upload_to_youtube:
            logger.info("\n[BONUS STEP] Uploading to YouTube...")
            try:
                upload_service = YouTubeUploadService()
                
                # Get research data for SEO optimization
                research_breakdown = {
                    "topic_category": "general",
                    "trend_timing": "upload_optimization", 
                    "volume_tier": "high"
                }
                enhanced_research = research_service.research_trending_topic(topic_query, research_breakdown)
                
                # Upload with SEO optimization
                upload_result = upload_service.upload_video(
                    video_path, 
                    video_path.with_suffix('.json'),
                    enhanced_research
                )
                
                if upload_result.get('success'):
                    video_url = upload_result['video_url']
                    logger.info(f"✅ Video uploaded to YouTube: {video_url}")
                    
                    # Add upload info to summary
                    metadata['youtube_upload'] = {
                        'success': True,
                        'video_url': video_url,
                        'video_id': upload_result['video_id'],
                        'upload_time': upload_result['metadata']['upload_timestamp']
                    }
                    
                    print(f"\n🎉 SUCCESS! Video is live on YouTube!")
                    print(f"🔗 Watch here: {video_url}")
                    
                else:
                    error = upload_result.get('error', 'Unknown error')
                    logger.warning(f"⚠️  YouTube upload failed: {error}")
                    print(f"\n⚠️  YouTube upload failed: {error}")
                    
                    if "credentials" in error.lower() or "authentication" in error.lower():
                        print("\n💡 TIP: Run 'python upload_video.py --test-auth' to set up YouTube credentials")
                    
                    metadata['youtube_upload'] = {
                        'success': False,
                        'error': error
                    }
                
                # Update metadata with upload info
                save_metadata(video_path, metadata)
                    
            except Exception as e:
                logger.error(f"YouTube upload error: {e}")
                print(f"\n❌ YouTube upload error: {e}")
                metadata['youtube_upload'] = {
                    'success': False,
                    'error': str(e)
                }
                save_metadata(video_path, metadata)
        
        # Cleanup temp files
        logger.info("\nCleaning up temporary files...")
        cleanup_temp_files()
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Print summary
        summary = create_summary_report(
            topic_query,
            video_path,
            audio_duration,
            processing_time
        )
        print(summary)
        logger.info("Pipeline completed successfully!")
        
        return video_path
        
    except KeyboardInterrupt:
        logger.info("\nPipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in pipeline: {e}", exc_info=True)
        sys.exit(1)


def show_top_active_topic():
    """
    Display the single top active trending topic with full breakdown
    """
    logger.info("=" * 70)
    logger.info("TOP ACTIVE TRENDING TOPIC (PAST 24 HOURS)")
    logger.info("=" * 70)
    
    try:
        trends_service = TrendsService()
        
        # Get the top active topic
        logger.info("Analyzing trending topics for highest volume active topic...")
        top_topic = trends_service.get_top_active_trending_topic()
        
        if not top_topic:
            logger.error("❌ No active trending topics found")
            print("\n❌ No active trending topics found in the past 24 hours")
            return
        
        # Display comprehensive topic information
        breakdown = top_topic.get("breakdown", {})
        
        print("\n" + "🎯" + "=" * 50)
        print("🏆 TOP ACTIVE TRENDING TOPIC")
        print("=" * 52)
        
        print(f"\n📝 Topic: {top_topic.get('query', 'Unknown')}")
        print(f"📊 Search Volume: {top_topic.get('search_volume', 'N/A')}")
        print(f"🔥 Virality Score: {top_topic.get('virality_score', 0)}/100")
        print(f"⚡ Status: {top_topic.get('status', 'unknown').title()}")
        print(f"🕐 Analysis Time: {top_topic.get('analysis_timestamp', 'N/A')}")
        print(f"⏰ Time Period: {top_topic.get('time_period', 'N/A')}")
        
        print(f"\n📈 TREND ANALYSIS:")
        print(f"   Direction: {breakdown.get('trend_direction', 'unknown').title()}")
        print(f"   Content Freshness: {breakdown.get('content_freshness', 'unknown').title()}")
        print(f"   Peak Popularity: {breakdown.get('peak_popularity', 0)}")
        print(f"   Stability Score: {breakdown.get('stability', 0)}")
        
        print(f"\n📰 CONTENT COVERAGE:")
        print(f"   Has News Coverage: {'Yes' if breakdown.get('has_news_coverage') else 'No'}")
        print(f"   News Results Count: {breakdown.get('news_results_count', 0)}")
        print(f"   Search Results Count: {breakdown.get('search_results_count', 0)}")
        
        if breakdown.get("estimated_results"):
            print(f"   Estimated Total Results: {breakdown.get('estimated_results', 0):,}")
        
        # Show trend breakdown (related queries)
        trend_breakdown = breakdown.get("trend_breakdown", [])
        if trend_breakdown:
            print(f"\n🔍 RELATED SEARCH QUERIES:")
            for i, query in enumerate(trend_breakdown[:5]):
                print(f"   {i+1}. {query}")
        
        # Show related searches
        related_searches = breakdown.get("related_searches", [])
        if related_searches:
            print(f"\n🔎 ADDITIONAL RELATED SEARCHES:")
            for i, search in enumerate(related_searches[:3]):
                print(f"   {i+1}. {search}")
        
        # Show articles if available
        articles = top_topic.get("articles", [])
        if articles:
            print(f"\n📰 RELATED ARTICLES ({len(articles)} found):")
            for i, article in enumerate(articles[:3]):  # Show top 3
                title = article.get("title", "No title")
                source = article.get("source", "Unknown source")
                print(f"   {i+1}. {title} - {source}")
        
        print("\n" + "=" * 52)
        logger.info(f"✅ Displayed top active topic: {top_topic.get('query')}")
        
    except Exception as e:
        logger.error(f"❌ Error showing top active topic: {e}")
        print(f"\n❌ Error: {e}")


def generate_trending_report():
    """
    Generate and display comprehensive trending topics breakdown report
    """
    logger.info("=" * 70)
    logger.info("DAILY TRENDING TOPICS BREAKDOWN REPORT")
    logger.info("=" * 70)
    
    try:
        trends_service = TrendsService()
        
        # Get daily trending topics with breakdown
        logger.info("Analyzing trending topics...")
        trending_topics = trends_service.get_daily_trending_topics()
        
        if not trending_topics:
            logger.error("❌ Could not fetch trending topics")
            return
        
        # Generate comprehensive report
        report = trends_service.get_trending_breakdown_report()
        
        if report.get("status") != "success":
            logger.error(f"❌ Report generation failed: {report.get('message', 'Unknown error')}")
            return
        
        # Display report
        print("\n" + "=" * 50)
        print("📊 TRENDING TOPICS ANALYSIS SUMMARY")
        print("=" * 50)
        
        analysis = report.get("trend_analysis", {})
        print(f"🕐 Analysis Time: {report.get('timestamp', 'Unknown')}")
        print(f"🌍 Region: {report.get('region', 'Unknown')}")
        print(f"📈 Total Topics: {report.get('total_topics', 0)}")
        print(f"⬆️  Rising Trends: {analysis.get('rising_trends', 0)}")
        print(f"⬇️  Falling Trends: {analysis.get('falling_trends', 0)}")
        print(f"➡️  Stable Trends: {analysis.get('stable_trends', 0)}")
        print(f"🔥 Avg Virality Score: {analysis.get('average_virality_score', 0)}")
        
        most_viral = analysis.get("most_viral_topic")
        if most_viral:
            print(f"🚀 Most Viral: '{most_viral.get('query', 'N/A')}' (Score: {most_viral.get('virality_score', 0)})")
        
        # Display top topics
        top_topics = report.get("top_topics", [])
        if top_topics:
            print("\n" + "=" * 50)
            print("🏆 TOP TRENDING TOPICS")
            print("=" * 50)
            
            for topic in top_topics:
                print(f"\n#{topic.get('rank', 0)}: {topic.get('query', 'Unknown')}")
                print(f"   🔥 Virality Score: {topic.get('virality_score', 0)}")
                print(f"   📊 Search Volume: {topic.get('search_volume', 'N/A')}")
                print(f"   📈 Trend Direction: {topic.get('trend_direction', 'unknown').title()}")
                print(f"   💯 Peak Popularity: {topic.get('peak_popularity', 0)}")
                print(f"   ⚖️  Stability: {topic.get('stability', 0)}")
        
        print("\n" + "=" * 50)
        logger.info("✅ Trending report generated successfully")
        
    except Exception as e:
        logger.error(f"❌ Error generating trending report: {e}")


def run_with_custom_topic(topic: str, language="english", upload_to_youtube=False):
    """
    Run pipeline with a custom topic instead of trending topics
    
    Args:
        topic: Custom topic string
        language: Script language (english or hinglish)
    """
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info(f"YouTube Shorts Automation - Custom Topic: {topic}")
    if language != "english":
        logger.info(f"Language: {language.upper()}")
    logger.info("=" * 70)
    
    ensure_directories()
    
    if not validate_api_keys():
        logger.error("API keys validation failed")
        sys.exit(1)
    
    if not test_ffmpeg_available():
        logger.error("FFmpeg not found. Please install FFmpeg: brew install ffmpeg")
        sys.exit(1)
    
    try:
        # Create topic dict
        custom_topic = {
            "rank": 1,
            "query": topic,
            "search_volume": "N/A",
            "articles": [],
        }
        
        # Step 1: Research Custom Topic
        logger.info(f"\n[STEP 1/5] Researching custom topic '{topic}'...")
        research_service = ResearchService()
        # For custom topics, create basic breakdown context
        custom_breakdown = {
            "topic_category": "general",
            "trend_timing": "custom_request",
            "volume_tier": "custom",
            "research_angles": [
                "Current developments and news",
                "Background context and significance", 
                "Recent updates and changes"
            ],
            "key_questions": [
                f"What is {topic} about?",
                f"What recent developments involve {topic}?",
                f"Why is {topic} significant or relevant now?"
            ],
            "geo_relevance": "general"
        }
        research_data = research_service.research_trending_topic(topic, custom_breakdown)
        
        if research_data and not research_data.get("fallback"):
            logger.info("✅ Research completed:")
            logger.info(f"   📄 Content: {research_data.get('content_length', 0)} characters")
            logger.info(f"   🔍 Key points: {len(research_data.get('key_points', []))}")
        else:
            logger.info("⚠️  Using basic topic information")
        
        # Step 2: Generate Script with Research
        logger.info(f"\n[STEP 2/5] Generating script with research...")
        script_generator = ScriptGenerator(language=language)
        script_data = script_generator.generate_script(custom_topic, research_data)
        logger.info(f"✅ Script generated: {script_data['title']}")
        
        # Step 3: Generate Voiceover
        logger.info(f"\n[STEP 3/5] Generating voiceover...")
        voiceover_service = VoiceoverService()
        audio_path = config.TEMP_DIR / generate_filename(topic, "mp3")
        
        success = voiceover_service.generate_voiceover(script_data["script"], audio_path)
        if not success:
            logger.error("Failed to generate voiceover")
            sys.exit(1)
        
        audio_duration = voiceover_service.get_audio_duration(audio_path)
        logger.info(f"✅ Voiceover generated: {audio_duration:.2f} seconds")
        
        # Step 4: Fetch Images
        logger.info(f"\n[STEP 4/5] Fetching images...")
        image_service = ImageService()
        image_paths = image_service.fetch_images_for_scenes(script_data["scenes"], topic, research_data=research_data, script_data=script_data)
        
        if not image_paths:
            logger.error("No images fetched")
            sys.exit(1)
        
        logger.info(f"✅ Downloaded {len(image_paths)} images")
        
        # Step 5: Assemble Video
        logger.info(f"\n[STEP 5/5] Assembling video...")
        video_service = SimpleVideoService()
        video_path = config.OUTPUT_DIR / generate_filename(topic, "mp4")
        
        success = video_service.create_video_with_ffmpeg(image_paths, audio_path, video_path, audio_duration, script_data)
        if not success:
            logger.error("Failed to create video")
            sys.exit(1)
        
        logger.info(f"✅ Video created: {video_path}")
        
        # Save metadata
        metadata = {
            "topic": topic,
            "title": script_data["title"],
            "description": script_data["description"],
            "hashtags": script_data["hashtags"],
            "script": script_data["script"],
            "duration": audio_duration,
            "video_file": str(video_path),
        }
        save_metadata(video_path, metadata)
        
        # Optional: Upload to YouTube
        if upload_to_youtube:
            logger.info("\n[BONUS STEP] Uploading to YouTube...")
            try:
                upload_service = YouTubeUploadService()
                upload_result = upload_service.upload_video(
                    video_path, 
                    video_path.with_suffix('.json'),
                    research_data
                )
                
                if upload_result.get('success'):
                    video_url = upload_result['video_url']
                    logger.info(f"✅ Video uploaded to YouTube: {video_url}")
                    print(f"\n🎉 SUCCESS! Video is live on YouTube!")
                    print(f"🔗 Watch here: {video_url}")
                    
                    metadata['youtube_upload'] = {
                        'success': True,
                        'video_url': video_url,
                        'video_id': upload_result['video_id'],
                        'upload_time': upload_result['metadata']['upload_timestamp']
                    }
                    save_metadata(video_path, metadata)
                    
                else:
                    error = upload_result.get('error', 'Unknown error')
                    logger.warning(f"⚠️  YouTube upload failed: {error}")
                    print(f"\n⚠️  YouTube upload failed: {error}")
                    
            except Exception as e:
                logger.error(f"YouTube upload error: {e}")
                print(f"\n❌ YouTube upload error: {e}")
        
        cleanup_temp_files()
        
        processing_time = time.time() - start_time
        summary = create_summary_report(topic, video_path, audio_duration, processing_time)
        print(summary)
        
        return video_path
        
    except Exception as e:
        logger.error(f"Error in custom topic pipeline: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automated YouTube Shorts Video Generator"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Custom topic (if not provided, will use trending topics)"
    )
    parser.add_argument(
        "--language",
        type=str,
        choices=["english", "hinglish"],
        default="english", 
        help="Script language: english or hinglish (Hindi+English mix)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode (validates API keys only)"
    )
    parser.add_argument(
        "--trending-report",
        action="store_true",
        help="Generate daily trending breakdown report only (no video creation)"
    )
    parser.add_argument(
        "--top-topic",
        action="store_true",
        help="Show only the single top active trending topic with breakdown (no video creation)"
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Automatically upload the generated video to YouTube"
    )
    
    args = parser.parse_args()
    
    if args.test:
        print("Testing API configuration...")
        setup_logging()
        if validate_api_keys():
            print("✅ All API keys are configured correctly")
        else:
            print("❌ API keys validation failed")
        sys.exit(0)
    
    if args.trending_report:
        setup_logging()
        generate_trending_report()
        sys.exit(0)
    
    if args.top_topic:
        setup_logging()
        show_top_active_topic()
        sys.exit(0)
    
    if args.topic:
        run_with_custom_topic(args.topic, args.language, args.upload)
    else:
        main(args.language, args.upload)
