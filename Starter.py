import os
import discord
import time as t
from discord import app_commands, Interaction, Embed

# Setup Credentials
BOT_TOKEN = 'Bot_Token_Here'  # Replace With Your Bot Token

# Setup
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"Bot is ready. Logged in as {client.user} (ID: {client.user.id})")
    print("Syncing commands to all guilds...")
    for guild in client.guilds:
        await tree.sync(guild=discord.Object(id=guild.id))
    print("Synced commands to all guilds.")

# Commands
@tree.command(name="ping", description="sends ping of bot")
async def ping(interaction: Interaction):
    latency = client.latency * 1000  # Convert to ms
    await interaction.response.send_message(f'Pong! `{latency:.2f}ms`', ephemeral=True)

client.run(BOT_TOKEN)
