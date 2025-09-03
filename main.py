#!/usr/bin/python3
import os
import imdb
import ollama
import base64
import discord
import time as t
import configparser
from contextlib import suppress
from discord.ext import commands
from discord import app_commands, Interaction, Embed

# Setup Credentials
botconfig = configparser.ConfigParser()
botconfig.read('conf.ini')
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

@tree.command(name="imdb", description="Pulls movie info from ImDB", guild=discord.Object(id=GUILD_ID))
async def imdbmovie(interaction: discord.Interaction, title: str):
    await interaction.response.defer()
    print(f"Responding to command (imdb).")
    ia = imdb.IMDb()
    iasearch = ia.search_movie(title)
    if iasearch:
        movie = iasearch[0]
        ia.update(movie) # Retrieve full details for the movie
        lnlen = 200
        try:
            synopsis = str(movie['synopsis'][0].replace("\n", "")[:lnlen])
        except Exception:
            await interaction.followup.send("Server under heavy load or movie not found!")
        try:
            await interaction.followup.send("ImDB: " + movie['title'] + ": Year " + str(movie['year']) + " - " + synopsis + "...", ephemeral=True)
        except Exception:
#            print("Responding to command (imdb) err: movie not found.")
            await interaction.followup.send("Server under heavy load or movie not found!")
    else:
        await interaction.followup.send("Server under heavy load or movie not found!")

@tree.command(name="roast", description="roasts a users", guild=discord.Object(id=GUILD_ID))
async def diss(interaction: discord.Interaction, user: str, topic: str):
    await interaction.response.defer()
    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": f" you are a roast bot, roast this user: {user} on {topic}"}])
    output = response["message"]["content"]
    await interaction.followup.send(output)

client.run(BOT_TOKEN)




