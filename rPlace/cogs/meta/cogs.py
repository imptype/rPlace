"""
Extra commands for the bot's owner to load/unload/reload specified cogs.
"""

from discord.ext import commands
import pathlib

class Cogs(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot
    self.path = pathlib.Path(__file__).parent.parent.parent.name
    
  @commands.command()
  @commands.is_owner()
  async def load(self, ctx, extension):
    if extension == 'cogs':
      await ctx.send('Can\'t load cogs')
      return
    self.bot.load_extension(f'{self.path}.cogs.{extension}')
    await ctx.send(f'Loaded {extension}')
  

  @commands.command()
  @commands.is_owner()
  async def unload(self, ctx, extension):
    if extension == 'cogs':
      await ctx.send('Can\'t unload cogs')
      return
    self.bot.unload_extension(f'{self.path}.cogs.{extension}')
    await ctx.send(f'Unloaded {extension}')


  @commands.command()
  @commands.is_owner()
  async def reload(self, ctx, extension):
    if extension == 'cogs':
      await ctx.send('Can\'t reload cogs')
      return
    self.bot.unload_extension(f'{self.path}.cogs.{extension}')
    await ctx.send(f'Unloaded {extension}')
    self.bot.load_extension(f'{self.path}.cogs.{extension}')
    await ctx.send(f'Loaded {extension}')


def setup(bot):
  bot.add_cog(Cogs(bot))