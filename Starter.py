import os
import discord
import time as t
from discord.ext import commands

# Setup Credentials
BOT_TOKEN = 'Bot_Token_Here'


# Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)
@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

'Commands'
@bot.command(name=ping)
async def ping(ctx):
    latency = bot.latency * 1000  # Convert to ms
    await ctx.send(f'Pong! `{latency:.2f}ms`')

bot.run(BOT_TOKEN)
