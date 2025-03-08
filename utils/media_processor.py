import os
import yt_dlp
import subprocess
import asyncio
from config.settings import TEMP_DIR

def log_media_info(info, platform, url):
    """Log media information to console and return structured info"""
    title = info.get('title', 'No title available')
    description = info.get('description', 'No description available')
    tags = info.get('tags', [])
    uploader = info.get('uploader', 'Unknown')
    
    duration = info.get('duration')
    duration_str = 'Unknown'
    if duration:
        minutes, seconds = divmod(int(duration), 60)
        duration_str = f"{minutes}:{seconds:02d}"
    
    # Log to console
    print("\n=== MEDIA INFORMATION ===")
    print(f"Platform: {platform}")
    print(f"URL: {url}")
    print(f"Title: {title}")
    print(f"Description: {description}")
    
    if tags:
        print(f"Tags: {', '.join(tags)}")
    else:
        print("Tags: None")
    
    print(f"Uploader: {uploader}")
    print(f"Duration: {duration_str}")
    print("========================\n")
    
    # Return structured info for classification
    return {
        'platform': platform,
        'url': url,
        'title': title,
        'description': description,
        'tags': tags,
        'uploader': uploader,
        'duration': duration_str,
        'transcript': ''  # Will be populated after transcription
    }

async def handle_large_youtube(status_message, video_path, url, temp_dir):
    file_size = os.path.getsize(video_path) / (1024 * 1024)
    await status_message.edit(content=f"Video is large ({file_size:.1f}MB). Trying lower quality...")
    
    # Quality levels from higher to lower
    quality_formats = [
        'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
        'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]',
        'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]',
        'worst[ext=mp4]/worst'
    ]
    
    success = False
    for quality in quality_formats:
        await status_message.edit(content=f"Trying quality: {quality.split('[')[0]}...")
        
        # Clean up previous download
        os.remove(video_path)
        
        # Try with lower quality
        lower_ydl_opts = {
            'format': quality,
            'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(lower_ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                
                # Check if this quality is small enough
                file_size = os.path.getsize(video_path) / (1024 * 1024)
                print(f"Downloaded at quality {quality.split('[')[0]}: {file_size:.1f}MB")
                
                if file_size <= 8:
                    success = True
                    break
        except Exception as e:
            print(f"Error downloading at quality {quality}: {str(e)}")
    
    if not success:
        await status_message.edit(content=f"Video is too large even at lowest quality. Discord has an 8MB upload limit.")
        if os.path.exists(video_path):
            os.remove(video_path)
        return None, 0
    
    return video_path, file_size

async def handle_large_instagram(status_message, video_path, temp_dir):
    file_size = os.path.getsize(video_path) / (1024 * 1024)
    await status_message.edit(content=f"Video is large ({file_size:.1f}MB). Attempting to compress...")
    
    # Compression levels from lower to higher compression
    crf_values = [23, 28, 32, 36, 40, 44]
    success = False
    
    for crf in crf_values:
        compressed_path = f"{temp_dir}/compressed_crf{crf}_{os.path.basename(video_path)}"
        
        # Use FFmpeg to compress the video
        try:
            await status_message.edit(content=f"Compressing with quality level {crf}...")
            os.system(f'ffmpeg -i "{video_path}" -vcodec libx264 -crf {crf} -preset faster -y "{compressed_path}"')
            
            if os.path.exists(compressed_path):
                compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
                print(f"Compressed with CRF {crf}: {compressed_size:.1f}MB")
                
                if compressed_size <= 8:
                    # We found a compression level that works
                    new_path = compressed_path
                    new_size = compressed_size
                    print(f"Successfully compressed video to {new_size:.1f}MB with CRF {crf}")
                    success = True
                    
                    # Clean up other compressed versions
                    for other_crf in crf_values:
                        if other_crf != crf:
                            other_path = f"{temp_dir}/compressed_crf{other_crf}_{os.path.basename(video_path)}"
                            if os.path.exists(other_path):
                                os.remove(other_path)
                    
                    # Clean up original file
                    os.remove(video_path)
                    return new_path, new_size
                else:
                    # This compression level wasn't enough, remove this file and try next level
                    os.remove(compressed_path)
        except Exception as e:
            print(f"Error during compression with CRF {crf}: {str(e)}")
            if os.path.exists(compressed_path):
                os.remove(compressed_path)
    
    if not success:
        await status_message.edit(content=f"Video is too large and couldn't be compressed below 8MB. Discord has an 8MB upload limit.")
        os.remove(video_path)
        return None, 0

def extract_audio(video_path, temp_dir):
    """Extract audio from video for transcription"""
    audio_path = f"{temp_dir}/audio_{os.path.basename(video_path)}.wav"
    
    # Extract audio using FFmpeg
    subprocess.run([
        'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', 
        '-ar', '16000', '-ac', '1', audio_path
    ], check=True)
    
    return audio_path