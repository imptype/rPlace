"""
Helper functions or code that is just odd.
"""

import time
import string
import asyncio
import discohook
import numpy as np
from PIL import Image

def is_local(interaction):
  if interaction.kind == 2: # app command, just started
    value = interaction.payload['data']
  else: # 3, 5 component or modal interaction, edited
    value = interaction.payload['message']['interaction']
  return value['name'] != 'canvas' # is local canvas command

def get_local_id(interaction):
  local_id = None
  if is_local(interaction): 
    local_id = interaction.guild_id or interaction.author.id # guild_id is None meaning it is in DMs
    #local_id = convert_text(local_id, string.digits) # unused because it sometimes breaks deta's querying
  return local_id # ^ saves storage

async def get_grid(interaction, force = False):
  local_id = get_local_id(interaction)
  app = interaction.client
  cache = app.pixels

  grid = cache.get(local_id)
  if force or not grid or app.refreshed_at + app.constants.REFRESH_DEBOUNCE < time.time():
    grid = await interaction.client.db.get_grid(local_id)
    cache[local_id] = grid
    app.refreshed_at = time.time()
  
  if force: # need to return local id too for updating db
    return grid, local_id
  
  return grid

def get_username(user):
  return user.name if user.discriminator == 0 else '{}#{}'.format(user.name, user.discriminator)

async def get_user_data(interaction, user_id):
  cache = interaction.client.users
  user_key = int(user_id)
  user_data = cache.get(user_key)
  if user_data is None:
    resp = await interaction.client.http.fetch_user(str(user_id))
    if resp.status == 200:
      data = await resp.json()
      user = discohook.User(interaction.client, data)
      username = get_username(user)
      avatar_url = user.avatar.url
      user_data = username, avatar_url      
    else:
      user_data = False # indicates Unknown user / fetch failed
    cache[user_key] = user_data
  return user_data

async def get_guild_data(interaction, guild_id):
  cache = interaction.client.guilds
  guild_key = int(guild_id)
  guild_data = cache.get(guild_key)
  if guild_data is None:
    try:
      guild = await interaction.client.fetch_guild(guild_id)
      guild_data = guild.name, guild.icon
    except: # fails if not mutual servers or on server widget/server discovery
      guild = False # indicates Unknown user / fetch failed
    cache[guild_key] = guild_data
  return guild_data

# space ' ' is reserved to be delimeter
ascii_chars = list("""!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~""")

def power_sum(values, base, offset = 0):
  return sum(value * base ** (index + offset) for index, value in enumerate(values))

def convert_text(text, chars):
  base = len(chars) + 1
  chars =  {char : index + 1 for index, char in enumerate(chars)}
  temp = []
  result = ''
  for char in text:
    value = chars[char] # indexerror = missing that char in char set
    if value * base ** len(temp) + power_sum(temp, base, 1) > len(ascii_chars): 
      result += ascii_chars[power_sum(temp, base)]
      temp = [value]
    else:
      temp.append(value)
  result += ascii_chars[power_sum(temp, base)]
  return result
    
def revert_text(text, chars):
  base = len(chars) + 1
  chars = list(chars)
  result = ''
  for char in text:
    value = ascii_chars.index(char)
    while value:
      result += chars[(value % base) - 1]
      value //= base
  return result

def draw_map(grid, size, startx = 0, starty = 0): # for sections, starty and startx is given
  a = np.empty((size, size, 3), np.uint8)
  for i in range(size):
    y_key = starty + i
    if y_key in grid:
      a[i] = np.vstack(tuple((
        (
          np.array(((grid[y_key][str(x_key)][0] >> 16) & 255, (grid[y_key][str(x_key)][0] >> 8) & 255, grid[y_key][str(x_key)][0] & 255))
          if str(x_key) in grid[y_key]
          else np.full((3), 255)
        )
        for x_key in range(startx, startx + size) # this ensures X order
      )))
    else: # new grids
      a[i] = np.full((size, 3), 255)
  return Image.fromarray(a[::-1]) # draw upside down

def to_chunks(lst, n):
  return [lst[i:i + n] for i in range(0, len(lst), n)]