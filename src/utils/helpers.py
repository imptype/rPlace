"""
Helper functions or code that is just odd.
"""

import time
import discohook

def is_local(interaction):
  if interaction.kind == 2: # app command, just started
    value = interaction.payload['data']
  else: # 3, 5 component or modal interaction, edited
    value = interaction.payload['message']['interaction']
  return value['name'] != 'canvas' # is local canvas command

def get_local_id(interaction):
  local_id = None
  if is_local(interaction): 
    local_id = interaction.guild_id or interaction.user_id # guild_id is None meaning it is in DMs
  return local_id

async def get_grid(interaction, force = False):
  local_id = get_local_id(interaction)
  app = interaction.client
  helpers = app.helpers
  cache = app.pixels

  grid = cache.get(local_id)
  if force or not grid or app.refreshed_at + helpers.REFRESH_DEBOUNCE < time.time():
    grid = await interaction.client.db.get_grid(local_id)
    cache[local_id] = grid
    app.refreshed_at = time.time()
  
  return grid

async def get_username(interaction, user_id):
  cache = interaction.client.users
  user_key = int(user_id)
  username = cache.get(user_key)
  if username is None:
    resp = await interaction.client.http.fetch_user(str(user_id))
    if resp.status == 200:
      data = await resp.json()
      user = discohook.User(data, interaction.client)
      username = user.name if user.discriminator == 0 else '{}#{}'.format(user.name, user.discriminator)
    else:
      username = False # indicates Unknown user / fetch failed
    cache[user_key] = username
  return username

async def get_guild_name(interaction, guild_id):
  cache = interaction.client.guilds
  guild_key = int(guild_id)
  guild_name = cache.get(guild_key)
  if guild_name is None:
    try:
      guild = await interaction.client.fetch_guild(guild_id)
      guild_name = guild.name
    except: # fails if not mutual servers or on server widget/server discovery
      guild = False # indicates Unknown user / fetch failed
    cache[guild_key] = guild_name
  return guild_name

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