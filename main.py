#!/usr/bin/python3
import os
import imdb
import base64
import ollama
import discord
import time as t
import random as r
import configparser
from contextlib import suppress
from discord.ext import commands
from discord import app_commands, Interaction, Embed

def logging(logfile, logstr, usern):
    with open(logfile, "a") as file:
        file.write(str(int(round(t.time() * 1000))) + " " + logstr + " from " + usern + "\n")

# Setup Credentials
botconfig = configparser.ConfigParser()
botconfig.read('conf.ini')
BOT_TOKEN = botconfig.get('API', 'apitoken')
GUILD_ID = botconfig.getint('API', 'guildid')
TRUNCATE_LEN = botconfig.getint('GENERAL', 'trunclen')
LOGF = botconfig.get('GENERAL', 'logfile')
logfn = LOGF
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"Bot is ready. Logged in as {client.user} (ID: {client.user.id})")
    logging(logfn, f"Bot is ready.  Logged in as {client.user} (ID: {client.user.id})", "self")
    await tree.sync(guild=discord.Object(id=GUILD_ID))

@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        print(f"{interaction.user} has use /{interaction.type} command")
        rand_int = r.randint(1, 10)
        if rand_int == 1:
            embed = discord.Embed(title="About The Bot", color=discord.Color.dark_green())
            embed.add_field(name="Who it is by?", value="Its a joint effort by Oxagast and Vesteria_", inline=False)
            embed.set_footer(text="Thanks for using our bot!")
            await interaction.user.send(embed=embed)

# Commands
@tree.command(name="ping", description="sends ping of bot", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    latency = client.latency * 1000  # Convert to ms
    logging(logfn, "Responding to command (ping)", str(interaction.user))
    await interaction.response.send_message(f'Pong! `{latency:.2f}ms`', ephemeral=True)

@tree.command(name="eb64", description="Encodes Base64", guild=discord.Object(id=GUILD_ID))
async def base64e(interaction: discord.Interaction, message_text: str):
    data = message_text.encode("utf-8")
    b64encoded = base64.b64encode(data)
    logging(logfn, "Responding to command (eb64)", str(interaction.user))
    await interaction.response.send_message("Encoded base64: " + b64encoded.decode('utf-8'), ephemeral=True)

@tree.command(name="db64", description="Decodes Base64", guild=discord.Object(id=GUILD_ID))
async def base64d(interaction: discord.Interaction, message_text: str):
    data = message_text.encode("utf-8")
    b64decoded = base64.b64decode(data)
    logging(logfn, "Responding to command (db64)", str(interaction.user))
    await interaction.response.send_message("Decoded base64: " + b64decoded.decode('utf-8'), ephemeral=True)

@tree.command(name="imdb", description="Pulls movie info from ImDB", guild=discord.Object(id=GUILD_ID))
async def imdbmovie(interaction: discord.Interaction, title: str):
    await interaction.response.defer()
    logging(logfn, "Responding to command (imdb)", str(interaction.user))
    ia = imdb.IMDb()
    iasearch = ia.search_movie(title)
    if iasearch:
        movie = iasearch[0]
        ia.update(movie) # Retrieve full details for the movie
        lnlen = TRUNCATE_LEN - 3
        synopsis = str(movie['synopsis'][0].replace("\n", "")[:lnlen])
        await interaction.followup.send("ImDB: " + movie['title'] + ": Year " + str(movie['year']) + " - " + synopsis + "...", ephemeral=True)
        print("Responding to command (imdb) err: movie not found.")
    else:
        await interaction.followup.send("Server under heavy load or movie not found!", ephemeral=True)
        logging("Responding to command (imdb) err: movie not found.", str(interaction.user))

@tree.command(name="roast", description="roasts a users", guild=discord.Object(id=GUILD_ID))
async def diss(interaction: discord.Interaction, user: str, topic: str):
    await interaction.response.defer()
    logging(logfn, "Responding to command (diss)", str(interaction.user))
    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": f" you are a roast bot, roast this user: {user} on {topic}"}])
    output = response["message"]["content"]
    await interaction.followup.send(output)

client.run(BOT_TOKEN)
