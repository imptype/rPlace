"""
Main canvas command.
"""

import time
import asyncio
from discord.ext import commands
import discord
from ...utils.database import (
  getDatabaseData,
  updateCell
)
from ...utils.canvas import draw
from ...utils.functions import (
  gridToCanvas, 
  timedOut, 
  stopped,
  getSection,
  makeTriggers,
  updateCursor,
  getchServerMember
)

reactStop = '⏹️'
reactExplore = '🔍'
reactBack = '⬅️'
reactAdd = '<:in:970441325512130610>'
reactMinus = '<:out:970441339902787636>'
reactHint = '💡'
p = '🧍'
s = '🏠'
t = '⏰'
c = '🎨'

zoomLevels = [3, 7, 13, 21, 31, 43]

class Canvas(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    bot.loop.create_task(self.async_init())
 
  async def async_init(self):
    self.grid = await getDatabaseData()  
    
  @commands.command()
  @commands.max_concurrency(1, commands.BucketType.user)
  async def canvas(self, ctx):
    
    embed = discord.Embed(
      title = 'Welcome to r/Place!',
      description = (
        f'**Canvas Size:** {len(self.grid[0])}x{len(self.grid)}\n'
        '\n'
        f'Click {reactExplore} to explore.'
      ),
      color = discord.Color.blurple()
    )

    msg = None

    while True:
      imageUrl = await draw(self.bot, gridToCanvas(self.grid))
      embed.set_image(url = imageUrl)    
      
      if msg:
        await msg.edit(embed = embed)
      else:
        msg = await ctx.send(embed = embed)

      reactions = reactExplore, reactStop
      
      for reaction in reactions:
        await msg.add_reaction(reaction)

      try:
        reactionObj, user = await self.bot.wait_for(
          'reaction_add',
          timeout = 25.0,
          check = lambda reaction, user: 
            user == ctx.author 
            and reaction.message == msg
            and str(reaction.emoji) in reactions
        )
      except asyncio.TimeoutError:
        await msg.clear_reactions()
        await timedOut(msg, embed)
        return

      await msg.clear_reactions()
      
      reaction = str(reactionObj.emoji)
      
      if reaction == reactStop:
        await stopped(msg, embed)
        return
        
      reactions = reactBack, reactAdd, reactMinus, reactHint, reactStop
      cursor = [0, 0]      # start position of cursor
      zoomLevel = int(len(zoomLevels)/2)
      zoom = zoomLevels[zoomLevel] # zoom is always odd so cursor is at the center, 5 means 5x5
      skipEdit = False # save ratelimits editing the same thing
      addedReactions = False # add reaction first time
      
      while True:
        if skipEdit:
          skipEdit = False
        else:
          tile = self.grid[cursor[1]][cursor[0]]
          section, newPointer = getSection(self.grid, cursor, zoom)
          imageUrl = await draw(self.bot, gridToCanvas(section), newPointer, zoom)
          serverObj, memberObj = await getchServerMember(self.bot, tile)
          if memberObj:
            memberName = str(memberObj)
          else:
            memberName = 'UnknownUser#0000'
          if serverObj:
            serverName = str(serverObj)
          else:
            serverName = 'UnknownServer'
          if tile:
            desc = (
              f"{c} #{tile['c']}\n"
              f"{p} {memberName}\n"#" | {tile['u']}\n"
              f"{s} {serverName}\n"#" | {tile['s']}\n"
              f"{t} <t:{tile['t']}:R>"
            )
          else:
            desc = 'Nobody has painted here yet.'
          subEmbed = discord.Embed(
            title = f'Selecting Tile ({cursor[0] + 1}, {cursor[1] + 1})',
            description = desc,
            color = discord.Color.blurple()
          )
          subEmbed.set_image(url = imageUrl)
          if memberObj:
            subEmbed.set_author(
              icon_url = memberObj.avatar_url,
              name = f'{memberObj}\'s Avatar'
            )
          if serverObj:
            subEmbed.set_thumbnail(url = serverObj.icon_url)
          await msg.edit(embed = subEmbed)
          if not addedReactions:
            for reaction in reactions:
              await msg.add_reaction(reaction)
            addedReactions = True

        reactionTask, messageTask = makeTriggers(self.bot, ctx, msg, reactions)

        done, pending = await asyncio.wait([
            messageTask,
            reactionTask
          ],
          timeout = 90.0,
          return_when = asyncio.FIRST_COMPLETED
        )

        for future in pending:
          future.cancel()

        if not done:
          await msg.clear_reactions()
          await timedOut(msg, subEmbed)
          return

        taskCompleted = done.pop()
        result = taskCompleted.result()
        name = taskCompleted.get_name()

        if name == 'messageTask':
          args = result.content.split()
          if args[0] in ('move', 'left', 'right', 'up', 'down'):
            cursor, skipEdit = updateCursor(self.grid, cursor, args)
          else:
            color = args[1].lower()
            skipEdit = False
            newData = {
              'c' : color.lstrip('#'),
              'u' : ctx.author.id,
              's' : ctx.guild.id,
              't' : int(time.time())
            }
            self.grid[cursor[1]][cursor[0]] = newData
            await updateCell(cursor[1]+1, cursor[0]+1, newData)
            await ctx.send(f'Colored **({cursor[0]}, {cursor[1]})** to **{color}**.', delete_after = 5)
          await result.delete()

        elif name == 'reactionTask':
          reactionObj, user = result
          reaction = str(reactionObj.emoji)

          prevZoom = zoomLevels[zoomLevel]

          if reaction == reactBack:
            await msg.clear_reactions()
            break
          elif reaction == reactAdd:
            zoomLevel -= 1
            if zoomLevel < 0:
              zoomLevel = 0
              await ctx.send(f'The max for zooming in is {zoom}x{zoom}.', delete_after = 5)
            else:
              zoom = zoomLevels[zoomLevel]
              await ctx.send(f'Zoomed in from {prevZoom}x{prevZoom} to {zoom}x{zoom}.', delete_after = 5)
          elif reaction == reactMinus:
            zoomLevel += 1
            if zoomLevel > len(zoomLevels) - 1:
              zoomLevel = len(zoomLevels) - 1
              await ctx.send(f'The max for zooming out is {zoom}x{zoom}.', delete_after = 5)
            else:
              zoom = zoomLevels[zoomLevel]
              await ctx.send(f'Zoomed out from {prevZoom}x{prevZoom} to {zoom}x{zoom}.', delete_after = 5)
          elif reaction == reactHint:
            await ctx.send(f'{reactHint} **How to move your cursor?**\nType `right 5` to move right 5 times. Directions are `up`, `left`, `right`, `down`. Or type `move 2,2` to jump to tile (2,2) directly. Then type `color #123abc` a valid hex color, to color the tile.')
          
            #showBulb = not showBulb
            await msg.remove_reaction(reactHint, user)
          elif reaction == reactStop:
            await msg.clear_reactions()
            await stopped(msg, embed)
            return
          await msg.remove_reaction(reaction, user)
def setup(bot):
  bot.add_cog(Canvas(bot))