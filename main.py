#!/usr/bin/python3
import os
import sys
import imdb
import ollama
import base64
import inspect
import discord
import threading
import time as t
import random as r
import configparser
from contextlib import suppress
from discord.ext import commands
from discord import app_commands, Interaction, Embed
from queue import Queue
totreqs = 0
startt = t.perf_counter()

def logging(logfile, logstr, usern):
    with open(logfile, "a") as file:
        file.write(str(int(round(t.time() * 1000))) + " " + logstr + " from " + usern + "\n")

def heartbeat(q, st):
    while True:
        qmsg = q.get() 
        if qmsg == "STOP":
            break
        q.task_done()
        t.sleep(300) # 5 minutes between haertbeats
        logging(logfn, "Requests handled: " + str(totreqs) + " Total uptime: " + str(convtime(round(t.perf_counter() - startt, 1))) + " sec", "self")

def convtime(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)


# Setup Credentials
botconfig = configparser.ConfigParser()
botconfig.read('conf.ini')
BOT_VERSION = "v0.1.8"
BOT_TOKEN = botconfig.get('API', 'apitoken')
GUILD_ID = botconfig.getint('API', 'guildid')
guildidstr = str(GUILD_ID)
TRUNCATE_LEN = botconfig.getint('GENERAL', 'trunclen')
LOGF = botconfig.get('GENERAL', 'logfile')
st = 30
# internal vars
logfn = LOGF
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
q = Queue()
hb = threading.Thread(target=heartbeat, args=(q, st))
hb.start()


@client.event
async def on_ready():
    print(f"Bot is ready. Logged in as {client.user} (ID: {client.user.id})")
    logging(logfn, f"Bot is ready.  Logged in as {client.user} (ID: {client.user.id})", "self")
    logging(logfn, "API Token: " + BOT_TOKEN[0:4] + "..." + BOT_TOKEN[len(BOT_TOKEN)-4:len(BOT_TOKEN)], "self")
    logging(logfn, "Guild: " + str(GUILD_ID)[0:4] + "..." + str(GUILD_ID)[len(str(GUILD_ID))-4:len(str(GUILD_ID))], "self")
    logging(logfn, "Logging to file: " + logfn, "self")
    logging(logfn, "Requests handled: " + str(totreqs) + " Total uptime: " + str(convtime(round(t.perf_counter() - startt, 1))) + " sec", "self")
    await tree.sync(guild=discord.Object(id=GUILD_ID))

@client.event
async def on_connect():
    guild = client.get_guild(GUILD_ID)
    for member in guild.members:
        if member.bot:
            if member.status == discord.Status.online:
                botname = str(client.user).split('#', 1)
                if member.name == str(botname[0]):
                    print("Bot already logged in!")
                    logging(logfn, "Another bot instance is online! Quitting to avoid collisions!", "self")
                    q.put("STOP")
                    hb.join()
                    print("Quitting!")
                    await client.close()

@client.event
async def on_interaction(interaction: discord.Interaction):
    global totreqs
    totreqs += 1
    if interaction.type == discord.InteractionType.application_command:
        print(f"{interaction.user} has used /{interaction.command.name} command")
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
    logging(logfn, f"Responding to command ({inspect.currentframe().f_code.co_name})", str(interaction.user))
    await interaction.response.send_message(f'Pong! `{latency:.2f}ms`', ephemeral=True)

@tree.command(name="eb64", description="Encodes Base64", guild=discord.Object(id=GUILD_ID))
async def base64e(interaction: discord.Interaction, message_text: str):
    data = message_text.encode("utf-8")
    b64encoded = base64.b64encode(data)
    logging(logfn, f"Responding to command ({inspect.currentframe().f_code.co_name})", str(interaction.user))
    await interaction.response.send_message("Encoded base64: " + b64encoded.decode('utf-8'), ephemeral=True)

@tree.command(name="db64", description="Decodes Base64", guild=discord.Object(id=GUILD_ID))
async def base64d(interaction: discord.Interaction, message_text: str):
    data = message_text.encode("utf-8")
    b64decoded = base64.b64decode(data)
    logging(logfn, f"Responding to command ({inspect.currentframe().f_code.co_name})", str(interaction.user))
    await interaction.response.send_message("Decoded base64: " + b64decoded.decode('utf-8'), ephemeral=True)

@tree.command(name="imdb", description="Pulls movie info from ImDB", guild=discord.Object(id=GUILD_ID))
async def imdbmovie(interaction: discord.Interaction, title: str):
    await interaction.response.defer(thinking=True)
    logging(logfn, f"Responding to command ({inspect.currentframe().f_code.co_name})", str(interaction.user))

    ia = imdb.IMDb()
    iasearch = ia.search_movie(title)
    if iasearch:
        movie = iasearch[0]
        ia.update(movie) # Retrieve full details for the movie
        lnlen = TRUNCATE_LEN - 3
        synopsis = str(movie['synopsis'][0].replace("\n", "")[:lnlen])
        title_part = movie['title']
        year_part = str(movie['year'])
        synopsis_part = synopsis + "..."
        poster_url = movie.get("full-size cover url")
        embed = discord.Embed(title=f"About The Movie: {title_part}, {year_part}", color=discord.Color.dark_green())
        embed.add_field(name="Description:", value=synopsis_part, inline=False)
        embed.set_image(url=poster_url)
        embed.set_footer(text="Thanks for using our bot!")
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Server under heavy load or movie not found!", ephemeral=True)
        logging(f"Responding to command ({inspect.currentframe().f_code.co_name}) err: movie not found.", str(interaction.user))
        print("Responding to command (imdb) err: movie not found.")

@tree.command(name="roast", description="roasts a users", guild=discord.Object(id=GUILD_ID))
async def diss(interaction: discord.Interaction, user: str, topic: str):
    await interaction.response.defer(thinking=True)
    logging(logfn, f"Responding to command ({inspect.currentframe().f_code.co_name})", str(interaction.user))
    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": f" you are a roast bot, roast this user: {user} on {topic}"}])
    output = response["message"]["content"] if "message" in response else str(response)
    await interaction.followup.send(output)

client.run(BOT_TOKEN)
