import subprocess
from pathlib import Path
import time
import logging
from typing import List, Dict, Any, Optional
import config

logger = logging.getLogger(__name__)

class EnhancedVideoService:
    """Enhanced video creation service with effects, transitions, and subtitles"""
    
    def create_enhanced_video(self, image_paths: List[Path], audio_path: Path, 
                             script_data: Dict[str, Any], audio_duration: float) -> Optional[Path]:
        """Create video with layered approach: align images first, then apply effects"""
        try:
            timestamp = int(time.time())
            topic = script_data.get('topic', 'video').replace(' ', '_')
            
            logger.info(f"Creating enhanced video with {len(image_paths)} images using layered approach")
            
            # Step 1: Create aligned slideshow without effects
            temp_slideshow = Path(config.TEMP_DIR) / f"slideshow_{timestamp}.mp4"
            slideshow_success = self._create_basic_slideshow(image_paths, audio_duration, temp_slideshow)
            
            if not slideshow_success:
                logger.error("Failed to create basic slideshow")
                return None
            
            # Step 2: Add audio to slideshow
            temp_with_audio = Path(config.TEMP_DIR) / f"with_audio_{timestamp}.mp4"
            audio_success = self._add_audio_to_video(temp_slideshow, audio_path, temp_with_audio)
            
            if not audio_success:
                logger.error("Failed to add audio")
                return None
            
            # Step 3: Apply effects and subtitles
            output_path = Path(config.OUTPUT_DIR) / f"{topic}_{timestamp}_enhanced.mp4"
            effects_success = self._apply_effects_and_subtitles(temp_with_audio, script_data, audio_duration, timestamp, output_path)
            
            if effects_success:
                logger.info(f"✅ Enhanced video created: {output_path}")
                # Cleanup temp files
                temp_slideshow.unlink(missing_ok=True)
                temp_with_audio.unlink(missing_ok=True)
                return output_path
            else:
                # Fallback: return the audio version if effects fail
                logger.warning("Effects failed, returning basic video with audio")
                fallback_path = Path(config.OUTPUT_DIR) / f"{topic}_{timestamp}_basic.mp4"
                temp_with_audio.rename(fallback_path)
                return fallback_path
                
        except Exception as e:
            logger.error(f"Error creating enhanced video: {e}")
            return None
    
    def _create_basic_slideshow(self, image_paths: List[Path], audio_duration: float, output_path: Path) -> bool:
        """Step 1: Create basic aligned slideshow"""
        try:
            duration_per_image = audio_duration / len(image_paths)
            logger.info(f"Creating basic slideshow: {duration_per_image:.2f}s per image")
            
            # Simple slideshow with just scaling and padding
            inputs = []
            for img_path in image_paths:
                inputs.extend(['-loop', '1', '-t', str(duration_per_image), '-i', str(img_path)])
            
            # Simple concat without effects
            filter_parts = []
            for i in range(len(image_paths)):
                filter_parts.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[v{i}]")
            
            concat_inputs = ''.join(f'[v{i}]' for i in range(len(image_paths)))
            filter_parts.append(f"{concat_inputs}concat=n={len(image_paths)}:v=1[out]")
            
            cmd = [
                'ffmpeg', '-y'
            ] + inputs + [
                '-filter_complex', ';'.join(filter_parts),
                '-map', '[out]',
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '28',
                '-r', '30', '-pix_fmt', 'yuv420p',
                str(output_path)
            ]
            
            logger.info("Creating basic slideshow...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error creating basic slideshow: {e}")
            return False
    
    def _add_audio_to_video(self, video_path: Path, audio_path: Path, output_path: Path) -> bool:
        """Step 2: Add audio to video"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '128k',
                '-shortest',
                str(output_path)
            ]
            
            logger.info("Adding audio to slideshow...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error adding audio: {e}")
            return False
    
    def _apply_effects_and_subtitles(self, video_path: Path, script_data: Dict, 
                                   audio_duration: float, timestamp: int, output_path: Path) -> bool:
        """Step 3: Apply effects and subtitles in final pass"""
        try:
            filter_parts = []
            
            # Create subtitle file if we have scenes
            if script_data.get('scenes'):
                subtitle_path = self._create_subtitle_file(script_data, audio_duration, timestamp)
                if subtitle_path:
                    filter_parts.append(f"[0:v]subtitles='{subtitle_path}':force_style='Fontsize=24,PrimaryColour=&Hffffff,Bold=1,OutlineColour=&H000000,Outline=3,BorderStyle=3,Alignment=10,MarginV=50'[withsubs]")
                    video_map = "[withsubs]"
                else:
                    video_map = "0:v"
            else:
                video_map = "0:v"
            
            # Add simple zoom and color enhancement
            if filter_parts:
                filter_parts.append(f"{video_map}zoompan=z='min(zoom+0.001,1.2)':d=1:fps=30,eq=brightness=0.03:contrast=1.05[final]")
                final_map = "[final]"
            else:
                filter_parts = [f"[0:v]zoompan=z='min(zoom+0.001,1.2)':d=1:fps=30,eq=brightness=0.03:contrast=1.05[final]"]
                final_map = "[final]"
            
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-filter_complex', ';'.join(filter_parts),
                '-map', final_map,
                '-map', '0:a',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-c:a', 'copy',
                str(output_path)
            ]
            
            logger.info("Applying effects and subtitles...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error applying effects: {e}")
            return False
    
    def _create_subtitle_file(self, script_data: Dict, audio_duration: float, timestamp: int) -> Optional[Path]:
        """Create SRT subtitle file from script scenes"""
        try:
            scenes = script_data.get('scenes', [])
            if not scenes:
                return None
            
            subtitle_path = Path(config.TEMP_DIR) / f"subtitles_{timestamp}.srt"
            
            srt_content = []
            time_per_scene = audio_duration / len(scenes)
            
            for i, scene in enumerate(scenes):
                start_time = i * time_per_scene
                end_time = (i + 1) * time_per_scene
                
                # Format subtitle text
                narration = scene.get('narration', '')
                if narration:
                    # Clean up narration for display
                    subtitle_text = narration.replace('"', '').replace("'", "").strip()
                    if len(subtitle_text) > 60:
                        subtitle_text = subtitle_text[:57] + "..."
                    
                    srt_content.append(str(i + 1))
                    srt_content.append(f"{self._seconds_to_srt_time(start_time)} --> {self._seconds_to_srt_time(end_time)}")
                    srt_content.append(subtitle_text)
                    srt_content.append("")  # Empty line
            
            if srt_content:
                with open(subtitle_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(srt_content))
                
                logger.info(f"Created subtitle file: {subtitle_path}")
                return subtitle_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating subtitles: {e}")
            return None
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def create_thumbnail(self, image_paths: List[Path], script_data: Dict) -> Optional[Path]:
        """Generate clickable thumbnail from video images"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            if not image_paths:
                return None
            
            # Use first image as base
            base_image = Image.open(image_paths[0])
            base_image = base_image.resize((1280, 720))  # YouTube thumbnail size
            
            # Add text overlay
            draw = ImageDraw.Draw(base_image)
            
            # Try to use system font, fallback to default
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
                font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
            except:
                font = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Get title from script
            title = script_data.get('title', 'TRENDING NOW')
            if len(title) > 35:
                title = title[:32] + "..."
            
            # Add background rectangle for text
            text_bbox = draw.textbbox((0, 0), title, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position text in lower third
            x = (1280 - text_width) // 2
            y = 720 - text_height - 80
            
            # Background rectangle
            draw.rectangle([x-20, y-10, x+text_width+20, y+text_height+10], fill=(0, 0, 0, 180))
            
            # Title text
            draw.text((x, y), title, font=font, fill=(255, 255, 255))
            
            # Add "TRENDING" badge
            badge_text = "🔥 TRENDING"
            draw.text((50, 50), badge_text, font=font_small, fill=(255, 100, 100))
            
            # Save thumbnail
            timestamp = int(time.time())
            topic = script_data.get('topic', 'video').replace(' ', '_')
            thumbnail_path = Path(config.OUTPUT_DIR) / f"{topic}_{timestamp}_thumbnail.jpg"
            
            base_image.save(thumbnail_path, 'JPEG', quality=95)
            logger.info(f"✅ Thumbnail created: {thumbnail_path}")
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return None