import os
import json
import re
import discord

# Function to read secrets from Docker secrets files
def read_secret(file_path):
    """Reads a secret from a file"""
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Load bot secrets from Docker Secrets
BOT_TOKEN = read_secret(os.getenv("BOT_TOKEN_FILE", "/run/secrets/bot_token"))
GEMINI_API_KEY = read_secret(os.getenv("GEMINI_API_KEY_FILE", "/run/secrets/gemini_api_key"))

# Bot configuration
COMMAND_PREFIX = '!'

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

# Ensure BOT_TOKEN is loaded
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing!")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing!")

print("Bot is starting...")
