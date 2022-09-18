"""
Help cog.
"""

from discord.ext import commands

class Help(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command(name = 'help')
  async def _help(self, ctx):
    await ctx.send('Hey, the only command available is `!canvas`, to explore and re-color pixels on the global canvas.')

def setup(bot):
  bot.add_cog(Help(bot))