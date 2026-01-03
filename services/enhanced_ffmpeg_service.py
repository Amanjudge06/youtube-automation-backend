"""
Enhanced FFmpeg Service - Production Ready
The enhanced_ffmpeg_service.py content moved here for import
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Dict
import config
import time

logger = logging.getLogger(__name__)


class EnhancedFFmpegVideoService:
    """Enhanced FFmpeg video creation using proven slideshow techniques"""
    
    def __init__(self):
        self.width = config.VIDEO_CONFIG["width"]
        self.height = config.VIDEO_CONFIG["height"] 
        self.fps = config.VIDEO_CONFIG["fps"]
    
    def create_video_slideshow_method(
        self,
        image_paths: List[Path],
        audio_path: Path,
        output_path: Path,
        audio_duration: float = 60.0,
        script_data: Dict = None
    ) -> str:
        """
        Method based on FFmpeg slideshow documentation
        https://trac.ffmpeg.org/wiki/Slideshow
        More reliable than complex filter chains
        """
        try:
            if not image_paths:
                logger.error("No images provided")
                return False
            
            # Convert string paths to Path objects
            image_paths = [Path(p) if isinstance(p, str) else p for p in image_paths]
            audio_path = Path(audio_path) if isinstance(audio_path, str) else audio_path
            output_path = Path(output_path) if isinstance(output_path, str) else output_path
            
            duration_per_image = audio_duration / len(image_paths)
            logger.info(f"Enhanced FFmpeg: Creating slideshow with {len(image_paths)} images, {duration_per_image:.2f}s each")
            
            # Create input list file for concat demuxer
            input_list = Path(config.TEMP_DIR) / f"input_list_{int(time.time())}.txt"
            
            # Process each image individually with effects
            processed_clips = []
            
            for i, img_path in enumerate(image_paths):
                try:
                    # Create individual video clip from image with effects
                    output_clip = Path(config.TEMP_DIR) / f"clip_{i}_{int(time.time())}.mp4"
                    
                    # Different zoom effects for variety  
                    # Increased duration (d) to ensure smooth zoom throughout the clip
                    zoom_effects = [
                        "zoompan=z='min(zoom+0.0015,1.1)':d=750:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
                        "zoompan=z='min(zoom+0.0015,1.1)':d=750:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
                        "zoompan=z='min(zoom+0.0015,1.1)':d=750:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
                        "zoompan=z='min(zoom+0.0015,1.1)':d=750:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
                        "zoompan=z='min(zoom+0.0015,1.1)':d=750:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
                    ]
                    
                    zoom_filter = zoom_effects[i % len(zoom_effects)]
                    
                    # Complex filter to handle landscape images correctly:
                    # 1. Create blurred background filling the screen
                    # 2. Scale foreground image to fit width (1080) without cropping
                    # 3. Overlay foreground on background
                    # 4. Apply subtle zoom to the result
                    filter_complex = (
                        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg];"
                        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                        f"[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1,{zoom_filter}"
                    )
                    
                    cmd = [
                        'ffmpeg', '-y',
                        '-loop', '1',
                        '-i', str(img_path),
                        '-filter_complex', filter_complex,
                        '-c:v', 'libx264',
                        '-preset', 'medium',
                        '-crf', '23',
                        '-pix_fmt', 'yuv420p',
                        '-t', str(duration_per_image),
                        '-r', str(self.fps),
                        str(output_clip)
                    ]
                    
                    logger.info(f"Creating clip {i+1}/{len(image_paths)} with dynamic zoom")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                    
                    if result.returncode == 0 and output_clip.exists():
                        processed_clips.append(output_clip)
                        logger.info(f"✅ Created clip {i+1} successfully")
                    else:
                        logger.error(f"Failed to create clip {i}: {result.stderr}")
                        
                except Exception as e:
                    logger.error(f"Error processing image {i}: {e}")
                    continue
            
            if not processed_clips:
                logger.error("No clips created successfully")
                return False
            
            # Create input list for concat
            with open(input_list, 'w') as f:
                for clip in processed_clips:
                    f.write(f"file '{clip.absolute()}'\n")
            
            # Concatenate all clips
            temp_video = Path(config.TEMP_DIR) / f"concat_{int(time.time())}.mp4"
            
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(input_list),
                '-c', 'copy',
                str(temp_video)
            ]
            
            logger.info("Concatenating video clips...")
            result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"Concatenation failed: {result.stderr}")
                self._cleanup_files(processed_clips + [input_list])
                return False
            
            # Add audio
            logger.info("Adding audio track...")
            final_cmd = [
                'ffmpeg', '-y',
                '-i', str(temp_video),
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                str(output_path)
            ]
            
            result = subprocess.run(final_cmd, capture_output=True, text=True, timeout=120)
            
            # Cleanup
            self._cleanup_files(processed_clips + [input_list, temp_video])
            
            if result.returncode == 0 and output_path.exists():
                logger.info("✅ Enhanced FFmpeg video created successfully!")
                return str(output_path)
            else:
                logger.error(f"Final assembly failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Enhanced FFmpeg method failed: {e}")
            return False
    
    def _cleanup_files(self, file_paths: List[Path]):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"Could not delete {file_path}: {e}")