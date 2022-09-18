"""
Starts running the bot.
"""

import os
import pathlib
import discord
from discord.ext import commands
from .utils.database import setupDatabase

def runBot():

  intents = discord.Intents.default()
  intents.members = True

  bot = commands.Bot(
    command_prefix = '!',
    case_insensitive = True,
    activity = discord.Activity(
      type = discord.ActivityType.watching,
      name = 'the Canvas! | !canvas'
    ),
    help_command = None,
    strip_after_prefix = True,
    intents = intents
  )
  
  @bot.event
  async def on_ready():

    await setupDatabase()
    
    print('Bot is online!')
    print(f'Guilds: {len(bot.guilds)}')

    cogs = {
      'meta' : [
        'cogs',
        'error',
        'logs'
      ],
      'commands' : [
        'ping',
        'test',
        'canvas',
        'help',
        'guilds'
      ]
    }

    root = pathlib.Path(__file__).parent.name

    for folder in cogs:
      for cog in cogs[folder]:
        try:
          bot.load_extension(f'{root}.cogs.{folder}.{cog}')
          print(f'Loaded {folder}/{cog}')
        except:
          print(f'Failed to load {folder}/{cog}')
    print('Done loading cogs')

  bot.run(os.getenv('DISCORD_BOT_TOKEN'))
