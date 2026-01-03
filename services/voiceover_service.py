"""
Voiceover Service
Generates AI voiceovers using ElevenLabs API
"""

import requests
import logging
from pathlib import Path
import config

logger = logging.getLogger(__name__)


class VoiceoverService:
    """Generate voiceovers using ElevenLabs Text-to-Speech"""
    
    def __init__(self):
        self.api_key = config.ELEVENLABS_API_KEY
        self.voice_id = config.VOICEOVER_CONFIG["voice_id"]
        self.model_id = config.VOICEOVER_CONFIG["model_id"]
        self.stability = config.VOICEOVER_CONFIG["stability"]
        self.similarity_boost = config.VOICEOVER_CONFIG["similarity_boost"]
        self.style = config.VOICEOVER_CONFIG.get("style", 0.2)
        self.use_speaker_boost = config.VOICEOVER_CONFIG.get("use_speaker_boost", True)
        self.enable_emotion_tags = config.VOICEOVER_CONFIG.get("enable_emotion_tags", True)
        self.emotion_intensity = config.VOICEOVER_CONFIG.get("emotion_intensity", 0.6)
        self.base_url = "https://api.elevenlabs.io/v1"
    
    def generate_voiceover(self, script_text: str, output_path: Path) -> bool:
        """
        Generate voiceover from script text with fallback to OpenAI TTS
        
        Args:
            script_text: Text to convert to speech
            output_path: Path where audio file will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try ElevenLabs first
            try:
                url = f"{self.base_url}/text-to-speech/{self.voice_id}"
                
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.api_key
                }
                
                # Add emotional context to script if enabled
                enhanced_text = self._enhance_script_with_emotions(script_text) if self.enable_emotion_tags else script_text
                
                payload = {
                    "text": enhanced_text,
                    "model_id": self.model_id,
                    "voice_settings": {
                        "stability": self.stability,
                        "similarity_boost": self.similarity_boost,
                        "style": self.style,
                        "use_speaker_boost": self.use_speaker_boost
                    }
                }
                
                logger.info(f"Generating voiceover ({len(script_text)} characters)")
                
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                
                # Save audio file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Voiceover saved to: {output_path}")
                return True
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"ElevenLabs failed: {e}. Trying OpenAI TTS...")
                
                # Fallback to OpenAI TTS
                from openai import OpenAI
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                
                enhanced_text = self._enhance_script_with_emotions(script_text) if self.enable_emotion_tags else script_text
                
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",  # Good for energetic content
                    input=enhanced_text,
                    speed=1.1  # Slightly faster for YouTube Shorts
                )
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                response.stream_to_file(output_path)
                
                logger.info(f"OpenAI TTS voiceover saved to: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error generating voiceover: {e}")
            return False
    
    def generate_subtitles(self, audio_path: Path) -> Path:
        """
        Generate SRT subtitles for the audio file using OpenAI Whisper API
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Path to generated SRT file
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            
            logger.info(f"Generating subtitles for: {audio_path}")
            
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="srt"
                )
            
            srt_path = audio_path.with_suffix(".srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(transcript)
                
            logger.info(f"✅ Subtitles generated: {srt_path}")
            return srt_path
            
        except Exception as e:
            logger.error(f"Error generating subtitles: {e}")
            return None

    def get_available_voices(self) -> list:
        """
        Fetch available voices from ElevenLabs
        
        Returns:
            List of available voices
        """
        try:
            url = f"{self.base_url}/voices"
            
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            voices = data.get("voices", [])
            
            logger.info(f"Found {len(voices)} available voices")
            
            for voice in voices:
                logger.debug(f"Voice: {voice.get('name')} - ID: {voice.get('voice_id')}")
            
            return voices
            
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return []
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get duration of audio file in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(str(audio_path))
            duration = len(audio) / 1000.0  # Convert milliseconds to seconds
            
            logger.info(f"Audio duration: {duration:.2f} seconds")
            return duration
            
        except ImportError:
            logger.warning("pydub not installed, cannot determine audio duration")
            return config.SCRIPT_CONFIG["script_duration_seconds"]
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return config.SCRIPT_CONFIG["script_duration_seconds"]

    def _enhance_script_with_emotions(self, script_text: str) -> str:
        """
        Enhance script with ElevenLabs v3 Alpha emotional audio tags for maximum expressiveness
        
        Args:
            script_text: Original script text
            
        Returns:
            Enhanced script with v3 emotion tags
        """
        if not self.enable_emotion_tags:
            return script_text
            
        try:
            # Use natural speech patterns without literal audio tags
            enhanced_text = script_text
            
            # Apply natural emphasis through punctuation and capitalization
            import re
            
            # Add natural pauses with ellipses instead of literal tags
            enhanced_text = enhanced_text.replace('. ', '... ')
            enhanced_text = enhanced_text.replace('! ', '! ')
            enhanced_text = enhanced_text.replace('? ', '? ')
            
            # Use capitalization for emphasis (v3 responds better to this)
            emphasis_patterns = {
                r'\b(amazing|incredible|insane|crazy|unbelievable|wow)\b': lambda m: m.group(0).upper(),
                r'\b(breaking|urgent|just happened|right now)\b': lambda m: m.group(0).upper(),
            }
            
            for pattern, replacement in emphasis_patterns.items():
                enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
            
            # Add natural speech hesitations
            enhanced_text = enhanced_text.replace(' honestly', ' honestly,')
            enhanced_text = enhanced_text.replace(' you guys', ' you guys,')
            enhanced_text = enhanced_text.replace(' look', ' look,')
            enhanced_text = enhanced_text.replace(' okay so', ' okay so...')
            
            logger.info("Enhanced script with v3 Alpha natural speech patterns")
            return enhanced_text
            
        except Exception as e:
            logger.error(f"Error enhancing script with v3 emotions: {e}")
            return script_text  # Return original on error
