import os
from dotenv import load_dotenv
import json
import re
import discord

# Load environment variables
load_dotenv('.env.local')

# Bot configuration
COMMAND_PREFIX = '!'
BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# URL patterns
INSTAGRAM_URL_PATTERN = r'(https?://(www\.)?(instagram\.com|instagr\.am)/reel/[a-zA-Z0-9_-]+\S*)'
YOUTUBE_URL_PATTERN = r'(https?://(www\.)?(youtube\.com/shorts/|youtu\.be/)[a-zA-Z0-9_-]+\S*)'

# Temp directory for downloads
TEMP_DIR = 'temp_downloads'

# Load map channels from JSON file
with open('channels.json', 'r') as f:
    MAP_CHANNELS = json.load(f)

# Map name variants to standardized names
MAP_ALIASES = {
    # Mirage variants
    'mirage': 'mirage',
    'de_mirage': 'mirage',
    
    # Inferno variants
    'inferno': 'inferno',
    'de_inferno': 'inferno',
    
    # [... rest of the map aliases ...]
}

# Known nade types
NADE_TYPES = [
    'smoke', 'flash', 'flashbang', 'molotov', 'molly', 'incendiary', 'he', 'grenade', 
    'decoy', 'nade', 'lineup', 'one way', 'pop flash', 'popflash'
]

# Discord intents
def get_discord_intents():
    intents = discord.Intents.default()
    intents.message_content = True
    return intents