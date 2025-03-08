import discord
from discord.ext import commands
import os
import asyncio
import re
import yt_dlp

from config.settings import INSTAGRAM_URL_PATTERN, YOUTUBE_URL_PATTERN, TEMP_DIR, MAP_CHANNELS
from utils.media_processor import log_media_info, handle_large_youtube, handle_large_instagram, extract_audio
from utils.transcription import transcribe_audio
from utils.classification import classify_cs_content, get_target_channel_id

class MediaHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Create temp directory if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return
        
        should_delete_message = False
        
        # Check if message contains Instagram reel URL
        instagram_matches = re.findall(INSTAGRAM_URL_PATTERN, message.content)
        if instagram_matches:
            for match in instagram_matches:
                url = match[0]  # Extract the full URL from the tuple
                await self.download_and_process_media(message, url, 'instagram')
                should_delete_message = True
        
        # Check if message contains YouTube shorts URL
        youtube_matches = re.findall(YOUTUBE_URL_PATTERN, message.content)
        if youtube_matches:
            for match in youtube_matches:
                url = match[0]  # Extract the full URL from the tuple
                await self.download_and_process_media(message, url, 'youtube')
                should_delete_message = True
        
        # Delete the original message if it contained a valid URL
        if should_delete_message:
            try:
                await message.delete()
            except discord.errors.Forbidden:
                print(f"Cannot delete message in {message.channel.name}: Missing permissions")
    
    @commands.command(name='download')
    async def download_command(self, ctx, url):
        """Command to download media from a URL and classify it"""
        if re.match(INSTAGRAM_URL_PATTERN, url):
            await self.download_and_process_media(ctx.message, url, 'instagram')
        elif re.match(YOUTUBE_URL_PATTERN, url):
            await self.download_and_process_media(ctx.message, url, 'youtube')
        else:
            await ctx.send("Unsupported URL. Please provide an Instagram reel or YouTube shorts link.")
    
    async def download_and_process_media(self, message, url, platform):
        """Download media from URL, analyze it, and forward to appropriate channel"""
        status_message = await message.channel.send(f"Downloading {platform} content...")
        
        try:
            # Always start with best quality
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': f'{TEMP_DIR}/%(title)s.%(ext)s',
                'noplaylist': True,
            }
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                
                # Log media information
                media_info = log_media_info(info, platform, url)
            
            # Check file size
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
            
            # Handle files larger than Discord's 8MB limit
            if file_size > 8:
                if platform == 'youtube':
                    video_path, file_size = await handle_large_youtube(status_message, video_path, url, TEMP_DIR)
                    if not video_path:  # If handling failed
                        return
                elif platform == 'instagram':
                    video_path, file_size = await handle_large_instagram(status_message, video_path, TEMP_DIR)
                    if not video_path:  # If handling failed
                        return
            
            # Extract audio for transcription
            await status_message.edit(content=f"Extracting audio for transcription...")
            
            try:
                audio_path = extract_audio(video_path, TEMP_DIR)
                
                # Transcribe audio with Whisper
                await status_message.edit(content=f"Transcribing audio content...")
                transcript = await transcribe_audio(audio_path)
                
                # Add transcript to media info
                media_info['transcript'] = transcript
                print(f"Transcript: {transcript}")
                
                # Clean up audio file
                os.remove(audio_path)
                
            except Exception as e:
                print(f"Error extracting/transcribing audio: {str(e)}")
                media_info['transcript'] = "Transcription failed."
            
            # Analyze the media content to classify it
            await status_message.edit(content=f"Analyzing content to determine the appropriate map channel...")
            classification_result = await classify_cs_content(media_info)
            
            # Determine the target channel
            target_channel_id = get_target_channel_id(classification_result, MAP_CHANNELS)
            if target_channel_id:
                target_channel = self.bot.get_channel(int(target_channel_id))
                if target_channel:
                    # Send to appropriate channel
                    await status_message.edit(content=f"Uploading to #{target_channel.name} ({file_size:.1f}MB)...")
                    
                    # Create a message with the classification info
                    description = f"**Map: {classification_result['map']}** | {classification_result['description']}"
                    
                    # Send the video with classification info
                    await target_channel.send(content=description, file=discord.File(video_path))
                    await status_message.edit(content=f"Successfully classified and posted to #{target_channel.name}!")
                else:
                    # Fallback to current channel if target not found
                    await status_message.edit(content=f"Target channel not found. Posting here instead...")
                    await message.channel.send(
                        content=f"**Map: {classification_result['map']}** | {classification_result['description']}\n\nSource: {url}",
                        file=discord.File(video_path)
                    )
            else:
                # If classification failed or no suitable channel, post to original channel
                await status_message.edit(content=f"Couldn't classify content. Posting here ({file_size:.1f}MB)...")
                await message.channel.send(file=discord.File(video_path))
            
            # Clean up
            os.remove(video_path)
            await asyncio.sleep(10)  # Wait a bit before deleting status message
            await status_message.delete()
            
        except Exception as e:
            await status_message.edit(content=f"Error processing {platform} content: {str(e)}")

def setup(bot):
    bot.add_cog(MediaHandler(bot))