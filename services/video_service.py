"""
Video Service
Assembles final video using MoviePy
"""

import logging
from pathlib import Path
from typing import List, Optional
import config

try:
    import moviepy
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.video.VideoClip import ImageClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.video.compositing.concatenate import concatenate_videoclips
    from moviepy.video.VideoClip import ColorClip
    from moviepy.audio.AudioClip import CompositeAudioClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # Alternative import approach
        import moviepy.editor as mp
        ImageClip = mp.ImageClip
        AudioFileClip = mp.AudioFileClip
        CompositeVideoClip = mp.CompositeVideoClip
        concatenate_videoclips = mp.concatenate_videoclips
        ColorClip = mp.ColorClip
        CompositeAudioClip = mp.CompositeAudioClip
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False
        logging.warning("MoviePy not installed. Install with: pip install moviepy")

logger = logging.getLogger(__name__)


class VideoService:
    """Assemble videos using MoviePy"""
    
    def __init__(self):
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is required. Install with: pip install moviepy")
        
        self.width = config.VIDEO_CONFIG["width"]
        self.height = config.VIDEO_CONFIG["height"]
        self.fps = config.VIDEO_CONFIG["fps"]
        self.image_duration = config.VIDEO_CONFIG["image_duration"]
        self.fade_duration = config.VIDEO_CONFIG["fade_duration"]
    
    def create_video(
        self,
        image_paths: List[Path],
        audio_path: Path,
        output_path: Path,
        audio_duration: float = None
    ) -> bool:
        """
        Create a vertical video from images and audio
        
        Args:
            image_paths: List of image file paths
            audio_path: Path to audio file
            output_path: Path to save output video
            audio_duration: Duration of audio in seconds (auto-detected if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not image_paths:
                logger.error("No images provided")
                return False
            
            logger.info(f"Creating video with {len(image_paths)} images")
            
            # Load audio
            audio = AudioFileClip(str(audio_path))
            if audio_duration is None:
                audio_duration = audio.duration
            
            logger.info(f"Audio duration: {audio_duration:.2f} seconds")
            
            # Calculate duration per image
            duration_per_image = audio_duration / len(image_paths)
            logger.info(f"Duration per image: {duration_per_image:.2f} seconds")
            
            # Create video clips from images
            clips = []
            for idx, img_path in enumerate(image_paths):
                try:
                    # Create image clip
                    clip = ImageClip(str(img_path))
                    clip = clip.set_duration(duration_per_image)
                    
                    # Resize to fit 9:16 aspect ratio
                    clip = self._resize_and_crop(clip)
                    
                    # Add crossfade transition (except for first clip)
                    if idx > 0 and self.fade_duration > 0:
                        clip = clip.crossfadein(self.fade_duration)
                    
                    clips.append(clip)
                    logger.debug(f"Added image {idx + 1}: {img_path.name}")
                    
                except Exception as e:
                    logger.error(f"Error processing image {img_path}: {e}")
                    continue
            
            if not clips:
                logger.error("No valid clips created")
                return False
            
            # Concatenate clips
            logger.info("Concatenating video clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Set audio
            final_video = final_video.set_audio(audio)
            
            # Set FPS
            final_video = final_video.set_fps(self.fps)
            
            # Add background music if configured
            if config.VIDEO_CONFIG["background_music"]:
                final_video = self._add_background_music(final_video)
            
            # Export video
            logger.info(f"Exporting video to: {output_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            final_video.write_videofile(
                str(output_path),
                codec=config.OUTPUT_CONFIG["video_codec"],
                audio_codec=config.OUTPUT_CONFIG["audio_codec"],
                bitrate=config.OUTPUT_CONFIG["bitrate"],
                fps=self.fps,
                preset="medium",
                threads=4,
            )
            
            # Close clips to free resources
            for clip in clips:
                clip.close()
            audio.close()
            final_video.close()
            
            logger.info(f"Video created successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating video: {e}", exc_info=True)
            return False
    
    def _resize_and_crop(self, clip):
        """
        Resize and crop image to fit 9:16 aspect ratio
        
        Args:
            clip: ImageClip to resize
            
        Returns:
            Resized and cropped clip
        """
        # Get original dimensions
        orig_width, orig_height = clip.size
        target_aspect = self.width / self.height  # 9:16 = 0.5625
        orig_aspect = orig_width / orig_height
        
        if orig_aspect > target_aspect:
            # Image is too wide, crop width
            new_width = int(orig_height * target_aspect)
            x_center = orig_width / 2
            x1 = int(x_center - new_width / 2)
            x2 = int(x_center + new_width / 2)
            clip = clip.crop(x1=x1, x2=x2)
        else:
            # Image is too tall, crop height
            new_height = int(orig_width / target_aspect)
            y_center = orig_height / 2
            y1 = int(y_center - new_height / 2)
            y2 = int(y_center + new_height / 2)
            clip = clip.crop(y1=y1, y2=y2)
        
        # Resize to target dimensions
        clip = clip.resize((self.width, self.height))
        
        return clip
    
    def _add_background_music(self, video_clip):
        """
        Add background music to video
        
        Args:
            video_clip: Video clip to add music to
            
        Returns:
            Video clip with background music
        """
        try:
            music_path = config.VIDEO_CONFIG["background_music"]
            if not Path(music_path).exists():
                logger.warning(f"Background music not found: {music_path}")
                return video_clip
            
            music = AudioFileClip(music_path)
            music = music.volumex(config.VIDEO_CONFIG["background_music_volume"])
            
            # Loop music if it's shorter than video
            if music.duration < video_clip.duration:
                music = music.loop(duration=video_clip.duration)
            else:
                music = music.subclip(0, video_clip.duration)
            
            # Composite audio (mix voiceover with music)
            if video_clip.audio:
                composite_audio = CompositeAudioClip([video_clip.audio, music])
                video_clip = video_clip.set_audio(composite_audio)
            else:
                video_clip = video_clip.set_audio(music)
            
            logger.info("Background music added")
            return video_clip
            
        except Exception as e:
            logger.error(f"Error adding background music: {e}")
            return video_clip
    
    def create_simple_video(
        self,
        image_paths: List[Path],
        output_path: Path,
        duration: float = 10.0
    ) -> bool:
        """
        Create a simple video without audio (for testing)
        
        Args:
            image_paths: List of image paths
            output_path: Output video path
            duration: Total duration in seconds
            
        Returns:
            True if successful
        """
        try:
            duration_per_image = duration / len(image_paths)
            
            clips = []
            for img_path in image_paths:
                clip = ImageClip(str(img_path))
                clip = clip.set_duration(duration_per_image)
                clip = self._resize_and_crop(clip)
                clips.append(clip)
            
            final_video = concatenate_videoclips(clips, method="compose")
            final_video = final_video.set_fps(self.fps)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_video.write_videofile(
                str(output_path),
                codec=config.OUTPUT_CONFIG["video_codec"],
                fps=self.fps,
            )
            
            for clip in clips:
                clip.close()
            final_video.close()
            
            logger.info(f"Simple video created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating simple video: {e}")
            return False
