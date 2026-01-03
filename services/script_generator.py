"""
Script Generator Service
Generates engaging YouTube Shorts scripts using AI with optimization feedback
"""

import openai
import logging
from typing import Dict, List
import config
import json
import re
from services.content_optimization_service import ContentOptimizationService

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generate YouTube Shorts scripts using OpenAI"""
    
    def __init__(self, language=None):
        openai.api_key = config.OPENAI_API_KEY
        
        # Initialize optimization service
        self.optimization_service = ContentOptimizationService()
        
        # Load optimized configuration
        self.optimized_config = self.optimization_service.get_optimized_script_config()
        
        # Use optimized parameters or fallback to config
        self.model = config.SCRIPT_CONFIG["model"]
        self.temperature = self.optimized_config.get("temperature", config.SCRIPT_CONFIG["temperature"])
        self.max_tokens = self.optimized_config.get("max_tokens", config.SCRIPT_CONFIG["max_tokens"])
        self.duration = config.SCRIPT_CONFIG["script_duration_seconds"]
        self.tone = self.optimized_config.get("tone", config.SCRIPT_CONFIG["tone"])
        self.language = language or config.SCRIPT_CONFIG["language"]
        self.hinglish_ratio = config.SCRIPT_CONFIG["hinglish_ratio"]
        
        # Optimization-specific parameters
        self.hook_style = self.optimized_config.get("hook_style", "question_based")
        self.engagement_elements = self.optimized_config.get("engagement_elements", ["What do you think?"])
        self.controversy_level = self.optimized_config.get("controversy_level", 0.3)
        self.trending_weight = self.optimized_config.get("trending_weight", 0.8)
        
        logger.info(f"Script generator initialized with optimization profile:")
        logger.info(f"  Hook style: {self.hook_style}")
        logger.info(f"  Tone: {self.tone}")
        logger.info(f"  Controversy level: {self.controversy_level}")
        logger.info(f"  Temperature: {self.temperature}")
    
    def generate_script(self, topic: Dict, research_data: Dict = None) -> Dict:
        """
        Generate a YouTube Shorts script for the given topic with research data
        
        Args:
            topic: Dictionary containing topic information
            research_data: Optional research data from Perplexity API
            
        Returns:
            Dictionary with script, storyboard, and metadata
        """
        topic_query = topic.get("query", "")
        topic_category = topic.get("category", "default")
        
        try:
            prompt = self._build_prompt(topic_query, research_data, topic_category)
            
            logger.info(f"Generating script for topic: {topic_query} (Category: {topic_category})")
            if research_data and not research_data.get("fallback"):
                logger.info("   Using Perplexity research data for enhanced script generation")
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the response
            script_data = self._parse_script_response(content, topic_query, research_data)
            
            logger.info(f"Successfully generated script with {len(script_data['scenes'])} scenes")
            return script_data
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            # Return a fallback script
            return self._generate_fallback_script(topic_query)
    
    def _build_prompt(self, topic: str, research_data: Dict = None, category: str = "default") -> str:
        """Build optimized prompt for script generation with performance-based adjustments"""
        
        # Get category-specific configuration
        category_config = config.CATEGORY_CONFIG.get(category, config.CATEGORY_CONFIG["default"])
        script_tone = category_config["script_tone"]
        image_focus = category_config["image_focus"]
        
        # Base topic information
        prompt_parts = []
        
        # Add optimization-aware hook generation
        hook_instructions = self._get_optimized_hook_instructions()
        engagement_instructions = self._get_optimized_engagement_instructions()
        
        if research_data and not research_data.get("fallback"):
            # Human-style informational prompt with research data and optimization
            prompt_parts.append(f"""I want you to write an EXTREMELY ENGAGING and FAST-PACED YouTube Shorts script with {script_tone}. This should sound like it was written by a real human content creator, NOT an AI.

Topic: "{topic}"
Category Style: {script_tone}
Target Images: {image_focus}

RESEARCH INFORMATION:
{self._format_research_for_prompt(research_data)}

{self._get_language_requirements()}

OPTIMIZATION-BASED ENGAGEMENT REQUIREMENTS (CRITICAL):
{hook_instructions}
{engagement_instructions}
- Use rapid-fire delivery: short, punchy sentences
- Include excitement words: "WAIT!", "OMG!", "INSANE!", "CRAZY!"
- Add emotional reactions: "I can't believe this!", "This is WILD!"
- Use ALL CAPS for emphasis on key words
- Create curiosity gaps: "But here's what REALLY happened..."

HUMAN-STYLE REQUIREMENTS:
- Write like you're telling friends breaking news
- Use casual, conversational language 
- Include natural speech patterns: "you know", "right?", "honestly", "look"
- Add slight hesitations and human quirks
- Use contractions: "can't", "won't", "it's", "that's"
- Include emotional reactions and personal opinions
- Make it sound spontaneous, not scripted
- Add natural filler words occasionally
- Use varied sentence lengths (short punchy + longer explanations)
- Include rhetorical questions to engage viewers
- Sound genuinely excited or surprised about the topic""")
        else:
            # Standard human-style prompt without research but with optimization
            prompt_parts.append(f"""I want you to write a YouTube Shorts script about "{topic}" that sounds like a REAL HUMAN made it, not an AI.

{self._get_language_requirements()}

OPTIMIZATION-BASED REQUIREMENTS:
{hook_instructions}
{engagement_instructions}

HUMAN AUTHENTICITY RULES:
- Talk like you're chatting with a friend
- Use natural, casual language
- Include spontaneous reactions and emotions
- Make it conversational, not formal
- Add personality and character to the voice
- Sound genuinely interested in the topic""")
        
        # Common requirements with human touch and retention optimization
        tone_description = self.tone
        if self.controversy_level > 0.5:
            tone_description += " with thought-provoking opinions that might spark debate"
        elif self.controversy_level > 0.3:
            tone_description += " with subtle controversial angles"
        
        prompt_parts.append(f"""

SCRIPT SPECIFICATIONS:
- Duration: {self.duration} seconds
- Tone: {tone_description} but NATURALLY human
- Hook Style: {self.hook_style} approach (optimized for performance)
- Make the viewer feel like they're discovering something with you
- End naturally, like how real people end conversations

RETENTION OPTIMIZATION FRAMEWORK (CRITICAL):

🎯 HOOK MASTERY (0-3 seconds):
✓ "This was hidden for years..." 
✓ "Nobody noticed this until now..."
✓ "This single mistake ended everything..."
✓ "Wait... this actually happened..."
❌ Never: "Did you know", "Today we're", "In this video"

🔄 LOOP PSYCHOLOGY (Every 2-3 seconds):
✓ "But here's what really happened..."
✓ "And then this shocked everyone..."
✓ "Wait, it gets even crazier..."
✓ "But the real story is..."

⚡ MICRO-SHOCK PHRASES:
✓ "WAIT..." → [surprised] + natural pause
✓ "This is insane!" → [excited] delivery
✓ "No way..." → [whispers] + pause
✓ "I can't believe this!" → [gasps] reaction
✓ "This changes everything!" → [urgent] tone

🎬 VISUAL RETENTION RULES (55+ SECOND VIDEO):
- New image every 4 seconds for longer content
- Each scene = DIFFERENT, SPECIFIC search term 
- Mix: Close-up → Wide shot → Action → Reaction → Detail → Wide → Close-up
- Never use generic terms like "relevant image"
- Plan for 14+ distinct visual scenes for full retention

AVOID AI DETECTION PATTERNS:
❌ "In this video, we will discuss..."
❌ "Today's topic is..."
❌ "Let's dive into..."
❌ "Without further ado..."
❌ "As we can see..."
❌ "It's important to note..."

CRITICAL: DO NOT use quotes within any text fields to avoid JSON parsing errors!
Use simple descriptive terms without quotation marks.
Also avoid backslashes (\\) and control characters.

RETENTION SCENE STRUCTURE (55+ SECONDS):
{{
    "title": "This [Shocking Thing] Changed Everything (retention-optimized title)",
    "hook": "Start mid-sentence with curiosity gap", 
    "script": "Full script with micro-shocks every 3-4 seconds",
    "scenes": [
        {{"time": "0-4s", "narration": "Hook that creates pattern interrupt", "visual_description": "specific shocking image search term"}},
        {{"time": "4-8s", "narration": "Partial reveal with new question", "visual_description": "different specific visual"}},
        {{"time": "8-12s", "narration": "Micro-shock and twist", "visual_description": "reaction or action shot"}},
        {{"time": "12-16s", "narration": "Build tension with open loop", "visual_description": "evidence or proof visual"}},
        {{"time": "16-20s", "narration": "Another shock or revelation", "visual_description": "impact or consequence image"}},
        {{"time": "20-24s", "narration": "Deep dive into details", "visual_description": "close-up detail shot"}},
        {{"time": "24-28s", "narration": "Plot twist or new information", "visual_description": "surprising visual evidence"}},
        {{"time": "28-32s", "narration": "Build to climax moment", "visual_description": "dramatic moment capture"}},
        {{"time": "32-36s", "narration": "Major revelation or shocking fact", "visual_description": "key evidence or proof"}},
        {{"time": "36-40s", "narration": "Emotional impact or reaction", "visual_description": "people reacting or celebrating"}},
        {{"time": "40-44s", "narration": "Consequences and what it means", "visual_description": "aftermath or impact visual"}},
        {{"time": "44-48s", "narration": "Future implications", "visual_description": "forward-looking imagery"}},
        {{"time": "48-52s", "narration": "Final shocking detail", "visual_description": "most compelling visual"}},
        {{"time": "52-56s", "narration": "Rewatch hook ending with call to action", "visual_description": "compelling final image"}}
    ],
    "hashtags": ["#topic related", "#trending", "#viral", "#shocking", "#mustwatch"],
    "description": "Retention-focused description with curiosity gaps"
}}

RETENTION TARGET: Make viewers watch multiple times and unable to scroll away.
Create addictive content that demands attention every single second.""")
        
        return "".join(prompt_parts)
    
    def _get_optimized_hook_instructions(self) -> str:
        """Generate hook instructions based on optimization profile"""
        if self.hook_style == "shocking":
            return """- START with a SHOCKING statement that makes viewers stop scrolling
- Use phrases like "You won't believe what just happened..." or "This will blow your mind..."
- Create immediate shock value without clickbait"""
        elif self.hook_style == "curiosity":
            return """- START with a curiosity gap that demands an answer
- Use phrases like "The secret everyone's talking about..." or "What they don't want you to know..."
- Build mystery from the first second"""
        else:  # question_based
            return """- START with a compelling question that viewers want answered
- Use direct questions like "Did you know..." or "What if I told you..."
- Make the question irresistible to ignore"""
    
    def _get_optimized_engagement_instructions(self) -> str:
        """Generate engagement instructions based on optimization profile"""
        instructions = []
        
        # Add performance-optimized engagement elements
        if self.engagement_elements:
            sample_elements = ", ".join(self.engagement_elements[:3])
            instructions.append(f"- Include high-performing engagement phrases like: {sample_elements}")
        
        # Add controversy-based instructions
        if self.controversy_level > 0.6:
            instructions.append("- Include bold opinions that might spark debate")
            instructions.append("- Ask provocative questions that demand viewer response")
        elif self.controversy_level > 0.3:
            instructions.append("- Add subtle opinion-based statements")
            instructions.append("- Include gentle discussion-starters")
        
        # Add call-to-action frequency
        instructions.append("- End with strong call-to-action for engagement")
        instructions.append("- Use phrases optimized for YouTube algorithm")
        
        return "\n".join(instructions)

    def get_optimization_status(self) -> Dict:
        """Get current optimization status and parameters"""
        return {
            "optimization_active": True,
            "hook_style": self.hook_style,
            "engagement_level": len(self.engagement_elements),
            "controversy_level": self.controversy_level,
            "temperature": self.temperature,
            "tone": self.tone,
            "last_optimization": self.optimization_service.current_optimization_profile.get("last_updated")
        }
    
    def _format_research_for_prompt(self, research_data: Dict) -> str:
        """Format research data for inclusion in the prompt - simplified"""
        try:
            # Get the main research content
            full_research = research_data.get("full_research", "")
            
            if full_research:
                # Return just the core research information
                return f"Research findings: {full_research[:500]}..."
            else:
                return "Research data available"
            
        except Exception as e:
            logger.warning(f"Error formatting research data: {e}")
            return f"Research available for topic: {research_data.get('topic', 'Unknown')}"
    
    def _parse_script_response(self, content: str, topic: str, research_data: Dict = None) -> Dict:
        """Parse AI response into structured format with enhanced error handling"""
        try:
            # Try to parse as JSON first
            if "{" in content and "}" in content:
                # Extract JSON from response (handle code blocks)
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                
                # Clean up common JSON formatting issues
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                
                # Debug logging
                logger.debug(f"Attempting to parse JSON (first 300 chars): {json_str[:300]}")
                
                try:
                    script_data = json.loads(json_str)
                except json.JSONDecodeError as json_error:
                    # Try to fix common JSON issues
                    logger.warning(f"Initial JSON parse failed: {json_error}")
                    
                    # Log the problematic section around the error
                    error_char = getattr(json_error, 'pos', 0)
                    start_debug = max(0, error_char - 50)
                    end_debug = min(len(json_str), error_char + 50)
                    logger.warning(f"Error context: ...{json_str[start_debug:end_debug]}...")
                    
                    # Try to fix multiple common JSON issues
                    fixed_json = json_str
                    
                    # Fix trailing commas before closing braces/brackets
                    fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                    
                    # Fix multiple commas
                    fixed_json = re.sub(r',(\s*,)+', r',', fixed_json)
                    
                    # Fix unescaped quotes within string values - more robust approach
                    # This finds strings and escapes internal quotes
                    def fix_quotes_in_strings(text):
                        # Pattern to find JSON string values
                        import re
                        def quote_fixer(match):
                            key_part = match.group(1)  # Everything before the colon
                            value_part = match.group(2)  # The string value
                            # Escape any unescaped quotes in the value
                            fixed_value = re.sub(r'(?<!\\)"', r'\\"', value_part)
                            return f'{key_part}"{fixed_value}"'
                        
                        # Match "key": "value with potential unescaped quotes"
                        pattern = r'("(?:[^"\\]|\\.)*"\s*:\s*)"([^"]*(?:"[^"]*)*)"'
                        return re.sub(pattern, quote_fixer, text)
                    
                    fixed_json = fix_quotes_in_strings(fixed_json)
                    
                    # Alternative approach: Replace problematic quotes with safer characters
                    # Find all string values and replace internal quotes with apostrophes
                    def replace_internal_quotes(match):
                        full_match = match.group(0)
                        if full_match.count('"') > 2:  # More than just opening and closing quotes
                            # Replace middle quotes with apostrophes
                            parts = full_match.split('"')
                            if len(parts) > 2:
                                # Keep first and last quotes, replace middle ones
                                middle = '"'.join(parts[1:-1]).replace('"', "'")
                                return f'"{middle}"'
                        return full_match
                    
                    # Match string values in JSON
                    fixed_json = re.sub(r'"[^"]*"(?=\s*[,}\]])', replace_internal_quotes, fixed_json)
                    
                    try:
                        script_data = json.loads(fixed_json)
                        logger.info("Successfully fixed and parsed JSON after error correction")
                    except json.JSONDecodeError as final_error:
                        logger.error(f"Could not fix JSON: {final_error}")
                        logger.error(f"Final JSON attempt (first 500 chars): {fixed_json[:500]}")
                        
                        # Last resort: Try to extract data using pattern matching
                        logger.info("Attempting pattern-based extraction as last resort")
                        
                        title_match = re.search(r'"title"\s*:\s*"([^"]*)"', content)
                        script_match = re.search(r'"script"\s*:\s*"([^"]*)"', content)
                        
                        if title_match and script_match:
                            logger.info("Successfully extracted data using pattern matching")
                            # Create a basic structure from pattern matches
                            extracted_data = {
                                "title": title_match.group(1),
                                "hook": script_match.group(1)[:100],
                                "script": script_match.group(1),
                                "scenes": [
                                    {
                                        "time": "0-30s",
                                        "narration": script_match.group(1),
                                        "visual_description": f"relevant images for {topic}"
                                    }
                                ],
                                "hashtags": [f"#{topic.replace(' ', '')}"],
                                "description": f"About {topic}"
                            }
                            return extracted_data
                        
                        # Final fallback to plain text parsing
                        return self._parse_plain_text_script(content, topic, research_data)
                
                # Validate and extract the actual script content
                if "script" in script_data:
                    actual_script = script_data["script"]
                    
                    # If scenes exist, extract narration from scenes instead
                    if "scenes" in script_data and script_data["scenes"]:
                        # Build script from scenes narration
                        narration_parts = []
                        for scene in script_data["scenes"]:
                            if "narration" in scene and scene["narration"]:
                                # Skip JSON structure elements
                                narration = scene["narration"]
                                if not any(x in narration for x in ['"title":', '"hook":', '"script":', '"scenes":', '{"time":']):
                                    narration_parts.append(narration)
                        
                        if narration_parts:
                            actual_script = " ".join(narration_parts)
                            script_data["script"] = actual_script
                
                # Ensure all required fields exist
                script_data.setdefault("title", f"Breaking: {topic}")
                script_data.setdefault("hook", script_data.get("script", "")[:100])
                script_data.setdefault("scenes", [])
                script_data.setdefault("hashtags", [f"#{topic.replace(' ', '')}"])
                script_data.setdefault("description", topic)
                
                logger.info(f"Successfully parsed JSON response with {len(script_data.get('scenes', []))} scenes")
                return script_data
            else:
                # Fallback: parse as plain text
                logger.warning("No JSON structure found in response, using plain text parser")
                return self._parse_plain_text_script(content, topic, research_data)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON response: {e}, using plain text parser")
            return self._parse_plain_text_script(content, topic, research_data)
    
    def _parse_plain_text_script(self, content: str, topic: str, research_data: Dict = None) -> Dict:
        """Parse plain text script into structured format"""
        lines = content.strip().split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        
        # Filter out JSON structure elements and code blocks
        filtered_lines = []
        for line in lines:
            # Skip JSON structure elements
            if any(x in line for x in ['"title":', '"hook":', '"script":', '"scenes":', '"hashtags":', '"description":', '```json', '```', '{"time":', '},']):
                continue
            # Skip lines that are just JSON syntax
            if line in ['{', '}', '[', ']', '],']:
                continue
            # Skip lines that start with JSON field indicators
            if line.startswith('"') and '":' in line:
                continue
            
            filtered_lines.append(line)
        
        # If no valid content lines found, create a script based on research data if available
        if not filtered_lines:
            # Try to create script from research data first
            if research_data and research_data.get("full_research"):
                research_summary = research_data.get("full_research", "")
                key_points = research_data.get("key_points", [])
                
                if self.language == "hinglish":
                    # Create research-based Hinglish content
                    hook = f"Dosto, maine {topic} ke baare mein kuch research kiya hai aur sach mein shocking news mila hai!"
                    
                    if key_points:
                        # Use first key point for main content
                        main_point = key_points[0] if len(key_points) > 0 else ""
                        filtered_lines = [
                            hook,
                            f"Dekho yaar, {main_point}",
                            "Aur ye sirf shururat hai! Comments mein batao ki aap kya sochte hain!"
                        ]
                    else:
                        # Use research summary
                        summary_snippet = research_summary[:150] + "..." if len(research_summary) > 150 else research_summary
                        filtered_lines = [
                            hook,
                            f"Research ke according, {summary_snippet}",
                            "Interesting hai na? Comments mein batayiye!"
                        ]
                else:
                    # Create research-based English content
                    hook = f"Okay guys, I did some research on {topic} and what I found is actually crazy!"
                    
                    if key_points:
                        main_point = key_points[0] if len(key_points) > 0 else ""
                        filtered_lines = [
                            hook,
                            f"So basically, {main_point}",
                            "And that's just the beginning! Let me know what you think!"
                        ]
                    else:
                        summary_snippet = research_summary[:150] + "..." if len(research_summary) > 150 else research_summary
                        filtered_lines = [
                            hook,
                            f"According to my research, {summary_snippet}",
                            "Pretty interesting, right? Tell me what you think!"
                        ]
            else:
                # Basic fallback without research data
                if self.language == "hinglish":
                    # Create Hinglish fallback content
                    filtered_lines = [
                        f"Dosto, suno! {topic} ke baare mein latest news aaya hai aur main aapko batana chahta hun.",
                        "Yaar, yeh sach mein interesting hai jab aap iske baare mein sochte hain.",
                        "Comments mein batayiye ki aap kya sochte hain!"
                    ]
                else:
                    # English fallback
                    filtered_lines = [
                        f"Hey everyone! So {topic} is trending right now and I had to tell you about this.",
                        "This is actually pretty interesting when you think about it.",
                        "Let me know what you think in the comments below!"
                    ]
        
        # Create scenes from filtered content
        scenes = []
        time_per_scene = max(1, self.duration // len(filtered_lines))
        
        for idx, line in enumerate(filtered_lines[:6]):  # Limit to 6 scenes max
            start = idx * time_per_scene
            end = min(start + time_per_scene, self.duration)
            scenes.append({
                "time": f"{start}-{end}s",
                "narration": line,
                "visual_description": f"Relevant image for: {topic}"
            })
        
        return {
            "title": f"Breaking: {topic}",
            "hook": filtered_lines[0] if filtered_lines else topic,
            "script": " ".join(filtered_lines),
            "scenes": scenes,
            "hashtags": [f"#{topic.replace(' ', '')}", "#Shorts", "#Trending"],
            "description": f"Everything you need to know about {topic}! #Shorts"
        }
    
    def _generate_fallback_script(self, topic: str) -> Dict:
        """Generate a human-style fallback script if AI fails"""
        script_text = f"Wait, did you guys hear about {topic}? Okay so this is actually trending right now and honestly, I can't believe this happened. Let me break this down for you real quick 'cause this is wild. Anyway, let me know what you think in the comments!"
        
        return {
            "title": f"This {topic} situation is INSANE",
            "hook": f"Wait, did you guys hear about {topic}?",
            "script": script_text,
            "scenes": [
                {
                    "time": "0-15s",
                    "narration": f"Wait, did you guys hear about {topic}? Okay so this is actually trending right now and honestly, I can't believe this happened.",
                    "visual_description": f"breaking news headlines about {topic}"
                },
                {
                    "time": "15-30s",
                    "narration": "Let me break this down for you real quick 'cause this is wild. Anyway, let me know what you think in the comments!",
                    "visual_description": f"social media reactions to {topic}"
                }
            ],
            "hashtags": [f"#{topic.replace(' ', '').lower()}", "#viral", "#trending", "#breaking"],
            "description": f"The {topic} situation is absolutely crazy - here's what's happening right now 👀"
        }
    
    def optimize_for_virality(self, topic: str) -> float:
        """
        Score a topic for potential virality (0-1 scale)
        
        Args:
            topic: Topic to score
            
        Returns:
            Virality score between 0 and 1
        """
        try:
            prompt = f"""Rate this topic's potential to go viral on YouTube Shorts (0-10 scale):

Topic: "{topic}"

Consider:
- Controversy level
- Current relevance
- Emotional appeal
- Shareability
- Broad appeal

Respond with ONLY a number between 0 and 10."""
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for scoring
                messages=[
                    {"role": "system", "content": "You are a viral content expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10,
            )
            
            score_text = response.choices[0].message.content.strip()
            score = float(score_text) / 10.0  # Normalize to 0-1
            
            logger.info(f"Virality score for '{topic}': {score:.2f}")
            return score
            
        except Exception as e:
            logger.error(f"Error scoring topic: {e}")
            return 0.5  # Default middle score

    def _get_system_prompt(self) -> str:
        """Get system prompt optimized for YouTube Shorts retention"""
        base_prompt = f"""You are an expert YouTube Shorts script writer specializing in MAXIMUM RETENTION optimization.

CRITICAL RETENTION RULES (NON-NEGOTIABLE):

1️⃣ FIRST 1.5 SECONDS DECIDE EVERYTHING:
- Never start with "Did you know", "Today we're talking about", "This video..."
- Start MID-SENTENCE or MID-ACTION
- Create PATTERN INTERRUPT + CURIOSITY GAP instantly
- Examples: "This was hidden for years...", "Nobody noticed this until now...", "This single mistake ended everything..."

2️⃣ NEVER LET VIEWER FEEL "COMPLETE" TOO EARLY:
- Open loops every 2-3 seconds
- Structure: Question → partial answer → new question → twist
- Use phrases like "but here's the crazy part...", "wait, it gets worse...", "and then this happened..."

3️⃣ INFORMATION SPEED RAMPING:
- 0-3s: Very fast, chaotic, curiosity-driven
- 3-7s: Slightly slower, explanation begins  
- 7-15s: Fast again (twists, reveals)
- Last 3s: Cliffhanger or payoff that makes them want to rewatch

4️⃣ MICRO-SHOCKS EVERY 3-4 SECONDS:
- "WAIT", "OMG", "INSANE", "CRAZY"
- Sudden emotional shifts
- Record scratch moments
- One-word emphasis: "LIE.", "FAKE.", "EXPOSED."

5️⃣ HUMAN SPEECH PATTERNS (NOT AI):
- Use: "Look", "honestly", "you guys", "right?", "I can't believe"
- Include natural hesitations: "...and uh...", "so basically..."
- Emotional reactions: "This is WILD!", "I'm literally shook"
- Contractions: "can't", "won't", "it's", "that's"

6️⃣ VISUAL DESCRIPTIONS FOR RETENTION:
- Change image every 1-1.5 seconds
- Specific, searchable terms (not generic)
- Mix: Wide → close-up → reaction → detail
- Each scene needs DIFFERENT image search term

7️⃣ END FOR REWATCH VALUE:
- End with "Watch again and notice..."
- Create revelation that makes beginning hit different
- Or end mid-sentence for loop effect

DURATION: {self.duration} seconds
RETENTION TARGET: 80%+ average view duration

Generate scripts that feel like a real person discovered breaking news and urgently wants to share it with friends."""
        
        if self.language == "hinglish":
            return f"""{base_prompt} 

IMPORTANT LANGUAGE REQUIREMENT: 
You create content for Indian audiences using HINGLISH (Hindi + English mix). 

HINGLISH RETENTION OPTIMIZATION:
- Mix approximately {int(self.hinglish_ratio * 100)}% Hindi words naturally into English sentences
- Use common Hindi words that create emotional connection: "yaar", "bhai", "dekho", "sach mein", "pagal"
- Include Hindi expressions for shock value: "Are yaar", "Kya baat hai!", "Bilkul pagal!", "Dekho guys"
- Use Hindi reactions for micro-shocks: "Waah!", "Kya!", "Yeh toh amazing hai!", "Sach mein pagal hai"
- Keep sentence structure English but sprinkle Hindi words for rhythm and retention

RETENTION-OPTIMIZED HINGLISH PHRASES:
✓ "Yaar, dekho yeh kitna crazy hai!" (Hook with curiosity)
✓ "Are bhai, wait... yeh toh bilkul shocking hai!" (Micro-shock)
✓ "Sach mein? Main believe nahi kar sakta!" (Emotional reaction) 
✓ "Dekho guys, ab main bataunga real story..." (Information teasing)
✓ "Yaar seriously, yeh dekh ke main shocked hu!" (Personal reaction)

Make it sound like how young Indians actually talk when they're excited about breaking news."""
        
        else:
            return f"""{base_prompt}

You use casual, retention-optimized English with natural speech patterns, contractions, and explosive emotions. 
Your goal is maximum viewer retention through psychological engagement techniques."""

    def _get_language_requirements(self) -> str:
        """Get language-specific requirements for the prompt"""
        if self.language == "hinglish":
            return f"""HINGLISH LANGUAGE REQUIREMENTS:
- Create script in HINGLISH (Hindi + English mix) for Indian audiences
- Use approximately {int(self.hinglish_ratio * 100)}% Hindi words mixed with English
- Include popular Hindi expressions: "yaar", "bhai", "dekho", "sach mein", "kya baat hai"
- Use Hindi reactions: "Waah!", "Are yaar!", "Bilkul!", "Pagal hai!"
- Keep main structure English but naturally include Hindi words
- Sound like how young Indians actually speak - trendy, casual Hinglish
- Examples: "Yaar yeh toh amazing hai!", "Dekho guys kya hua", "Sach mein? Kya baat hai!"

AVOID:
- Formal Hindi or overly traditional language
- Pure Hindi sentences (keep mixing with English)
- Forced or unnatural Hindi word placement"""
        
        else:
            return """ENGLISH LANGUAGE REQUIREMENTS:
- Use natural, casual English 
- Include modern slang and expressions
- Sound conversational and relatable"""
