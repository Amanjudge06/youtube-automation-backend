"""
Image Service - Clean Version
Fetches relevant images using SERP API
"""

import requests
import logging
from typing import List, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import config

logger = logging.getLogger(__name__)


class ImageService:
    """Fetch relevant images using Google Images API via SerpAPI"""
    
    def __init__(self):
        self.api_key = config.SERP_API_KEY
        self.base_url = "https://serpapi.com/search"
        self.num_images = config.IMAGE_CONFIG["num_images"]
        self.safe_search = config.IMAGE_CONFIG["safe_search"]
        self.image_type = config.IMAGE_CONFIG["image_type"]
        self.image_size = config.IMAGE_CONFIG["image_size"]
    
    def search_images(self, query: str, num_images: int = None, **kwargs) -> List[Dict]:
        """
        Search for images related to query using Google Images API
        """
        if num_images is None:
            num_images = self.num_images
        
        try:
            params = {
                "engine": "google_images",
                "q": query,
                "api_key": self.api_key,
                "hl": "en",
                "gl": "us",
                "ijn": "0",
            }
            
            logger.info(f"Searching images for: {query}")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                logger.error(f"SerpAPI error: {data['error']}")
                return []
            
            images_results = data.get("images_results", [])
            
            if not images_results:
                logger.warning(f"No images found for query: {query}")
                return []
            
            images = []
            for idx, img in enumerate(images_results[:num_images]):
                image_data = {
                    "position": img.get("position", idx + 1),
                    "url": img.get("original", ""),
                    "thumbnail": img.get("thumbnail", ""),
                    "title": img.get("title", ""),
                    "source": img.get("source", ""),
                    "width": img.get("original_width", 0),
                    "height": img.get("original_height", 0),
                }
                
                if not image_data["url"]:
                    continue
                    
                images.append(image_data)
            
            logger.info(f"Found {len(images)} images")
            return images
            
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return []
    
    def download_images(self, images: List[Dict], output_dir: Path) -> List[Path]:
        """Download images to local directory with parallel processing for 3-5x speedup"""
        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded_paths = []
        seen_urls = set()  # Track URLs to avoid duplicates
        
        # Filter out duplicate URLs upfront
        unique_images = []
        for img in images:
            url = img.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_images.append(img)
        
        logger.info(f"⚡ Downloading {len(unique_images)} images in parallel (max 5 workers)...")
        
        # Download images in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_img = {
                executor.submit(self._download_single_image, img, output_dir, idx): img 
                for idx, img in enumerate(unique_images)
            }
            
            for future in as_completed(future_to_img):
                try:
                    result = future.result(timeout=15)
                    if result:
                        downloaded_paths.append(result)
                except Exception as e:
                    logger.warning(f"Parallel download failed: {e}")
                    continue
        
        logger.info(f"✅ Downloaded {len(downloaded_paths)}/{len(unique_images)} images successfully")
        return downloaded_paths
    
    def _download_single_image(self, img: Dict, output_dir: Path, idx: int) -> Path:
        """Download a single image (used by parallel executor)"""
        try:
            url = img.get("url", "")
            if not url or url.startswith("x-raw-image://"):
                return None
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                # Skip GIFs - they cause issues with FFmpeg
                logger.debug(f"Skipping GIF image: {url[:60]}")
                return None
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg'  # default
                
                filename = f"image_{idx + 1}{ext}"
                file_path = output_dir / filename
                
            
            # Save image with unique filename
            filename = f"img_{idx}_{int(time.time())}{ext}"
            file_path = output_dir / filename
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Validate image
            if file_path.stat().st_size < 1024:  # Less than 1KB
                file_path.unlink()
                return None
            
            # Check for valid image headers
            with open(file_path, 'rb') as f:
                header = f.read(100)
            
            is_valid = False
            if header.startswith(b'\xFF\xD8\xFF'):  # JPEG
                is_valid = True
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                is_valid = True
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):  # GIF
                # Skip GIFs - remove the file
                logger.debug(f"Removing GIF file: {file_path.name}")
                file_path.unlink()
                return None
            elif b'RIFF' in header and b'WEBP' in header:  # WebP
                is_valid = True
            
            # Reject HTML error pages
            if b'<html' in header.lower() or b'<!doctype' in header.lower():
                is_valid = False
            
            if not is_valid:
                file_path.unlink()
                return None
            
            return file_path
            
        except Exception as e:
            logger.warning(f"Failed to download image {idx}: {e}")
            return None
    
    def _create_fallback_images(self, topic: str, output_dir: Path, count: int = 5) -> List[Path]:
        """Create simple colored placeholder images when real images fail to download"""
        from PIL import Image, ImageDraw, ImageFont
        
        fallback_paths = []
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
            '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'
        ]
        
        try:
            for i in range(count):
                # Create a simple colored rectangle with text
                img = Image.new('RGB', (1080, 1920), color=colors[i % len(colors)])
                draw = ImageDraw.Draw(img)
                
                # Add text
                try:
                    # Try to use a system font
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 60)
                except:
                    font = ImageFont.load_default()
                
                text = f"Video about\n{topic}"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (1080 - text_width) // 2
                y = (1920 - text_height) // 2
                
                draw.text((x, y), text, fill='white', font=font, anchor='mm')
                
                # Save the image
                filename = f"fallback_{i+1}.jpg"
                file_path = output_dir / filename
                img.save(file_path, 'JPEG', quality=85)
                
                if file_path.exists():
                    fallback_paths.append(file_path)
                    logger.info(f"Created fallback image: {filename}")
                    
        except Exception as e:
            logger.error(f"Error creating fallback images: {e}")
            
        return fallback_paths
    
    def fetch_images_for_scenes(self, topic: str, script_data: Dict, research_data: Dict = None) -> List[Path]:
        """
        Fetch topic-specific images using enhanced search with scene descriptions from script
        
        Args:
            topic: Topic string (e.g., "ole miss football")
            script_data: Script dictionary with 'scenes' array containing visual_description fields
            research_data: Optional research context
        
        Returns:
            List of downloaded image paths
        """
        logger.info(f"Fetching images for topic: {topic}")
        
        # Generate search queries from scene descriptions
        queries = self._generate_search_queries(topic, script_data, research_data)
        
        # NEW STRATEGY: One unique image per scene for true variety
        logger.info(f"🎨 Fetching unique images for {len(queries)} different scenes")
        
        all_images = []
        seen_queries = set()
        
        # Use ALL 14 scene visual descriptions for maximum variety
        for idx, query in enumerate(queries[:14]):
            # Skip duplicate queries
            if query.lower() in seen_queries:
                continue
            seen_queries.add(query.lower())
            
            try:
                # Fetch only 1-2 images per query for MORE VARIETY
                # (Better to have 14 different scenes than 6 scenes with many similar images)
                images = self.search_images(query, 1 if idx > 10 else 2)
                all_images.extend(images)
                
                logger.info(f"  Scene {idx+1}: '{query[:50]}...' → {len(images)} images")
                
                # Continue through ALL queries for maximum diversity
                # Only stop if we have way more than needed
                if len(all_images) >= 25:
                    logger.info(f"📦 Reached 25+ images, stopping to avoid duplicates")
                    break
            except Exception as e:
                logger.warning(f"Failed to search '{query[:30]}': {e}")
                continue
        
        logger.info(f"✅ Collected {len(all_images)} images from {len(seen_queries)} unique searches")
        
        if not all_images:
            logger.error("No images found for any queries")
            return []
        
        # Download images
        output_dir = Path(config.TEMP_DIR) / "images"
        downloaded_paths = self.download_images(all_images, output_dir)
        
        # If no images downloaded or too few, create fallback placeholder images
        if len(downloaded_paths) < 3:
            logger.warning(f"Only {len(downloaded_paths)} valid images downloaded. Creating fallback placeholders...")
            downloaded_paths.extend(self._create_fallback_images(topic, output_dir, 8 - len(downloaded_paths)))
        
        # Return best images for longer videos
        return downloaded_paths[:14] if len(downloaded_paths) >= 14 else downloaded_paths
    
    def _generate_search_queries(self, topic: str, script_data: Dict = None, research_data: Dict = None) -> List[str]:
        """Generate specific, varied search queries - STRICTLY TOPIC BASED (No Script Scenes)"""
        queries = []
        
        # PRIORITY 1: Topic-based queries (STRICTLY RELATED TO TOPIC)
        logger.info(f"🔍 Generating queries strictly for topic: {topic}")
        
        # Basic topic queries
        queries.append(f"{topic} high quality photo")
        queries.append(f"{topic} news image")
        
        # PRIORITY 2: Use research data for context (if available)
        if research_data and research_data.get('key_points'):
            for point in research_data['key_points'][:3]:
                if point and len(point) > 15:
                    # Extract key entities/nouns from the point instead of the whole sentence
                    # Simple heuristic: take the first few words
                    words = point.split()[:6]
                    query = ' '.join(words)
                    queries.append(query)
        
        # PRIORITY 3: Add topic-specific variations for visual diversity
        topic_lower = topic.lower()
        
        # Add varied shot types for visual diversity based on topic category
        if 'lawsuit' in topic_lower or 'legal' in topic_lower or 'controversy' in topic_lower:
            queries.extend([
                f"{topic} courtroom scene",
                f"{topic} celebrity reaction photo",
                f"{topic} dramatic news headline",
                f"{topic} paparazzi close-up photo",
                f"{topic} legal document photo"
            ])
        elif 'earthquake' in topic_lower or 'disaster' in topic_lower:
            queries.extend([
                f"{topic} damage photos",
                f"{topic} emergency response images",
                f"{topic} aftermath aerial view",
                f"{topic} rescue operation"
            ])
        elif any(term in topic_lower for term in ['vs', 'match', 'game', 'football', 'sports', 'nba', 'nfl']):
            queries.extend([
                f"{topic} match action shot",
                f"{topic} stadium wide shot",
                f"{topic} player celebration",
                f"{topic} coach sideline reaction",
                f"{topic} scoreboard final score",
                f"{topic} fans in stadium"
            ])
        elif any(term in topic_lower for term in ['movie', 'film', 'trailer', 'actor', 'actress']):
            queries.extend([
                f"{topic} movie poster",
                f"{topic} red carpet event",
                f"{topic} scene still",
                f"{topic} cast photo",
                f"{topic} premiere event"
            ])
        else:
            # Generic high-quality variations
            queries.extend([
                f"{topic} dramatic photo",
                f"{topic} close-up shot",
                f"{topic} wide angle view",
                f"{topic} action moment",
                f"{topic} event photo",
                f"{topic} press conference"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower()
            if q_lower not in seen and len(q) > 5:
                seen.add(q_lower)
                unique_queries.append(q)
        
        logger.info(f"Generated {len(unique_queries)} unique search queries based strictly on topic")
        return unique_queries[:14]  # Return top 14 queries for maximum variety