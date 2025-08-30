#!/usr/bin/python3
import os
import discord
import time as t
import base64
import configparser
from discord.ext import commands
from discord import app_commands, Interaction, Embed
botconfig = configparser.ConfigParser()
botconfig.read('conf.ini')
# Setup Credentials
BOT_TOKEN = botconfig.get('API', 'apitoken')
GUILD_ID = botconfig.getint('API', 'guildid')
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
    print(f"Responding to command (ping).")
    await interaction.response.send_message(f'Pong! `{latency:.2f}ms`', ephemeral=True)


@tree.command(name="eb64", description="Encodes Base64", guild=discord.Object(id=GUILD_ID))
async def base64e(interaction: discord.Interaction, message_text: str):
    data = message_text.encode("utf-8")
    b64encoded = base64.b64encode(data)
    print(f"Responding to command (eb64).")
    await interaction.response.send_message("Encoded base64: " + b64encoded.decode('utf-8'), ephemeral=True)

@tree.command(name="db64", description="Decodes Base64", guild=discord.Object(id=GUILD_ID))
async def base64d(interaction: discord.Interaction, message_text: str):
    data = message_text.encode("utf-8")
    b64decoded = base64.b64decode(data)
    print(f"Responding to command (db64).")
    await interaction.response.send_message("Decoded base64: " + b64decoded.decode('utf-8'), ephemeral=True)

client.run(BOT_TOKEN)
