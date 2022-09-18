"""
Generates feedback for users on the most common errors.
"""

import sys
import traceback
import discord
from discord.ext import commands
import datetime
from ...utils.functions import shortText, dotText

class CommandErrorHandler(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_command_error(self, ctx, error):

    # Ignore if local on_command_error handler is present.
    if hasattr(ctx.command, 'on_error'): 
      return

    # Ignore if local cog_command_error handler is present.
    cog = ctx.cog
    if cog:
      if cog._get_overridden_method(cog.cog_command_error) is not None:
        return

    # Get original exception if present.
    error = getattr(error, 'original', error)

    # Ignore these errors.
    ignored = (
      commands.CommandNotFound, 
    )
    if isinstance(error, ignored):
      return

    # Get custom documented text for exception if present
    text = 'Oh no! Something went wrong while running the command!'
    if isinstance(error, commands.DisabledCommand):
      text = 'This command has been disabled.'
    elif isinstance(error, commands.ExtensionNotLoaded):
      text = 'Cog/extension has not been loaded.'
    elif isinstance(error, commands.NoPrivateMessage):
      text = 'This command cannot be used in Private Messages.'
    elif isinstance(error, commands.MaxConcurrencyReached):
      text = 'An instance of this command that you invoked is still running.'
    elif isinstance(error, commands.CommandOnCooldown):
      text = 'This command is on cooldown. Please try again after {} seconds.'.format(round(error.retry_after, 1))
    elif isinstance(error, commands.MissingPermissions):
      text = 'You are missing the required permissions to run this command!'
    elif isinstance(error, commands.BotMissingPermissions):
      text = 'The bot is missing permissions to run this command!'
    elif isinstance(error, commands.MissingRequiredArgument):
      text = 'This command is missing a required argument: {}'.format(error.param)
    elif isinstance(error, commands.ConversionError):
      text = str(error)

    # Send response.
    try:
      n = '\n'
      doc = error.__doc__
      if doc:
        cb = f'{error.__class__.__name__}: {dotText(error.__doc__.split(n)[0])}'
      else:
        cb = error.__class__.__name__
      await ctx.send((
        f'{text}'
        '```fix\n'
        f'{cb}'
        '```'
        ))
    except discord.HTTPException:
      pass

    # Print the traceback too for any errors not listed below
    known = (
      commands.DisabledCommand, 
      commands.ExtensionNotLoaded, 
      commands.NoPrivateMessage, 
      commands.MaxConcurrencyReached, 
      commands.CommandOnCooldown, 
      commands.MissingPermissions, 
      commands.MissingRequiredArgument, 
      commands.ConversionError
    )
    if not isinstance(error, known):
      print((
        '\n'
        f'Ignoring exception in command "{ctx.command}"\n'
        f'DateTime: {datetime.datetime.utcnow()}\n'
        f'Author: {ctx.author}\n'
        f'UserID: {ctx.author.id}\n'
        f'ServerID: {ctx.guild.id}\n'
        f'ChannelID: {ctx.channel.id}\n'
        f'MessageID: {ctx.message.id}\n'
        f'Content: {shortText(ctx.message.content, 100)}\n'
        f'{type(error)}\n'
        f'{error}\n'
        f'{error.__traceback__}'
      ))
      traceback.print_exception(
        type(error), 
        error, 
        error.__traceback__, 
        file = sys.stderr
      )

def setup(bot):
  bot.add_cog(CommandErrorHandler(bot))