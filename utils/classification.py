import google.generativeai as genai
import json
import os
from config.settings import GEMINI_API_KEY, MAP_ALIASES

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
    "temperature": 0.1,
    "top_p": 0.9,
    "max_output_tokens": 512,
}
model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)

async def classify_cs_content(media_info):
    """Use Gemini API to classify CS:GO/CS2 content using both metadata and transcript"""
    # Combine title, description, tags and transcript for analysis
    content_to_analyze = f"Title: {media_info['title']}\nDescription: {media_info['description']}"
    
    # Add transcript data if available
    if media_info.get('transcript') and media_info['transcript'].strip():
        content_to_analyze += f"\n\nTranscript of audio: {media_info['transcript']}"
    
    # Add tags with lower weight
    if media_info['tags']:
        content_to_analyze += f"\nTags: {', '.join(media_info['tags'])}"
    
    prompt = f"""
    Analyze this Counter-Strike video/reel content and identify:
    1. Which CS:GO/CS2 map it's about (must be one of: mirage, inferno, dust2, anubis, nuke, ancient, train, cache, overpass, vertigo)
    2. What type of grenade tutorial it is (smoke, flash, molotov, HE grenade, etc.)
    3. A very brief one-line description (max 60 chars) combining the map and the grenade type.
    Content to analyze:
    {content_to_analyze}
    
    Pay special attention to the transcript if available, as it likely contains the creator's explanation of what they're demonstrating.
    
    Respond in this exact JSON format:
    {{
        "map": "map_name",
        "nade_type": "grenade_type",
        "description": "description (max 60 chars)",
        "confidence": "high/medium/low"
    }}
    
    If you can't determine with at least medium confidence, use "unknown" for the map.
    Give heavy weight to the title, transcript, and description, but less to tags as they can be misleading.
    """
    
    try:
        response = model.generate_content(prompt)
        # Parse the JSON response
        response_text = response.text
        # Extract JSON if it's within code blocks or other formatting
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        print("Classification result:", result)
        
        # Standardize map name if it's a known variant
        if result['map'].lower() in MAP_ALIASES:
            result['map'] = MAP_ALIASES[result['map'].lower()]
        
        return result
    except Exception as e:
        print(f"Error classifying content: {str(e)}")
        # Return default classification on error
        return {
            "map": "unknown",
            "nade_type": "unknown",
            "description": "CS:GO/CS2 tutorial",
            "confidence": "low"
        }

def get_target_channel_id(classification, map_channels):
    """Get the target Discord channel ID based on classification"""
    if classification['map'] == "unknown" or classification['confidence'] == "low":
        return None
    
    map_name = classification['map'].lower()
    
    # Check if we have a channel for this map
    if map_name in map_channels:
        return map_channels[map_name]
    
    return None