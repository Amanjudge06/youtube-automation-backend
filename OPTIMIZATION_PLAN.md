# 🚀 Video Pipeline Optimization Plan

## Current Performance Baseline
- **Total Pipeline Time:** ~180-240 seconds (3-4 minutes)
  - Trending Analysis: ~10s
  - Research: ~15s  
  - Script Generation: ~20s
  - Voiceover: ~25s
  - Image Download: ~30s (sequential)
  - Video Assembly: ~60-80s
  - Upload: ~20s

## 🎯 Optimization Targets

### **Priority 1: High Impact, Easy Implementation**

#### 1. ⚡ Parallel Image Downloads (Save ~22s)
**Current:** Sequential downloads (30s for 14 images)
**Optimized:** Concurrent downloads with ThreadPoolExecutor (6-8s)
**Impact:** 70% time reduction on image fetching
**Complexity:** Low

```python
# Implementation:
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_images_parallel(self, images: List[Dict], output_dir: Path, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(self._download_single_image, img, output_dir): img 
                   for img in images}
        downloaded_paths = []
        for future in as_completed(futures):
            result = future.result()
            if result:
                downloaded_paths.append(result)
    return downloaded_paths
```

#### 2. 🎬 FFmpeg Hardware Acceleration (Save ~20-30s)
**Current:** Software encoding with veryfast preset (~60-80s)
**Optimized:** Hardware acceleration (h264_videotoolbox on Mac) (~30-40s)
**Impact:** 40-50% time reduction on video assembly
**Complexity:** Low

```bash
# Check if hardware encoding available:
ffmpeg -encoders | grep videotoolbox

# Replace:
-c:v libx264 -preset veryfast
# With:
-c:v h264_videotoolbox -b:v 5M
```

#### 3. 📊 Batch Image API Calls (Save ~10s)
**Current:** 5-7 separate SerpAPI calls
**Optimized:** 1-2 calls fetching 20+ images each
**Impact:** 60% reduction in API latency
**Complexity:** Low

```python
# Instead of multiple queries:
for query in queries:
    images = self.search_images(query, 3)  # 7 API calls

# Batch approach:
primary_images = self.search_images(main_query, 15)  # 1 API call
fallback_images = self.search_images(fallback_query, 5)  # 1 API call
```

#### 4. 🎤 Audio Pre-normalization (Save ~5s)
**Current:** FFmpeg normalizes during video assembly
**Optimized:** Pre-normalize audio file before video creation
**Impact:** Simpler FFmpeg command, faster processing
**Complexity:** Low

```python
# Add audio normalization step:
def normalize_audio(self, audio_path: Path) -> Path:
    normalized_path = audio_path.with_stem(f"{audio_path.stem}_normalized")
    cmd = [
        'ffmpeg', '-i', str(audio_path),
        '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
        '-ar', '44100', '-ac', '2',
        str(normalized_path)
    ]
    subprocess.run(cmd, capture_output=True, timeout=10)
    return normalized_path
```

---

### **Priority 2: Medium Impact, Moderate Complexity**

#### 5. 🔄 Async Voiceover + Images (Save ~25s)
**Current:** Sequential: Voiceover (25s) → then Images (30s)
**Optimized:** Parallel: Both at same time (30s total)
**Impact:** 40% time reduction on content gathering
**Complexity:** Medium

```python
import asyncio

async def gather_content_parallel(self, script_data, topic):
    # Run voiceover and image fetch simultaneously
    voiceover_task = asyncio.to_thread(self.voiceover_service.generate, script_data['script'])
    images_task = asyncio.to_thread(self.image_service.fetch_images, script_data['scenes'])
    
    audio_path, image_paths = await asyncio.gather(voiceover_task, images_task)
    return audio_path, image_paths
```

#### 6. 💾 Intelligent Image Caching (Save ~15-30s on repeated topics)
**Current:** Re-download same images for similar topics
**Optimized:** Cache images by query hash for 24 hours
**Impact:** Near-instant image retrieval for popular topics
**Complexity:** Medium

```python
import hashlib
from datetime import datetime, timedelta

class ImageCache:
    def __init__(self, cache_dir: Path, ttl_hours=24):
        self.cache_dir = cache_dir / "cache"
        self.ttl = timedelta(hours=ttl_hours)
        
    def get_cached_images(self, query: str) -> Optional[List[Path]]:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cache_path = self.cache_dir / query_hash
        
        if cache_path.exists():
            cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if datetime.now() - cache_time < self.ttl:
                return list(cache_path.glob("*.jpg"))
        return None
```

#### 7. 🎯 Dynamic Scene Count (Better Quality)
**Current:** Fixed 14 scenes regardless of script length
**Optimized:** Calculate optimal scene count: 1 scene per 3-4 seconds
**Impact:** Better visual pacing, less redundant images
**Complexity:** Medium

```python
def calculate_optimal_scenes(self, script_length: int, audio_duration: float) -> int:
    """
    Calculate ideal number of scenes based on script density
    - Fast-paced scripts (220+ WPM): 1 scene per 3s (18 scenes for 55s)
    - Normal scripts (150-220 WPM): 1 scene per 4s (14 scenes)
    - Slow scripts (<150 WPM): 1 scene per 5s (11 scenes)
    """
    words_per_minute = (script_length / audio_duration) * 60
    
    if words_per_minute > 220:
        return int(audio_duration / 3)
    elif words_per_minute > 150:
        return int(audio_duration / 4)
    else:
        return int(audio_duration / 5)
```

#### 8. 🖼️ Image Pre-processing Pipeline (Save ~10s)
**Current:** FFmpeg resizes images during video assembly
**Optimized:** Pre-resize and optimize images before FFmpeg
**Impact:** Faster FFmpeg processing, smaller memory footprint
**Complexity:** Medium

```python
from PIL import Image

def preprocess_image(self, img_path: Path, output_path: Path) -> Path:
    """Resize and optimize image before FFmpeg processing"""
    with Image.open(img_path) as img:
        # Convert to RGB (remove alpha channel)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to exact video dimensions
        img_resized = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        
        # Save with optimal quality
        img_resized.save(output_path, 'JPEG', quality=92, optimize=True)
    
    return output_path
```

---

### **Priority 3: High Impact, High Complexity**

#### 9. 📝 Strict JSON Schema with Retry (Eliminate Parsing Errors)
**Current:** Multiple fallback parsers, frequent JSON errors
**Optimized:** Function calling with Pydantic schema, automatic retry
**Impact:** 100% reliable JSON parsing, no fallback scripts
**Complexity:** High

```python
from pydantic import BaseModel
from typing import List

class SceneSchema(BaseModel):
    time: str
    narration: str
    visual_description: str

class ScriptSchema(BaseModel):
    title: str
    hook: str
    script: str
    scenes: List[SceneSchema]
    hashtags: List[str]
    description: str

# Use OpenAI function calling:
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    functions=[{
        "name": "generate_script",
        "parameters": ScriptSchema.model_json_schema()
    }],
    function_call={"name": "generate_script"}
)
```

#### 10. 🎬 Intelligent Scene Timing (Better Retention)
**Current:** Equal duration per image (4s each)
**Optimized:** Variable timing based on narration complexity
**Impact:** More natural pacing, better viewer retention
**Complexity:** High

```python
def calculate_scene_timings(self, scenes: List[Dict], audio_duration: float) -> List[float]:
    """
    Distribute time based on narration length:
    - Long narration (20+ words): 6 seconds
    - Medium narration (12-20 words): 4 seconds  
    - Short narration (<12 words): 3 seconds
    """
    timings = []
    for scene in scenes:
        word_count = len(scene['narration'].split())
        if word_count > 20:
            timings.append(6.0)
        elif word_count > 12:
            timings.append(4.0)
        else:
            timings.append(3.0)
    
    # Normalize to match audio duration
    total_time = sum(timings)
    scale_factor = audio_duration / total_time
    return [t * scale_factor for t in timings]
```

---

## 📊 Expected Results After All Optimizations

| Stage | Current | Optimized | Savings |
|-------|---------|-----------|---------|
| Image Download | 30s | 6s | **-24s** |
| Video Assembly | 70s | 35s | **-35s** |
| Voiceover + Images | 55s | 30s | **-25s** |
| Audio Processing | 5s | 3s | **-2s** |
| API Calls | 20s | 8s | **-12s** |
| **TOTAL** | **180s** | **82s** | **🎯 -98s (54% faster)** |

---

## 🔧 Implementation Roadmap

### Week 1: Quick Wins (Priority 1)
- [x] Day 1: Implement parallel image downloads
- [x] Day 2: Add FFmpeg hardware acceleration
- [x] Day 3: Batch API calls optimization
- [x] Day 4: Audio pre-normalization
- [x] Day 5: Testing and benchmarking

### Week 2: Medium Complexity (Priority 2)
- [ ] Day 1-2: Async content gathering
- [ ] Day 3: Image caching system
- [ ] Day 4: Dynamic scene count logic
- [ ] Day 5: Image pre-processing pipeline

### Week 3: Advanced Features (Priority 3)
- [ ] Day 1-2: JSON schema with function calling
- [ ] Day 3-4: Intelligent scene timing
- [ ] Day 5: Full pipeline integration testing

---

## 🎯 Monitoring & Metrics

Track these KPIs to measure optimization success:

```python
class PipelineMetrics:
    def __init__(self):
        self.metrics = {
            'image_download_time': 0,
            'video_assembly_time': 0,
            'total_pipeline_time': 0,
            'json_parse_failures': 0,
            'cache_hit_rate': 0,
            'ffmpeg_encoding_fps': 0
        }
    
    def log_stage(self, stage_name: str, duration: float):
        self.metrics[f'{stage_name}_time'] = duration
        logger.info(f"⏱️ {stage_name}: {duration:.2f}s")
```

---

## 🚨 Critical Considerations

### 1. **Hardware Acceleration Compatibility**
- Mac: Use `h264_videotoolbox`
- Linux: Use `h264_nvenc` (NVIDIA) or `h264_vaapi` (Intel/AMD)
- Windows: Use `h264_qsv` (Intel) or `h264_nvenc`

### 2. **API Rate Limits**
- SerpAPI: 100 requests/month (free), 5000/month (paid)
- ElevenLabs: 10k characters/month (free)
- OpenAI: Monitor token usage

### 3. **Memory Management**
- Pre-processing 14+ images: ~200MB RAM
- FFmpeg encoding: ~500MB-1GB RAM
- Total pipeline: Budget 2GB RAM minimum

### 4. **Error Recovery**
- Implement retry logic with exponential backoff
- Cache successful API responses
- Graceful degradation for optional features

---

## 📈 Success Metrics

**Target Performance:**
- ✅ Total pipeline < 90 seconds (from 180s)
- ✅ Image download < 10 seconds (from 30s)
- ✅ Video assembly < 40 seconds (from 70s)
- ✅ Zero JSON parsing failures
- ✅ 80%+ cache hit rate for popular topics

**Quality Metrics:**
- ✅ Maintain 1080x1920 resolution
- ✅ 30fps smooth playback
- ✅ Proper audio sync (±100ms)
- ✅ Natural scene transitions
- ✅ No visual artifacts
