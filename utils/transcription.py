import whisper
import asyncio
import os

# Load Whisper model
whisper_model = whisper.load_model("base")

async def transcribe_audio(audio_path):
    """Transcribe audio using Whisper model (running in a thread pool to avoid blocking)"""
    def transcribe():
        try:
            # Transcribe the audio file
            result = whisper_model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            return ""
    
    # Run transcription in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, transcribe)