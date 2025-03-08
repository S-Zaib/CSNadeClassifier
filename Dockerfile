# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV BOT_HOME=/app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Create a non-root user and switch to it
RUN useradd -m botuser
WORKDIR $BOT_HOME
COPY --chown=botuser:botuser . $BOT_HOME
USER botuser

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Use BuildKit to securely inject secrets
RUN --mount=type=secret,id=bot_token,env=BOT_TOKEN \
    --mount=type=secret,id=gemini_api_key,env=GEMINI_API_KEY \
    echo "BOT_TOKEN and GEMINI_API_KEY secrets injected securely."

# Command to run the bot
CMD ["python", "main.py"]
