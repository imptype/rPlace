"""
Simple get list of guilds cog.
"""

from discord.ext import commands

class Guilds(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    
  @commands.command()
  @commands.is_owner()
  async def guilds(self, ctx): 
    guilds = sorted(
      [(guild.member_count, guild.name) for guild in self.bot.guilds], 
      key = lambda x: x[0],
      reverse = True
    )

    str = '```v\n' + '\n'.join([f"{g[0]} - {g[1]}" for g in guilds]) + '```'

    await ctx.send(str[:2000])
    

def setup(bot):
  bot.add_cog(Guilds(bot))