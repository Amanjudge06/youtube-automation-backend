# YouTube Shorts Automation System

A fully automated, headless Python system that creates YouTube Shorts videos from trending topics. Runs end-to-end without manual intervention.

## 🎯 Features

- **Automated Trending Topic Detection**: Fetches real-time trending topics from Google Trends via SERP API
- **AI Script Generation**: Creates engaging 20-30 second scripts using OpenAI GPT
- **Professional Voiceover**: Converts scripts to natural-sounding audio using ElevenLabs
- **Smart Image Sourcing**: Automatically fetches relevant, high-quality images via SERP API
- **Video Assembly**: Creates vertical (9:16) videos ready for YouTube Shorts
- **Modular Architecture**: Clean, maintainable service-based structure
- **Config-Driven**: All settings in one config file
- **Server-Ready**: Designed to run via cron jobs or cloud VMs

## 📁 Project Structure

```
YouTube Automation/
├── config.py                    # All configuration and API keys
├── main.py                      # Main orchestration script
├── requirements.txt             # Python dependencies
├── services/
│   ├── trends_service.py       # Fetch trending topics (SERP API)
│   ├── script_generator.py     # Generate scripts (OpenAI)
│   ├── voiceover_service.py    # Generate voiceover (ElevenLabs)
│   ├── image_service.py        # Fetch images (SERP API)
│   └── video_service.py        # Assemble video (MoviePy)
├── utils/
│   └── helpers.py              # Utility functions
├── output/                     # Generated videos
├── temp/                       # Temporary files
└── logs/                       # Application logs
```

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
# Install FFmpeg (required for MoviePy)
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html

# Install Python packages
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit [config.py](config.py) and add your API keys:

```python
# SERP API (https://serpapi.com/)
SERP_API_KEY = "your_serp_api_key_here"

# OpenAI API (https://platform.openai.com/)
OPENAI_API_KEY = "your_openai_api_key_here"

# ElevenLabs API (https://elevenlabs.io/)
ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"
```

Or use environment variables:

```bash
export SERP_API_KEY="your_key"
export OPENAI_API_KEY="your_key"
export ELEVENLABS_API_KEY="your_key"
```

### 3. Customize Settings (Optional)

In [config.py](config.py), adjust:
- **Region**: Change `TRENDING_CONFIG["region"]` to your target region (US, GB, AU, etc.)
- **Video Duration**: Adjust `SCRIPT_CONFIG["script_duration_seconds"]`
- **Voice**: Change `VOICEOVER_CONFIG["voice_id"]` for different voices
- **Video Quality**: Modify `VIDEO_CONFIG` settings

## 📺 Usage

### Run with Trending Topics (Automatic)

```bash
python main.py
```

This will:
1. Fetch trending topics from Google Trends
2. Select the best topic
3. Generate an engaging script
4. Create AI voiceover
5. Fetch relevant images
6. Assemble a 9:16 video
7. Save to `output/` directory

### Run with Custom Topic

```bash
python main.py --topic "Artificial Intelligence Breakthrough"
```

### Test Configuration

```bash
python main.py --test
```

Validates that all API keys are properly configured.

## 🔧 Advanced Configuration

### Background Music (Optional)

1. Add a music file to your project
2. Update [config.py](config.py):

```python
VIDEO_CONFIG = {
    ...
    "background_music": "path/to/music.mp3",
    "background_music_volume": 0.1,  # 10% volume
}
```

### Scheduling with Cron

Create videos automatically every 6 hours:

```bash
# Edit crontab
crontab -e

# Add this line
0 */6 * * * cd /path/to/YouTube\ Automation && /usr/bin/python3 main.py
```

### Running on Cloud Server

```bash
# Using screen for persistent sessions
screen -S youtube-automation
python main.py

# Detach with Ctrl+A, D
# Reattach with: screen -r youtube-automation
```

## 📊 Output Files

Each video generation creates:

1. **Video File**: `output/Topic_Name_20231222_143022.mp4`
2. **Metadata File**: `output/Topic_Name_20231222_143022.json`
   - Includes title, description, hashtags, script
   - Ready for YouTube upload

## 🎨 Video Specifications

- **Aspect Ratio**: 9:16 (YouTube Shorts)
- **Resolution**: 1080x1920 pixels
- **Format**: MP4 (H.264)
- **Audio**: AAC codec
- **Frame Rate**: 30 FPS
- **Duration**: 20-30 seconds (configurable)

## 🔍 API Requirements

### SERP API
- **Purpose**: Fetch trending topics and images
- **Free Tier**: 100 searches/month
- **Sign up**: https://serpapi.com/

### OpenAI API
- **Purpose**: Generate engaging scripts
- **Model**: GPT-4 Turbo (configurable to GPT-3.5)
- **Sign up**: https://platform.openai.com/

### ElevenLabs API
- **Purpose**: AI voiceover generation
- **Free Tier**: 10,000 characters/month
- **Sign up**: https://elevenlabs.io/

## 🛠️ Troubleshooting

### MoviePy/FFmpeg Issues

```bash
# Ensure FFmpeg is installed
ffmpeg -version

# Reinstall MoviePy
pip uninstall moviepy
pip install moviepy --no-cache-dir
```

### API Errors

```bash
# Test API configuration
python main.py --test

# Check logs
tail -f logs/youtube_automation.log
```

### Image Download Failures

- Some images may fail due to server restrictions
- System automatically fetches backup images
- Adjust `IMAGE_CONFIG["num_images"]` for more fallbacks

## 📝 Customization Examples

### Change Voice

List available voices:

```python
from services.voiceover_service import VoiceoverService

service = VoiceoverService()
voices = service.get_available_voices()
for voice in voices:
    print(f"{voice['name']}: {voice['voice_id']}")
```

Update [config.py](config.py):

```python
VOICEOVER_CONFIG = {
    "voice_id": "new_voice_id_here",
    ...
}
```

### Blacklist Topics

Add keywords to avoid:

```python
TOPIC_SELECTION = {
    ...
    "blacklist_keywords": ["nsfw", "tragedy", "death", "politics"],
}
```

### Use Google News Instead

In [main.py](main.py), replace:

```python
trending_topics = trends_service.get_trending_topics()
```

With:

```python
trending_topics = trends_service.get_google_news_trending()
```

## 🔒 Security Best Practices

1. **Never commit API keys** to version control
2. Use environment variables for production
3. Add `.env` to `.gitignore`
4. Rotate API keys regularly
5. Use separate keys for dev/prod environments

## 📈 Scaling & Performance

- **Processing Time**: ~2-5 minutes per video
- **Disk Space**: ~10-50 MB per video
- **Concurrent Execution**: Not recommended (API rate limits)
- **Daily Capacity**: Depends on API tier limits

## 🐛 Known Limitations

- SERP API has rate limits (100 searches/month on free tier)
- ElevenLabs free tier: 10,000 characters/month
- Some trending topics may not have suitable images
- Video quality depends on source image quality

## 📄 License

This project is for educational purposes. Ensure you comply with:
- YouTube's Terms of Service
- API providers' usage policies
- Copyright laws for images/content

## 🤝 Contributing

This is a production-ready automation system. To extend:
1. Add new services in `services/`
2. Update config in [config.py](config.py)
3. Modify pipeline in [main.py](main.py)

## 📧 Support

Check logs for detailed error messages:

```bash
tail -f logs/youtube_automation.log
```

## 🎬 Example Output

After running the system, you'll get:

```
╔══════════════════════════════════════════════════════════════╗
║           YouTube Shorts Generation Summary                  ║
╚══════════════════════════════════════════════════════════════╝

Topic: AI Breakthrough in Medical Research
Video: AI_Breakthrough_Medical_Research_20231222_143022.mp4
Duration: 28s
File Size: 12.45 MB
Processing Time: 3m 42s

Output Location: output/AI_Breakthrough_Medical_Research_20231222_143022.mp4

Status: ✅ Ready for upload
```

---

**Ready to create viral YouTube Shorts automatically! 🚀**
