"""
Enhanced Image Service with Multiple Sources and Visual Deduplication
- SerpAPI Google Images
- Pexels API
- Unsplash API
- Wikipedia/Wikimedia
- Perceptual hashing for visual similarity
"""

import requests
import logging
import re
from typing import List, Dict, Set, Tuple
from pathlib import Path
from PIL import Image
import imagehash
import config

logger = logging.getLogger(__name__)


class EnhancedImageService:
    """Advanced image fetching with multiple sources and visual deduplication"""
    
    def __init__(self):
        self.serp_api_key = config.SERP_API_KEY
        self.pexels_api_key = config.PEXELS_API_KEY
        self.unsplash_api_key = config.UNSPLASH_ACCESS_KEY
        self.num_images = 14
        
        # Track hashes for deduplication
        self.file_hashes: Set[str] = set()
        self.visual_hashes: List = []
    
    def extract_entities_from_topic(self, topic: str) -> List[str]:
        """
        Extract person names and key entities from topic
        Simple approach: Capitalize words that look like names
        """
        entities = []
        
        # Common patterns for celebrity names
        words = topic.split()
        
        # Look for capitalized consecutive words (likely names)
        i = 0
        while i < len(words):
            if words[i][0].isupper() and len(words[i]) > 2:
                # Check if next word is also capitalized (full name)
                if i + 1 < len(words) and words[i + 1][0].isupper() and len(words[i + 1]) > 2:
                    full_name = f"{words[i]} {words[i + 1]}"
                    entities.append(full_name)
                    i += 2
                else:
                    entities.append(words[i])
                    i += 1
            else:
                i += 1
        
        logger.info(f"Extracted entities: {entities}")
        return entities
    
    def extract_movie_name(self, text: str) -> str:
        """Extract movie title from text"""
        # Look for common movie patterns
        patterns = [
            r"'([^']+)'",  # 'Movie Name'
            r'"([^"]+)"',  # "Movie Name"
            r"\*([^*]+)\*",  # *Movie Name*
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def generate_smart_queries(self, topic: str, research_data: Dict = None, script_data: Dict = None) -> List[str]:
        """
        Generate intelligent, specific search queries based on topic and research
        """
        queries = []
        entities = self.extract_entities_from_topic(topic)
        
        # Tier 1: Direct person searches (most specific)
        for entity in entities[:2]:  # First 2 entities (usually main subjects)
            queries.extend([
                f"{entity} professional photo 2024",
                f"{entity} high quality portrait",
                f"{entity} red carpet event photo",
                f"{entity} official press photo",
            ])
        
        # Tier 2: Context from research data
        if research_data:
            summary = research_data.get('summary', '')
            
            # Check for movie/show
            if any(word in summary.lower() for word in ['movie', 'film', 'show', 'series']):
                movie_name = self.extract_movie_name(summary)
                if movie_name:
                    queries.extend([
                        f"{movie_name} official poster",
                        f"{movie_name} movie still high quality",
                        f"{movie_name} film promotional image"
                    ])
            
            # Check for events
            if 'premiere' in summary.lower():
                queries.append(f"{entities[0]} premiere event photo")
            if 'awards' in summary.lower():
                queries.append(f"{entities[0]} awards ceremony photo")
        
        # Tier 3: Topic-specific (lawsuit, controversy, etc.)
        topic_lower = topic.lower()
        if 'lawsuit' in topic_lower or 'legal' in topic_lower:
            queries.extend([
                f"{entities[0]} court appearance photo",
                f"{entities[0]} legal battle news image",
                "celebrity lawsuit courtroom photo"
            ])
        elif 'scandal' in topic_lower or 'controversy' in topic_lower:
            queries.extend([
                f"{entities[0]} paparazzi photo candid",
                f"{entities[0]} entertainment news photo"
            ])
        
        # Tier 4: Social media and news screenshots
        queries.extend([
            f"{topic} news headline screenshot",
            f"{entities[0]} social media post",
            f"{topic} trending news photo"
        ])
        
        # Tier 5: Fallback variety
        queries.extend([
            f"Hollywood {entities[0]} photograph",
            f"{topic} entertainment industry",
            f"{entities[0]} celebrity lifestyle"
        ])
        
        # Remove duplicates while preserving order
        unique_queries = []
        for q in queries:
            if q and len(q) > 10 and q not in unique_queries:
                unique_queries.append(q)
        
        logger.info(f"Generated {len(unique_queries)} smart queries")
        return unique_queries[:20]  # Top 20 most specific
    
    def search_serp_api(self, query: str, num: int = 3) -> List[Dict]:
        """Search Google Images via SerpAPI"""
        try:
            params = {
                "engine": "google_images",
                "q": query,
                "api_key": self.serp_api_key,
                "num": num,
                "hl": "en",
                "gl": "us"
            }
            
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            images = []
            for img in data.get("images_results", [])[:num]:
                # Filter out stock photo sites
                source = img.get("source", "").lower()
                if any(blocked in source for blocked in ['shutterstock', 'istockphoto', 'gettyimages', 'dreamstime']):
                    continue
                
                images.append({
                    "url": img.get("original", ""),
                    "thumbnail": img.get("thumbnail", ""),
                    "source": "serp",
                    "title": img.get("title", "")
                })
            
            return images
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []
    
    def search_pexels(self, query: str, num: int = 3) -> List[Dict]:
        """Search Pexels API for high-quality free photos"""
        if not self.pexels_api_key:
            return []
        
        try:
            headers = {"Authorization": self.pexels_api_key}
            params = {"query": query, "per_page": num, "orientation": "portrait"}
            
            response = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            images = []
            for photo in data.get("photos", []):
                images.append({
                    "url": photo["src"]["large2x"],
                    "thumbnail": photo["src"]["medium"],
                    "source": "pexels",
                    "title": query
                })
            
            logger.info(f"Pexels: Found {len(images)} images for '{query}'")
            return images
        except Exception as e:
            logger.warning(f"Pexels search failed: {e}")
            return []
    
    def search_unsplash(self, query: str, num: int = 3) -> List[Dict]:
        """Search Unsplash API for professional photography"""
        if not self.unsplash_api_key:
            return []
        
        try:
            params = {
                "query": query,
                "per_page": num,
                "orientation": "portrait",
                "client_id": self.unsplash_api_key
            }
            
            response = requests.get(
                "https://api.unsplash.com/search/photos",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            images = []
            for photo in data.get("results", []):
                images.append({
                    "url": photo["urls"]["regular"],
                    "thumbnail": photo["urls"]["thumb"],
                    "source": "unsplash",
                    "title": query
                })
            
            logger.info(f"Unsplash: Found {len(images)} images for '{query}'")
            return images
        except Exception as e:
            logger.warning(f"Unsplash search failed: {e}")
            return []
    
    def search_all_sources(self, query: str) -> List[Dict]:
        """Search all available image sources"""
        all_images = []
        
        # Source 1: SerpAPI (primary)
        serp_images = self.search_serp_api(query, 3)
        all_images.extend(serp_images)
        
        # Source 2: Pexels (high quality stock)
        pexels_images = self.search_pexels(query, 2)
        all_images.extend(pexels_images)
        
        # Source 3: Unsplash (professional photography)
        unsplash_images = self.search_unsplash(query, 2)
        all_images.extend(unsplash_images)
        
        return all_images
    
    def calculate_visual_hash(self, img_path: Path) -> imagehash.ImageHash:
        """Calculate perceptual hash of image"""
        try:
            img = Image.open(img_path)
            # Use average hash for speed, dhash for better accuracy
            return imagehash.average_hash(img, hash_size=8)
        except Exception as e:
            logger.warning(f"Failed to hash image {img_path}: {e}")
            return None
    
    def is_visually_similar(self, img_path: Path, threshold: int = 8) -> bool:
        """Check if image is visually similar to already downloaded images"""
        try:
            new_hash = self.calculate_visual_hash(img_path)
            if not new_hash:
                return False
            
            for existing_hash in self.visual_hashes:
                difference = new_hash - existing_hash
                if difference < threshold:
                    logger.info(f"Image visually similar (diff={difference}), skipping")
                    return True
            
            self.visual_hashes.append(new_hash)
            return False
        except Exception as e:
            logger.warning(f"Visual similarity check failed: {e}")
            return False
    
    def download_images(self, images: List[Dict], output_dir: Path) -> List[Path]:
        """Download images with visual deduplication"""
        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded_paths = []
        
        for idx, img in enumerate(images):
            try:
                url = img.get("url", "")
                if not url or url.startswith("x-raw-image://"):
                    continue
                
                # Skip duplicate URLs
                if url in self.file_hashes:
                    logger.info(f"Duplicate URL, skipping")
                    continue
                self.file_hashes.add(url)
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                response = requests.get(url, headers=headers, timeout=15, stream=True)
                response.raise_for_status()
                
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'
                
                filename = f"image_{idx + 1}{ext}"
                file_path = output_dir / filename
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Validate file size
                if file_path.stat().st_size < 5120:  # Less than 5KB is suspicious
                    file_path.unlink()
                    logger.warning(f"File too small: {filename}")
                    continue
                
                # Validate image format
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(100)
                    
                    is_valid = False
                    if header.startswith(b'\xFF\xD8\xFF'):  # JPEG
                        is_valid = True
                    elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                        is_valid = True
                    elif b'RIFF' in header and b'WEBP' in header:  # WebP
                        is_valid = True
                    
                    if b'<html' in header.lower() or b'<!doctype' in header.lower():
                        is_valid = False
                    
                    if not is_valid:
                        file_path.unlink()
                        logger.warning(f"Invalid image format: {filename}")
                        continue
                except Exception as e:
                    file_path.unlink()
                    logger.warning(f"Error validating image: {e}")
                    continue
                
                # Check visual similarity (perceptual hash)
                if self.is_visually_similar(file_path, threshold=8):
                    file_path.unlink()
                    continue
                
                # FFprobe validation
                try:
                    import subprocess
                    result = subprocess.run([
                        'ffprobe', '-v', 'quiet', '-print_format', 'json',
                        '-show_format', str(file_path)
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        downloaded_paths.append(file_path)
                        logger.info(f"✅ Downloaded: {filename} (source: {img.get('source', 'unknown')})")
                    else:
                        file_path.unlink()
                        logger.warning(f"FFprobe validation failed: {filename}")
                except:
                    # If ffprobe fails but other checks passed, keep it
                    downloaded_paths.append(file_path)
                    logger.info(f"✅ Downloaded: {filename} (ffprobe skipped)")
                
            except Exception as e:
                logger.warning(f"Failed to download image {idx + 1}: {e}")
                continue
        
        return downloaded_paths
    
    def fetch_images_for_scenes(self, scenes: List[Dict], topic: str, research_data: Dict = None, script_data: Dict = None) -> List[Path]:
        """
        Main method: Fetch diverse, relevant images using multi-source strategy
        """
        logger.info(f"🎯 Fetching high-quality images for: {topic}")
        
        # Reset hashes for new fetch
        self.file_hashes = set()
        self.visual_hashes = []
        
        # Generate smart queries
        queries = self.generate_smart_queries(topic, research_data, script_data)
        
        # Search all sources
        all_images = []
        for query in queries:
            images = self.search_all_sources(query)
            all_images.extend(images)
            
            if len(all_images) >= 50:  # Collect pool of 50 candidates
                break
        
        logger.info(f"📊 Collected {len(all_images)} candidate images from all sources")
        
        # Download with visual deduplication
        output_dir = Path(config.TEMP_DIR) / "images"
        downloaded_paths = self.download_images(all_images, output_dir)
        
        logger.info(f"✅ Downloaded {len(downloaded_paths)} unique, visually diverse images")
        
        # Return best 14 images
        return downloaded_paths[:14] if len(downloaded_paths) >= 14 else downloaded_paths
