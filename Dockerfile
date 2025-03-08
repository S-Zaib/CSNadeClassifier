# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# Set environment variables
ENV BOT_HOME=/app
WORKDIR $BOT_HOME

# Install system dependencies (Only essential ones!)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy only required files first (to leverage Docker caching)
COPY requirements.txt .

# Install dependencies **without cache** and in a virtualenv-like structure
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the bot's source code
COPY . .

# Create a non-root user and use it
RUN useradd -m botuser && chown -R botuser:botuser $BOT_HOME
USER botuser

# Securely mount secrets using BuildKit
RUN --mount=type=secret,id=bot_token,env=BOT_TOKEN \
    --mount=type=secret,id=gemini_api_key,env=GEMINI_API_KEY \
    echo "BOT_TOKEN and GEMINI_API_KEY secrets injected securely."

# Command to run the bot
CMD ["python", "main.py"]
