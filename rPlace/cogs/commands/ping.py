"""
Measures the bot's latency, mainly used to check if the bot can just respond.
"""

import time
from discord.ext import commands

class Ping(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    
  @commands.command()
  @commands.guild_only()
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def ping(self, ctx): 
    start = time.perf_counter()
    msg = await ctx.send("Resolving...")
    end = time.perf_counter()
    duration = (end - start) * 1000
    await msg.edit(content = f"**Web socket latency:** {round(self.bot.latency * 1000)}ms\n**Total latency:** {duration:.0f}ms")

def setup(bot):
  bot.add_cog(Ping(bot))