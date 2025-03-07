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

# Supported URL patterns - updated to capture the full URL
INSTAGRAM_URL_PATTERN = r'(https?://(www\.)?(instagram\.com|instagr\.am)/reel/[a-zA-Z0-9_-]+\S*)'
YOUTUBE_URL_PATTERN = r'(https?://(www\.)?(youtube\.com/shorts/|youtu\.be/)[a-zA-Z0-9_-]+\S*)'

@bot.event
async def on_ready():
    print(f'Bot is logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    should_delete_message = False
    
    # Check if message contains Instagram reel URL
    instagram_matches = re.findall(INSTAGRAM_URL_PATTERN, message.content)
    if instagram_matches:
        for match in instagram_matches:
            # The first element of the tuple is the full URL
            url = match[0]  # Extract the full URL from the tuple
            await download_and_send_media(message, url, 'instagram')
            should_delete_message = True
    
    # Check if message contains YouTube shorts URL
    youtube_matches = re.findall(YOUTUBE_URL_PATTERN, message.content)
    if youtube_matches:
        for match in youtube_matches:
            # The first element of the tuple is the full URL
            url = match[0]  # Extract the full URL from the tuple
            await download_and_send_media(message, url, 'youtube')
            should_delete_message = True
    
    # Delete the original message if it contained a valid URL
    if should_delete_message:
        try:
            await message.delete()
        except discord.errors.Forbidden:
            # Bot doesn't have permission to delete messages
            print(f"Cannot delete message in {message.channel.name}: Missing permissions")
    
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
        
        # Configure yt-dlp options with lower quality preference
        ydl_opts = {
            # Prefer lower quality formats to stay under Discord's 8MB limit
            'format': 'worst[ext=mp4]/bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[ext=mp4]/best',
            'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
            'noplaylist': True,
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            
            # Log media information to console
            print("\n=== MEDIA INFORMATION ===")
            print(f"Platform: {platform}")
            print(f"URL: {url}")
            
            # Title
            title = info.get('title', 'No title available')
            print(f"Title: {title}")
            
            # Description
            description = info.get('description', 'No description available')
            print(f"Description: {description}")
            
            # Tags/Categories
            tags = info.get('tags', [])
            categories = info.get('categories', [])
            
            if tags:
                print(f"Tags: {', '.join(tags)}")
            else:
                print("Tags: None")
                
            if categories:
                print(f"Categories: {', '.join(categories)}")
            else:
                print("Categories: None")
                
            # Additional useful info
            uploader = info.get('uploader', 'Unknown')
            print(f"Uploader: {uploader}")
            
            duration = info.get('duration')
            if duration:
                minutes, seconds = divmod(int(duration), 60)
                print(f"Duration: {minutes}:{seconds:02d}")
            
            print("========================\n")
        
        # Check file size
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
        
        if file_size > 8:  # Discord has an 8MB limit for regular users
            # Try to compress the video if it's still too large
            await status_message.edit(content=f"Video is large ({file_size:.1f}MB). Attempting to compress...")
            
            # Start with a moderate compression level
            crf_values = [23, 28, 32, 36, 40, 44]
            success = False
            
            for crf in crf_values:
                compressed_path = f"{temp_dir}/compressed_crf{crf}_{os.path.basename(video_path)}"
                
                # Use FFmpeg to compress the video with current CRF value
                try:
                    await status_message.edit(content=f"Compressing with quality level {crf}...")
                    os.system(f'ffmpeg -i "{video_path}" -vcodec libx264 -crf {crf} -preset faster -y "{compressed_path}"')
                    
                    if os.path.exists(compressed_path):
                        compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
                        print(f"Compressed with CRF {crf}: {compressed_size:.1f}MB")
                        
                        if compressed_size <= 8:
                            # We found a compression level that works
                            video_path = compressed_path
                            file_size = compressed_size
                            print(f"Successfully compressed video to {file_size:.1f}MB with CRF {crf}")
                            success = True
                            
                            # Clean up other compressed versions
                            for other_crf in crf_values:
                                if other_crf != crf:
                                    other_path = f"{temp_dir}/compressed_crf{other_crf}_{os.path.basename(video_path)}"
                                    if os.path.exists(other_path):
                                        os.remove(other_path)
                            
                            break
                        else:
                            # This compression level wasn't enough, remove this file and try next level
                            os.remove(compressed_path)
                except Exception as e:
                    print(f"Error during compression with CRF {crf}: {str(e)}")
                    if os.path.exists(compressed_path):
                        os.remove(compressed_path)
            
            if not success:
                # If we couldn't compress it enough with any CRF value
                await status_message.edit(content=f"Video is too large and couldn't be compressed below 8MB. Discord has an 8MB upload limit.")
                # Clean up
                os.remove(video_path)
                return
        
        # Send the video
        await status_message.edit(content=f"Uploading {platform} content ({file_size:.1f}MB)...")
        await message.channel.send(file=discord.File(video_path))
        await status_message.delete()
        
        # Clean up
        os.remove(video_path)
        # Any compressed files should have been cleaned up already
        
    except Exception as e:
        await status_message.edit(content=f"Error downloading {platform} content: {str(e)}")

# Replace 'YOUR_BOT_TOKEN' with your actual Discord bot token
bot.run(os.getenv('BOT_TOKEN'))

