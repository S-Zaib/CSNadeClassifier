# CSNadeClassifier

A Discord bot that automatically detects, downloads, and classifies Counter-Strike (CS:GO/CS2) grenade tutorial videos from Instagram Reels and YouTube Shorts, then organizes them into map-specific channels.

## Features

- 🎮 **Automatic Content Detection**: Monitors Discord messages for Instagram Reels and YouTube Shorts links
- 📥 **Smart Download**: Downloads videos with automatic quality adjustment to fit Discord's file size limits
- 🔊 **Audio Transcription**: Uses OpenAI's Whisper model to transcribe audio for better classification
- 🤖 **AI-Powered Classification**: Leverages Google's Gemini AI to identify:
  - Which CS:GO/CS2 map is featured (Mirage, Inferno, Dust2, etc.)
  - What type of grenade tutorial it is (smoke, flash, molotov, etc.)
- 📂 **Automatic Organization**: Forwards videos to map-specific Discord channels
- 🧠 **Smart Map Recognition**: Understands various map name formats (de_dust2, dust 2, etc.)

## Prerequisites

Before setting up this bot, make sure you have:

- Python 3.8 or higher
- FFmpeg installed on your system
- A Discord Bot Token
- A Google Gemini API Key

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/CSNadeClassifier.git
cd CSNadeClassifier
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Create configuration files**

Create a `.env.local` file in the project root:

```
BOT_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Create a `channels.json` file to map CS maps to Discord channel IDs:

```json
{
  "mirage": "1234567890123456789",
  "inferno": "1234567890123456789",
  "dust2": "1234567890123456789",
  "anubis": "1234567890123456789",
  "nuke": "1234567890123456789",
  "ancient": "1234567890123456789",
  "train": "1234567890123456789",
  "cache": "1234567890123456789",
  "overpass": "1234567890123456789",
  "vertigo": "1234567890123456789"
}
```

## Usage

### Starting the Bot

```bash
python bot.py
```

### Commands

- `!download [URL]` - Manually trigger the download and classification process for a video

### Automatic Detection

The bot automatically detects Instagram Reels and YouTube Shorts links posted in any channel it has access to. It will:

1. Download the video
2. Analyze content (title, description, audio transcript)
3. Classify which map and grenade type it shows
4. Forward to the appropriate channel
5. Delete the original message (if it has permission)

## Whisper Model Options

The bot uses OpenAI's Whisper model for audio transcription. You can adjust the model size in the code:

```python
whisper_model = whisper.load_model("base")  # Options: "tiny", "base", "small", "medium", "large"
```

Smaller models are faster but less accurate, while larger models are more accurate but require more computational resources.

## Technical Details

### Video Processing

1. **Download**: Uses `yt-dlp` to download from Instagram and YouTube
2. **Size Management**: 
   - For YouTube: Tries progressively lower quality formats if the video exceeds Discord's 8MB limit
   - For Instagram: Uses FFmpeg to compress with increasing compression ratios (CRF values)
3. **Audio Extraction**: Uses FFmpeg to extract audio for transcription

### Classification

Uses Google's Gemini AI model with this classification process:
1. Extracts metadata (title, description, tags)
2. Transcribes audio using Whisper
3. Sends all data to Gemini for classification
4. Parses the JSON response with the map, grenade type, and description

## Troubleshooting

### Common Issues

- **FFmpeg not found**: Ensure FFmpeg is installed and in your system PATH
- **Discord upload errors**: Check if your bot has the correct permissions in the target channels
- **Transcription errors**: You may need more computational resources for larger Whisper models

## Permissions Required

The Discord bot requires these permissions:
- Read Messages/View Channels
- Send Messages
- Manage Messages (to delete the original message)
- Attach Files
- Read Message History

## Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [Google Gemini AI](https://ai.google.dev/)
