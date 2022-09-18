"""
Guild join and leave logs.
"""

import os
import discord
from datetime import datetime
from discord.ext import commands
from ...utils.functions import getchChannel

class Logs(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot
    self.channel = os.getenv('LOG_CHANNEL')

  async def sendLog(self, guild, join = True):
    if join:
      action = 'Joined'
      color = discord.Color.green()
    else:
      action = 'Left'
      color = discord.Color.red()
    b = sum(m.bot for m in guild.members)
    embed = discord.Embed(
      title = f'{action} Guild | Count: {len(self.bot.guilds)}',
      description = (
        f'**Name:** {guild.name} | {guild.id}\n'
        f'**Owner:** {guild.owner} | {guild.owner.id}\n'
        f'**Members**: {guild.member_count}\n'
        f'**Bots:** {b} or {int((b/guild.member_count)*100)}%\n'
        f'**Channels:** {len(guild.channels)}\n'
        f'**Emojis:** {len(guild.emojis)}\n'
        f'**Boosts:** {guild.premium_subscription_count}\n'
        f'**Created At:** <t:{int(guild.created_at.timestamp())}:R>\n'
        f'**Description:** {guild.description}'
      ),
      color = color,
      timestamp = datetime.utcnow()
    )
    embed.set_author(
      name = guild.owner.name,
      icon_url = guild.owner.avatar_url
    )
    embed.set_thumbnail(url = guild.icon_url)
    channel = await getchChannel(self.bot, self.channel)
    await channel.send(embed = embed)
  
  @commands.Cog.listener()
  async def on_guild_join(self, guild):
    await self.sendLog(guild)

  @commands.Cog.listener()
  async def on_guild_remove(self, guild):
    await self.sendLog(guild, False)

def setup(bot):
  bot.add_cog(Logs(bot))