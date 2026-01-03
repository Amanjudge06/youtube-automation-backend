"""
Enhanced Video Creator with Simple Working Approach
Creates videos using a proven FFmpeg approach that actually works
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional
import config
import time
import platform

logger = logging.getLogger(__name__)


class SimpleVideoService:
    """Create videos using a working FFmpeg approach with background and subtitles"""
    
    def __init__(self):
        self.width = config.VIDEO_CONFIG["width"]  # 1080 for 9:16
        self.height = config.VIDEO_CONFIG["height"]  # 1920 for 9:16
        self.fps = config.VIDEO_CONFIG["fps"]
        self.subscribe_bg_path = Path(config.BASE_DIR) / config.VIDEO_CONFIG["subscribe_background"]
        
        # Detect hardware acceleration
        self.hw_encoder = self._detect_hardware_encoder()
        if self.hw_encoder:
            logger.info(f"🚀 Hardware acceleration enabled: {self.hw_encoder}")
        else:
            logger.info("⚙️  Using software encoding (slower but compatible)")
    
    def create_video_with_ffmpeg(
        self,
        image_paths: List[Path],
        audio_path: Path,
        output_path: Path,
        audio_duration: float = 30.0,
        script_data: Dict = None,
        subtitles_path: Path = None
    ) -> bool:
        """
        Production-grade video creation using ONE FFmpeg filtergraph
        - No intermediate files
        - No stream copy issues
        - Proper normalization before effects
        - Algorithm-friendly micro-motion
        """
        try:
            if not image_paths:
                logger.error("No images provided")
                return False
            
            # Filter out invalid images
            valid_images = []
            for img_path in image_paths:
                try:
                    result = subprocess.run(['file', str(img_path)], capture_output=True, text=True, timeout=5)
                    if 'image data' in result.stdout.lower() or any(fmt in result.stdout.lower() for fmt in ['jpeg', 'jpg', 'png', 'gif', 'webp']):
                        valid_images.append(img_path)
                    else:
                        logger.warning(f"Skipping invalid image: {img_path}")
                except Exception as e:
                    logger.warning(f"Could not validate image {img_path}: {e}")
                    valid_images.append(img_path)
            
            if not valid_images:
                logger.error("No valid images found after filtering")
                return False
            
            logger.info(f"Creating video with {len(valid_images)} valid images using single filtergraph")
            image_paths = valid_images
            
            # Duration per image - FASTER for retention (3-4s max)
            max_duration_per_image = 4.0  # Never exceed 4 seconds per image
            duration_per_image = min(audio_duration / len(image_paths), max_duration_per_image)
            
            # If we need more images to fill duration, repeat some
            if audio_duration / len(image_paths) > max_duration_per_image:
                images_needed = int(audio_duration / max_duration_per_image) + 1
                # Cycle through images to reach needed count
                extended_paths = (image_paths * ((images_needed // len(image_paths)) + 1))[:images_needed]
                image_paths = extended_paths
                duration_per_image = audio_duration / len(image_paths)
            
            logger.info(f"Duration per image: {duration_per_image:.2f}s (optimized for retention)")
            logger.info(f"Total images used: {len(image_paths)}")
            
            # Build FFmpeg command with ONE filtergraph
            cmd = ['ffmpeg', '-y']
            
            # Add all images as inputs WITHOUT loop (zoompan handles duration)
            for img_path in image_paths:
                cmd.extend([
                    '-i', str(img_path)
                ])
            
            # Add audio input
            cmd.extend(['-i', str(audio_path)])
            
            # Build filtergraph: normalize → effects → concat
            filter_parts = []
            # MORE AGGRESSIVE MOTION for retention
            motion_types = [
                "z='min(zoom+0.0015,1.25)'",   # Aggressive zoom in
                "z='if(lte(zoom,1.0),1.3,max(1.0,zoom-0.002))'",  # Zoom out from 1.3x
                "z='min(zoom+0.002,1.35)'",    # Fast zoom in
                "z='min(zoom+0.0012,1.2)'",    # Medium-fast zoom
                "z='if(lte(zoom,1.0),1.25,max(1.0,zoom-0.0015))'",  # Ken Burns effect
                "z='min(zoom+0.0018,1.3)'",    # Dynamic zoom
                "z='min(zoom+0.001,1.15)'"     # Subtle zoom
            ]
            
            for i in range(len(image_paths)):
                # Normalize FIRST: scale + crop (no black bars)
                # Then apply zoompan for micro-motion
                # Add setsar=1 to fix SAR mismatches
                motion = motion_types[i % len(motion_types)]
                frames = int(duration_per_image * 30)  # 30 fps
                
                # Complex filter to handle landscape images correctly:
                # 1. Create blurred background filling the screen
                # 2. Scale foreground image to fit width (1080) without cropping
                # 3. Overlay foreground on background
                # 4. Apply subtle zoom to the result
                filter_parts.append(
                    f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg{i}];"
                    f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg{i}];"
                    f"[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2:shortest=1,setsar=1,"
                    f"zoompan={motion}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30[v{i}]"
                )
            
            # Concatenate all processed streams
            concat_inputs = ''.join(f'[v{i}]' for i in range(len(image_paths)))
            filter_parts.append(f"{concat_inputs}concat=n={len(image_paths)}:v=1:a=0,format=yuv420p[outv]")
            
            # Complete filtergraph
            filtergraph = ';'.join(filter_parts)
            
            # Add filtergraph and output parameters with hardware acceleration
            cmd.extend([
                '-filter_complex', filtergraph,
                '-map', '[outv]',
                '-map', f'{len(image_paths)}:a',  # Audio from last input
            ])
            
            # Use hardware encoder if available (2x faster)
            if self.hw_encoder:
                if 'videotoolbox' in self.hw_encoder:
                    cmd.extend(['-c:v', self.hw_encoder, '-b:v', '3M'])
                elif 'nvenc' in self.hw_encoder:
                    cmd.extend(['-c:v', self.hw_encoder, '-preset', 'p4', '-b:v', '3M'])
                else:
                    cmd.extend(['-c:v', self.hw_encoder, '-b:v', '3M'])
            else:
                cmd.extend(['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '26'])
            
            cmd.extend([
                '-c:a', 'aac',
                '-r', '30',
                '-shortest',
                str(output_path)
            ])
            
            logger.info("Creating video with single-pass filtergraph...")
            logger.info(f"Processing {len(image_paths)} images with alternating motion effects")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("🎬 Video created successfully with production-grade pipeline!")
                
                # Add subtitles if provided (PRIORITY)
                if subtitles_path and subtitles_path.exists():
                    logger.info("📝 Adding generated captions from Whisper...")
                    return self._add_subtitles_to_video(output_path, script_data, audio_duration, subtitles_path)
                
                # Fallback to estimated subtitles
                if script_data and script_data.get('script'):
                    logger.info("📝 Adding estimated captions...")
                    return self._add_subtitles_to_video(output_path, script_data, audio_duration)
                
                return True
            else:
                logger.error(f"Video creation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg command timed out")
            return False
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            return False
    
    def _add_subtitles_to_video(self, video_path: Path, script_data: Dict, audio_duration: float, srt_path: Path = None) -> bool:
        """Add burned-in subtitles with bold styling for mobile retention"""
        try:
            temp_srt = False
            if not srt_path:
                # Create SRT file from script estimation
                srt_content = self._create_subtitle_content(script_data, audio_duration, 0)
                if not srt_content:
                    logger.warning("No subtitle content generated, skipping captions")
                    return True
                
                import time
                srt_path = Path(config.TEMP_DIR) / f"subtitles_{int(time.time())}.srt"
                with open(srt_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                temp_srt = True
            
            # Create output with subtitles
            output_with_subs = video_path.with_stem(f"{video_path.stem}_captioned")
            
            # FFmpeg subtitle filter - BOLD, high-contrast, mobile-optimized
            # Use relative path for subtitles to avoid escaping issues on some systems, but absolute is safer if handled right
            # We'll use the absolute path but ensure it's properly formatted
            
            subtitle_filter = (
                f"subtitles='{srt_path}':"
                f"force_style='FontName=Arial Black,FontSize=24,Bold=1,"
                f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,"
                f"BackColour=&H80000000,Outline=2,Shadow=1,"
                f"Alignment=2,MarginV=60'"
            )
            
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-vf', subtitle_filter,
                '-c:v', self.hw_encoder if self.hw_encoder else 'libx264',
            ]
            
            # Add bitrate control for subtitles pass too
            if self.hw_encoder:
                cmd.extend(['-b:v', '3M'])
            else:
                cmd.extend(['-crf', '26'])

            cmd.extend([
                '-c:a', 'copy',  # Don't re-encode audio
                str(output_with_subs)
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Replace original with captioned version
                output_with_subs.replace(video_path)
                if temp_srt and srt_path.exists():
                    srt_path.unlink()  # Clean up temp SRT file
                logger.info("✅ Captions added successfully!")
                return True
            else:
                logger.warning(f"Subtitle addition failed, keeping original: {result.stderr[:200]}")
                return True  # Don't fail the whole pipeline
                
        except Exception as e:
            logger.warning(f"Error adding subtitles: {e}")
            return True  # Don't fail the whole pipeline

    def _cleanup_segments(self, segments: List[Path]):
        """Clean up temporary segment files"""
        for segment in segments:
            if segment.exists():
                try:
                    segment.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete {segment}: {e}")

    def _cleanup_all(self, segments: List[Path], concat_file: Path = None, temp_video: Path = None):
        """Clean up all temporary files"""
        self._cleanup_segments(segments)
        
        if concat_file and concat_file.exists():
            try:
                concat_file.unlink()
            except Exception as e:
                logger.warning(f"Could not delete concat file: {e}")
                
        if temp_video and temp_video.exists():
            try:
                temp_video.unlink()
            except Exception as e:
                logger.warning(f"Could not delete temp video: {e}")

    def _create_subtitle_content(self, script_data: Dict, audio_duration: float, num_images: int) -> str:
        """Create SRT subtitle content with BOLD key phrases for retention"""
        try:
            if not script_data:
                return ""
            
            # Use main script text instead of scene narration for better sync
            main_script = script_data.get('script', '')
            if not main_script:
                # Fallback to scenes if no main script
                scenes = script_data.get('scenes', [])
                if not scenes:
                    return ""
                main_script = ' '.join([scene.get('narration', '') for scene in scenes])
            
            # Split script into smaller chunks for mobile readability (2-4 words max)
            words = main_script.split()
            chunks = []
            current_chunk = []
            
            # Key phrases to EMPHASIZE (make uppercase)
            emphasis_keywords = ['INSANE', 'SHOCKING', 'CRAZY', 'MILLION', 'BILLION', 
                               'WAIT', 'BREAKING', 'EXCLUSIVE', 'REVEALED', 'SECRET',
                               'DRAMA', 'SCANDAL', 'LAWSUIT', 'BEEF', 'EXPOSED']
            
            for word in words:
                # Emphasize key words
                clean_word = word.strip('.,!?')
                if any(keyword.lower() in clean_word.lower() for keyword in emphasis_keywords):
                    word = word.upper()
                
                current_chunk.append(word)
                # SHORTER chunks (2-4 words) for rapid-fire captions
                if len(current_chunk) >= 3:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
            
            if current_chunk:  # Add remaining words
                chunks.append(' '.join(current_chunk))
            
            if not chunks:
                return ""
            
            srt_lines = []
            duration_per_chunk = audio_duration / len(chunks)
            
            for i, chunk in enumerate(chunks):
                # Add slight delay to sync better with narration (0.2s offset)
                start_time = (i * duration_per_chunk) + 0.2
                end_time = ((i + 1) * duration_per_chunk) + 0.2
                
                # Ensure we don't exceed audio duration
                if start_time >= audio_duration:
                    break
                if end_time > audio_duration:
                    end_time = audio_duration
                    
                # Format time as SRT timestamp (HH:MM:SS,mmm)
                start_srt = self._seconds_to_srt_time(start_time)
                end_srt = self._seconds_to_srt_time(end_time)
                
                if chunk.strip():
                    srt_lines.append(str(i + 1))
                    srt_lines.append(f"{start_srt} --> {end_srt}")
                    srt_lines.append(chunk.strip())
                    srt_lines.append("")  # Empty line between subtitles
            
            return "\n".join(srt_lines)
            
        except Exception as e:
            logger.error(f"Error creating subtitle content: {e}")
            return ""
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


    def _detect_hardware_encoder(self) -> Optional[str]:
        """Detect available hardware encoder for faster video processing"""
        try:
            # Get list of available encoders
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=5
            )
            encoders = result.stdout.lower()
            
            system = platform.system()
            
            # Check for hardware encoders based on OS
            if system == 'Darwin':  # macOS
                if 'h264_videotoolbox' in encoders:
                    return 'h264_videotoolbox'
            elif system == 'Linux':
                if 'h264_nvenc' in encoders:
                    return 'h264_nvenc'  # NVIDIA
                elif 'h264_vaapi' in encoders:
                    return 'h264_vaapi'  # Intel/AMD
            elif system == 'Windows':
                if 'h264_nvenc' in encoders:
                    return 'h264_nvenc'  # NVIDIA
                elif 'h264_qsv' in encoders:
                    return 'h264_qsv'  # Intel Quick Sync
            
            return None  # Fallback to software encoding
        except Exception as e:
            logger.warning(f"Hardware encoder detection failed: {e}")
            return None


def test_ffmpeg_available():
    """Test if FFmpeg is available and working"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except:
        return False