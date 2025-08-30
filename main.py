import os
import discord
import time as t
from dotenv import load_dotenv, dotenv_values
from discord import app_commands, Interaction, Embed

# Setup Credentials
load_dotenv()
BOT_TOKEN = os.getenv("bot_token")
GUILD_ID = os.getenv("guild_id")

# Setup
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"Bot is ready. Logged in as {client.user} (ID: {client.user.id})")
    await tree.sync(guild=discord.Object(id=GUILD_ID))

# Commands
@tree.command(name="ping", description="sends ping of bot", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    latency = client.latency * 1000  # Convert to ms
    await interaction.response.send_message(f'Pong! `{latency:.2f}ms`', ephemeral=True)

client.run(BOT_TOKEN)
