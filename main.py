import discord
from discord.ext import commands
import os

from config.settings import get_discord_intents, BOT_TOKEN, COMMAND_PREFIX, TEMP_DIR

# Initialize the bot
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=get_discord_intents())

@bot.event
async def on_ready():
    print(f'Bot is logged in as {bot.user}')
    
    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)

# Load extensions
bot.load_extension('cogs.media_handler')

# Run the bot
if __name__ == "__main__":
    bot.run(BOT_TOKEN)