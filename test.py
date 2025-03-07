import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio
import re
from dotenv import load_dotenv

# Load environment variables from .env.local file
load_dotenv('.env.local')

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Supported URL patterns
INSTAGRAM_URL_PATTERN = r'https?://(www\.)?(instagram\.com|instagr\.am)/reel/[a-zA-Z0-9_-]+'
YOUTUBE_URL_PATTERN = r'https?://(www\.)?(youtube\.com/shorts/|youtu\.be/)[a-zA-Z0-9_-]+'

@bot.event
async def on_ready():
    print(f'Bot is logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if message contains Instagram reel URL
    instagram_urls = re.findall(INSTAGRAM_URL_PATTERN, message.content)
    if instagram_urls:
        for match in instagram_urls:
            url = match[0]  # Extract the full URL
            await download_and_send_media(message, url, 'instagram')
    
    # Check if message contains YouTube shorts URL
    youtube_urls = re.findall(YOUTUBE_URL_PATTERN, message.content)
    if youtube_urls:
        for match in youtube_urls:
            url = match[0]  # Extract the full URL
            await download_and_send_media(message, url, 'youtube')
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='download')
async def download_command(ctx, url):
    """Command to download media from a URL"""
    if re.match(INSTAGRAM_URL_PATTERN, url):
        await download_and_send_media(ctx.message, url, 'instagram')
    elif re.match(YOUTUBE_URL_PATTERN, url):
        await download_and_send_media(ctx.message, url, 'youtube')
    else:
        await ctx.send("Unsupported URL. Please provide an Instagram reel or YouTube shorts link.")

async def download_and_send_media(message, url, platform):
    """Download media from URL and send it to the channel"""
    status_message = await message.channel.send(f"Downloading {platform} content...")
    
    try:
        # Create a temporary directory for downloads
        temp_dir = 'temp_downloads'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
            'noplaylist': True,
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
        
        # Check file size
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
        
        if file_size > 8:  # Discord has an 8MB limit for regular users
            await status_message.edit(content=f"Video is too large ({file_size:.1f}MB). Discord has an 8MB upload limit.")
            return
        
        # Send the video
        await status_message.edit(content=f"Uploading {platform} content...")
        await message.channel.send(file=discord.File(video_path))
        await status_message.delete()
        
        # Clean up
        os.remove(video_path)
        
    except Exception as e:
        await status_message.edit(content=f"Error downloading {platform} content: {str(e)}")

# Replace 'YOUR_BOT_TOKEN' with your actual Discord bot token
bot.run(os.getenv('BOT_TOKEN'))

