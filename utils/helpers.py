"""
Utility Helper Functions
Common utilities for the YouTube automation system
"""

import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
import config


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, config.LOGGING_CONFIG["level"]),
        format=config.LOGGING_CONFIG["format"],
        handlers=[
            logging.FileHandler(config.LOGGING_CONFIG["file"]),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")


def generate_filename(topic: str, extension: str = "mp4") -> str:
    """
    Generate a unique filename for output
    
    Args:
        topic: Video topic
        extension: File extension
        
    Returns:
        Filename string
    """
    # Clean topic for filename
    clean_topic = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)
    clean_topic = clean_topic.replace(" ", "_")[:50]  # Limit length
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{clean_topic}_{timestamp}.{extension}"


def cleanup_temp_files():
    """Remove temporary files and directories"""
    logger = logging.getLogger(__name__)
    
    try:
        if config.TEMP_DIR.exists():
            shutil.rmtree(config.TEMP_DIR)
            config.TEMP_DIR.mkdir(exist_ok=True)
            logger.info("Temporary files cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")


def validate_api_keys() -> bool:
    """
    Validate that all required API keys are configured
    
    Returns:
        True if all keys are valid, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    required_keys = {
        "SERP_API_KEY": config.SERP_API_KEY,
        "OPENAI_API_KEY": config.OPENAI_API_KEY,
        "ELEVENLABS_API_KEY": config.ELEVENLABS_API_KEY,
        "PERPLEXITY_API_KEY": config.PERPLEXITY_API_KEY,
    }
    
    missing_keys = []
    placeholder_keys = []
    
    for key_name, key_value in required_keys.items():
        if not key_value:
            missing_keys.append(key_name)
        elif "your_" in key_value.lower() or "here" in key_value.lower():
            placeholder_keys.append(key_name)
    
    if missing_keys:
        logger.error(f"Missing API keys: {', '.join(missing_keys)}")
        return False
    
    if placeholder_keys:
        logger.error(f"API keys not configured (still have placeholder values): {', '.join(placeholder_keys)}")
        return False
    
    logger.info("All API keys validated successfully")
    return True


def get_disk_space() -> dict:
    """
    Get available disk space
    
    Returns:
        Dictionary with disk space info
    """
    try:
        stat = shutil.disk_usage(config.OUTPUT_DIR)
        return {
            "total": stat.total,
            "used": stat.used,
            "free": stat.free,
            "percent_used": (stat.used / stat.total) * 100
        }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking disk space: {e}")
        return {}


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1m 30s")
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        config.OUTPUT_DIR,
        config.TEMP_DIR,
        config.LOGS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def save_metadata(video_path: Path, metadata: dict):
    """
    Save video metadata to JSON file
    
    Args:
        video_path: Path to video file
        metadata: Metadata dictionary
    """
    import json
    
    logger = logging.getLogger(__name__)
    
    try:
        metadata_path = video_path.with_suffix(".json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metadata saved to: {metadata_path}")
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def get_video_metadata(video_path: Path) -> dict:
    """
    Get video metadata from file
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary with video metadata
    """
    import json
    import os
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    try:
        # Try to load existing metadata JSON file
        metadata_path = video_path.with_suffix(".json")
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # If no metadata file, create basic metadata from file info
        stat = os.stat(video_path)
        file_size = get_file_size_mb(video_path)
        
        metadata = {
            "filename": video_path.name,
            "file_size_mb": round(file_size, 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "topic": video_path.stem.split("_")[0] if "_" in video_path.stem else "Unknown",
            "status": "generated"
        }
        
        # Try to get video duration using moviepy
        try:
            from moviepy.editor import VideoFileClip
            with VideoFileClip(str(video_path)) as clip:
                metadata["duration_seconds"] = round(clip.duration, 2)
                metadata["duration_formatted"] = format_duration(clip.duration)
                metadata["resolution"] = f"{clip.w}x{clip.h}"
                metadata["fps"] = clip.fps
        except Exception as e:
            logger.warning(f"Could not get video details: {e}")
            metadata["duration_seconds"] = 0
            metadata["duration_formatted"] = "Unknown"
            metadata["resolution"] = "Unknown"
            metadata["fps"] = 0
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error getting video metadata: {e}")
        return {
            "filename": video_path.name if video_path else "Unknown",
            "error": str(e)
        }


def create_summary_report(
    topic: str,
    video_path: Path,
    duration: float,
    processing_time: float
) -> str:
    """
    Create a summary report of the video generation
    
    Args:
        topic: Video topic
        video_path: Path to generated video
        duration: Video duration in seconds
        processing_time: Time taken to process
        
    Returns:
        Summary report string
    """
    file_size = get_file_size_mb(video_path)
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║           YouTube Shorts Generation Summary                  ║
╚══════════════════════════════════════════════════════════════╝

Topic: {topic}
Video: {video_path.name}
Duration: {format_duration(duration)}
File Size: {file_size:.2f} MB
Processing Time: {format_duration(processing_time)}

Output Location: {video_path}

Status: ✅ Ready for upload
"""
    
    return report
