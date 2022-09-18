"""
Utility functions that don't belong anywhere else, contains:
- shortText       ; returns the truncated string if bigger than the given max characters length
- dotText         ; returns the string with a '.' at the end if not already
- getchChannel    ; get then fetches
- immutify        ; immutifies the input
- cellToColor     ; converts cell to hex color, white if None
- gridToCanvas    ; gets the hex colors in the 2d grid
- timedOut        ; times out an embed
- getSection      ; gets a section of the 2d list
- makeTriggers    ; makes reaction and message wait_for tasks
- updateCursor    ; updates the cursor
"""

import re
import asyncio
import numpy as np

def shortText(text, maxCharacters, shortest = False):
  a = text
  n = maxCharacters
  if shortest:
    b = '...'
  else:
    b = '\n... ({0} chars left)'
  if n < len(a):
    b = b.format(len(a)-n)
    a = a[:n-len(b)] + b
  return a

def dotText(text):
  return text + ('' if text[-1] == '.' else '.')

async def getchChannel(bot, channelID):
  channel = bot.get_channel(channelID)
  if not channel:
    channel = await bot.fetch_channel(channelID)
  return channel

def immutify(a):
  if (isinstance(a, int)):
    return a
  if (isinstance(a, str)):
    return a
  if (isinstance(a, tuple)):
    out = []
    for elem in a:
        new = immutify(elem)
        out.append(new)
    return tuple(out)
  if (isinstance(a, frozenset)):
    #out = []
    #for elem in a:
      #new = immutify(elem)
      #out.append(new)
    #return frozenset(out)
    return a
  if (isinstance(a, set)):
    out = []
    for elem in a:
      new = immutify(elem)
      out.append(new)
    return frozenset(out)
  if (isinstance(a, list)):
    out = []
    for elem in a:
      new = immutify(elem)
      out.append(new)
    return tuple(out)
  if (isinstance(a, dict)):
    tup = []
    pair = []
    for elem in a:
      new1 = immutify(elem)
      new2 = immutify(a[elem])
      pair.append(new1)
      pair.append(new2)
      tup.append(tuple(pair))
      pair = []
    return tuple(tup)

def getGridColors(grid):
  newGrid = []
  for y, row in enumerate(grid):
    newRow = []
    for x, item in enumerate(row):
      if isinstance(item, dict) and 'c' in item:
        newRow.append(item['c'])
      else:
        newRow.append(None)
    newGrid.append(newRow)
  return newGrid

def cellToColor(i):
  if isinstance(i, dict) and 'c' in i:
    return (int(i['c'][:2], 16), int(i['c'][2:4], 16) , int(i['c'][4:6], 16))
  return (255, 255, 255)

def gridToCanvas(grid):
  r, c = len(grid), len(grid[0])
  newGrid = [[None] * r for _ in range(c)]
  #for c in range(C):
  #  for r in range(R - 1, -1, -1):
  #    newGrid[C-c-1][r] = cellToColor(grid[r][c])
  for y, row in enumerate(grid):
    for x, cell in enumerate(row):
      newGrid[y][x] = cellToColor(cell)
  return list(reversed(newGrid))

async def timedOut(msg, embed):
  footer = embed.footer.text
  text = '⌛ Interaction timed out.'
  if footer:
    text = footer + ' | ' + text
  embed.set_footer(text = text)
  await msg.edit(embed = embed)

async def stopped(msg, embed):
  footer = embed.footer.text
  text = '⏹️ Interaction stopped.'
  if footer:
    text = footer + ' | ' + text
  embed.set_footer(text = text)
  await msg.edit(embed = embed)

def getSection(grid, pointer, zoom):
  height = len(grid)
  width = len(grid[0])
  radius = int(zoom/2)
  newPointer = [radius] * 2
  startx = pointer[0] - radius
  if startx < 0:
    startx = 0
    newPointer[0] = pointer[0]
  elif pointer[0] + radius > width - 1:
    startx = width - zoom
    newPointer[0] = zoom - (width - pointer[0])
  starty = pointer[1] - radius
  if starty < 0:
    starty = 0
    newPointer[1] = pointer[1]
  elif pointer[1] + radius > height - 1:
    starty = height - zoom
    newPointer[1] = zoom - (height - pointer[1])
  section = np.array(grid)[starty:starty+zoom, startx:startx+zoom].tolist()
  return section, newPointer

def makeTriggers(bot, ctx, msg, reactions):
  reactionTask = asyncio.create_task(
    bot.wait_for(
      'reaction_add',
      check = lambda reaction, user: 
        user == ctx.author 
        and reaction.message == msg
        and str(reaction.emoji) in reactions
    ),
    name = 'reactionTask'
  )
  pattern = '^(((left|right|up|down) [1-9][0-9]*)|(move [1-9][0-9]*,[1-9][0-9]*)|(color #[0-9a-fA-F]{6}))$'
  messageTask = asyncio.create_task(
    bot.wait_for(
      'message',
      check = lambda message:
        message.author == ctx.author
        and re.match(pattern, message.content)
    ),
    name = 'messageTask'
  )
  return reactionTask, messageTask

def updateCursor(grid, cursor, args): 
  border = len(grid) - 1
  before = cursor.copy()
  if args[0] == 'move':
    f = lambda v: int(v) - 1
    cursor = list(map(f, args[1].split(',')))
  else:
    units = int(args[1])
    if args[0] == 'left':
      cursor[0] -= units
    elif args[0] == 'right':
      cursor[0] += units
    elif args[0] == 'up':
      cursor[1] += units
    elif args[0] == 'down':
      cursor[1] -= units
  if cursor[0] > border:
    cursor[0] = border
  elif cursor[0] < 0:
    cursor[0] = 0
  if cursor[1] > border:
    cursor[1] = border
  elif cursor[1] < 0:
    cursor[1] = 0
  skipEdit = before == cursor
  return cursor, skipEdit

async def getchServerMember(bot, tile):
  if not tile:
    return None, None
  guildID = tile['s']
  guild = bot.get_guild(guildID)
  #if not guild:
  #  guild = await bot.fetch_guild(guildID)
  if not guild:
    return None, None
  mID = tile['u']
  member = guild.get_member(mID)
  if not member:
    member = await guild.fetch_member(mID)
  return guild, member