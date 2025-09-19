#!/usr/bin/python3
import re
import os
import sys
import uuid
import ollama
import signal
import base64
import inspect
import discord
import asyncio
import requests
import threading
import time as t
import random as r
import configparser
from queue import Queue
from typing import Optional
from imdb import Cinemagoer
from contextlib import suppress
from discord.ext import commands
from filelock import Timeout, FileLock
from discord import app_commands, Interaction, Embed
from selenium.webdriver.common.actions import interaction

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
        t.sleep(st) # 5 minutes between haertbeats
        logging(logfn, "Requests handled: " + str(totreqs) + " Total uptime: " + str(convtime(round(t.perf_counter() - startt, 1))) + " sec", "self")

def convtime(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def shutdown():
    print("\nCleaning up and exiting...")
    global lockfile
    q.put("STOP")
    logging(logfn, "Shutting down bot.  Total runtime: " + str(convtime(round(t.perf_counter() - startt, 1))), "self")
    os.remove(lockfile)
    sys.exit(0)

def sighandler(sig, frame):
    shutdown()

botconfig = configparser.ConfigParser()
if len(sys.argv) - 1 == 1:
    if os.path.exists(sys.argv[1]):
        conffn = sys.argv[1]
        botconfig.read(conffn)
    else:
        print("Config file doesn't exist!  Falling back to default.")
        botconfig.read('conf.ini')
elif len(sys.argv) - 1 > 1:
    print("Too many arguments! Quitting!")
    exit(1)
else:
    botconfig.read('conf.ini')
# Setup Credentials
BOT_VERSION = "v0.1.9"
BOT_TOKEN = botconfig.get('API', 'apitoken')
GUILD_ID = botconfig.getint('API', 'guildid')
guildidstr = str(GUILD_ID)
TRUNCATE_LEN = botconfig.getint('GENERAL', 'trunclen')
LOGF = botconfig.get('GENERAL', 'logfile')
st = botconfig.getint('GENERAL', 'heartbeat')
lockfile = botconfig.get('GENERAL', 'locklocation')
cooldown = botconfig.get('GENERAL', 'cooldown')

# Internal Vars
logfn = LOGF
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
q = Queue()
hb = threading.Thread(target=heartbeat, args=(q, st))
hb.start()
signal.signal(signal.SIGINT, sighandler)

# Setup Sticky Messages
global sticky, sticky_channel, sticky_id, sticky_title, sticky_description
sticky = False
sticky_channel = ""
sticky_id = "0"
sticky_title = ""
sticky_description = ""
idx = ""

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
    global lockfile
    t.sleep(1)
    guild = client.get_guild(GUILD_ID)
    if os.path.exists(lockfile): # if the lockfile is present
        print("Bot already running on this machine!")
        logging(logfn, "Another bot instance is running! Quitting to avoid collisions!", "self")
        os._exit(1)
    else:
        with FileLock(lockfile): # create lockfile for duration
            for member in guild.members:
                if member.bot:
                    if member.status == discord.Status.online:
                        botname = str(client.user).split('#', 1) # split on the hash
                        if member.name == str(botname[0]):  # get the username
                            print("Bot already logged in!")
                            logging(logfn, "Another bot instance is online! Quitting to avoid collisions!", "self")
                            q.put("STOP")
                            hb.join()
                            print("Quitting!")
                            os.remove(lockfile)
                            q.put("STOP") # send this to the hb worker thread
                            #await client.close() # close discord conn

@client.event
async def on_interaction(interaction: discord.Interaction):
    global totreqs # total requests
    totreqs += 1 # increment each req
    if interaction.type == discord.InteractionType.application_command:
        print(f"{interaction.user} has used /{interaction.command.name} command")
        rand_int = r.randint(1, 10)
        if rand_int == 1:
            embed = discord.Embed(title="About The Bot", color=discord.Color.dark_green())
            embed.add_field(name="Who it is by?", value="Its a joint effort by Oxagast and Vesteria_", inline=False)
            embed.set_footer(text="Thanks for using our bot!")
            await interaction.user.send(embed=embed)


@client.event
async def on_message(message: discord.Message):
    global sticky, sticky_channel, sticky_id, sticky_title, sticky_description, idx
    if message.author == client.user:
        return
    if sticky:
        channel = client.get_channel(int(sticky_channel))
        if sticky_id:
            try:
                message = await channel.fetch_message(int(sticky_id))
                await message.delete()
            except discord.NotFound:
                pass
        embed = discord.Embed(title=sticky_title, color=discord.Color.dark_green())
        embed.add_field(name='', value=sticky_description, inline=False)
        message = await channel.send(embed=embed)
        sticky_id = message.id
        sticky_channel = message.channel.id

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

    ia = Cinemagoer()
    iasearch = ia.search_movie(title)
    if iasearch:
        movie = iasearch[0]
        ia.update(movie) # Retrieve full details for the movie
        lnlen = TRUNCATE_LEN - 3
        plots = movie.get('plot')
        if plots:
            synopsis = str(plots[0].replace("\n", "")[:lnlen]) + "..."
        else:
            synopsis = "No plot available."
        url = f'https://www.imdb.com/title/tt{movie.movieID}/ratings/'
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"}
        response = requests.get(url, headers=headers)
        match = re.search(r'"aggregateRating":\s*([\d.]+)', response.text)
        rating = match.group(1)
        title_part = movie['title']
        year_part = str(movie['year'])
        synopsis_part = synopsis + "..."
        poster_url = movie.get("full-size cover url")
        embed = discord.Embed(title=f"{title_part}, {year_part}", color=discord.Color.dark_green())
        embed.add_field(name="Description:", value=synopsis_part, inline=False)
        embed.set_image(url=poster_url)
        embed.set_footer(text=f"⭐{rating}/10")
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Server under heavy load or movie not found!", ephemeral=True)
        logging(f"Responding to command ({inspect.currentframe().f_code.co_name}) err: movie not found.", str(interaction.user))
        print("Responding to command (imdb) err: movie not found.")

@tree.command(name="roast", description="roasts a users", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, cooldown, key=lambda i: (i.user.id,))
async def diss(interaction: discord.Interaction, topic: str, member: Optional[discord.Member] = None ):
    await interaction.response.defer(thinking=True)
    logging(logfn, f"Responding to command ({inspect.currentframe().f_code.co_name})", str(interaction.user))
    if topic and member:
        response = await asyncio.to_thread(ollama.chat, model="llama2-uncensored", messages=[{"role":"system","content":"You are a savage roast bot. Do not hold back — be over-the-top, and ruthless. Use creative insults, sarcasm, and lots of very dark humor."},{"role":"user","content":f"Roast {member} about {topic}."}])
        output = response["message"]["content"] if "message" in response else str(response)
    elif topic:
        response = await asyncio.to_thread(ollama.chat, model="llama2-uncensored", messages=[{"role":"system","content":"You are a savage roast bot. Do not hold back — be over-the-top, and ruthless. Use creative insults, sarcasm, and lots of very dark humor."},{"role":"user","content":f"Roast {topic}."}])
        output = response["message"]["content"] if "message" in response else str(response)
    else:
        output = 'Please at least one option'
    await interaction.followup.send(output)

@tree.command(name="llm", description="runs an llm", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, cooldown, key=lambda i: (i.user.id,))
async def llm(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True)
    logging(logfn, f"Responding to command ({inspect.currentframe().f_code.co_name})", str(interaction.user))
    response = await asyncio.to_thread(ollama.chat, model="llama2-uncensored", messages=[{"role":"system","content":"You are a an llm inside of a discord bot, do what ever the user ask for."},{"role":"user","content":f"{prompt}"}])
    output = response["message"]["content"] if "message" in response else str(response)
    await interaction.followup.send(output)

@tree.command(name="sticky_enable", description="enables sticky messages", guild=discord.Object(id=GUILD_ID))
async def sticky_enable(interaction: discord.Interaction, title: str, description: str, channel: str):
    await interaction.response.defer(thinking=True)
    global sticky, sticky_channel, sticky_id, sticky_title, sticky_description, idx
    sticky = True
    sticky_channel = channel.replace("<#", "").replace(">", "")
    sticky_id = None
    sticky_title = title
    sticky_description = description
    await interaction.followup.send('Sticky message is enabled', ephemeral=True)

@tree.command(name="sticky_disable", description="disables sticky messages", guild=discord.Object(id=GUILD_ID))
async def sticky_disable(interaction: discord.Interaction):
    sticky = False
    await interaction.followup.send('Sticky message is disabled', ephemeral=True)

# Error Handling
@diss.error
async def diss(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"⏳ Slow down! Try again in `{error.retry_after:.1f}` seconds.", ephemeral=True)

@llm.error
async def llm(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"⏳ Slow down! Try again in `{error.retry_after:.1f}` seconds.", ephemeral=True)

client.run(BOT_TOKEN)
