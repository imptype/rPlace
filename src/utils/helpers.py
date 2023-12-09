"""
Helper functions or code that is just odd.
"""

#import os
import time
import string
#import aiohttp
import asyncio
#import hashlib
import discohook
import numpy as np
from PIL import Image

# space ' ' is reserved to be delimeter
ASCII_CHARS = list("""!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~""")

# encryption is unused, could use it for a future bot
CRYPT_CHARS = list(string.digits + string.ascii_letters + ':._') # all possible chars in custom id
MAX_SURROGATE = 2_048
START_SURROGATE = 55_296 # 0xd800
MAX_UNICODE = 1_114_112 - MAX_SURROGATE # 0x10ffff - unprintable/pointer chars
MAX_RANDOM = 4_294_967_296 # 0x100000000
#SALT = int(''.join(map(lambda x: str(ord(x)), os.getenv('SALT')))) # int, used for unicode char text sum int
#SALT2 = os.getenv('SALT2') # str, used for hash sum
#SALT3 = int(''.join(map(lambda x: str(ord(x)), os.getenv('SALT3')))) # int, used for position of text sum in text result

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

async def get_grid(interaction, force = False): # interaction Client = taking snapshot

  if isinstance(interaction, discohook.Client): # discohook
    app = interaction
    local_id = None
  else:
    app = interaction.client
    local_id = get_local_id(interaction)

  cache = app.pixels
  refresh_cache = app.refreshes

  grid_data = cache.get(local_id) # grid {}, configs {}
  refresh_at = refresh_cache.get(local_id) # if grid exists, this will too
  defer_response = None
  now = time.time()
  if force or grid_data is None or refresh_at / 10 ** 7 + app.constants.REFRESH_DEBOUNCE < now:

    # before joining queue, check if fetch debounce expired before fetching
    if not force or not grid_data or refresh_at / 10 ** 7 + app.constants.FETCH_DEBOUNCE < now:
      
      async def defer(): # avoid deferring if we are fast
        await asyncio.sleep(2 - (time.time() - interaction.created_at)) # 2 seconds passed and still fetching = must defer

      async def fetch():
        lock = app.locks.get(local_id)
        if not lock:
          app.locks[local_id] = lock = asyncio.Lock()

        await lock.acquire()
        try: # while in queue, check if fetch debounce expired before fetching again
          grid_data = cache.get(local_id)
          if not grid_data or refresh_cache[local_id] / 10 ** 7 + app.constants.FETCH_DEBOUNCE < time.time(): 
            cache[local_id] = grid_data = await app.db.get_grid(local_id)
            refresh_cache[local_id] = refresh_at = int(time.time() * 10 ** 7)
        finally:
          lock.release()

        return grid_data, refresh_at

      loop = asyncio.get_event_loop()
      defer_task = loop.create_task(defer())
      fetch_task = loop.create_task(fetch())

      done, pending = await asyncio.wait((defer_task, fetch_task), return_when = asyncio.FIRST_COMPLETED)
      
      if defer_task in done: # 2 seconds passed
        defer_response = await interaction.response.defer()
      else:
        defer_task.cancel()
      
      if fetch_task in pending:
        await fetch_task # ensure this completes

      grid_data, refresh_at = fetch_task.result()
  
  if force: # need to return local id too for updating db
    return grid_data, defer_response, refresh_at, local_id
  return grid_data, defer_response, refresh_at # startview needs this to decide if refresh button works and exploreview too

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
      guild_data = False # indicates Unknown user / fetch failed
    cache[guild_key] = guild_data
  return guild_data

def power_sum(values, base, offset = 0):
  return sum(value * base ** (index + offset) for index, value in enumerate(values))

def validate_unicode(value, reverse = False): # 0xD000 to 0xDFFF are surrogates, unprintable/pointers
  if value >= START_SURROGATE:
    value -= MAX_SURROGATE * (2 * int(reverse) - 1) # 1 when true, -1 when false
  return value

def convert_text(text):
  base = len(string.digits) + 1
  chars =  {char : index + 1 for index, char in enumerate(string.digits)}
  temp = []
  result = ''
  for char in text:
    value = chars[char] # indexerror = missing that char in char set
    if value * base ** len(temp) + power_sum(temp, base, 1) > len(ASCII_CHARS): 
      result += ASCII_CHARS[power_sum(temp, base)]
      temp = [value]
    else:
      temp.append(value)
  result += ASCII_CHARS[power_sum(temp, base)]
  return result
    
def revert_text(text):
  base = len(string.digits) + 1
  chars = list(string.digits)
  result = ''
  for char in text:
    value = ASCII_CHARS.index(char)
    while value:
      result += chars[(value % base) - 1]
      value //= base
  return result

# def encrypt_text(text):

#   text_sum = (sum(map(ord, text)) + SALT) % MAX_UNICODE
#   state = np.random.RandomState(int(hashlib.sha256((str(text_sum) + SALT2).encode()).hexdigest(), 16) % MAX_RANDOM)
#   char_map = dict(zip(CRYPT_CHARS, state.permutation(CRYPT_CHARS)))
#   text = ''.join(char_map[i] for i in text)

#   base = len(CRYPT_CHARS) + 1
#   chars =  {char : index + 1 for index, char in enumerate(CRYPT_CHARS)}
#   temp = []
#   result = ''
#   for char in text:
#     value = chars[char] # indexerror = missing that char in char set
#     if value * base ** len(temp) + power_sum(temp, base, 1) >= MAX_UNICODE:
#       result += chr(validate_unicode(power_sum(temp, base)))
#       temp = [value]
#     else:
#       temp.append(value)
#   result += chr(validate_unicode(power_sum(temp, base)))

#   sum_pos = (sum(map(ord, result)) + text_sum + SALT3) % (len(result) - 1)
#   result = result[:sum_pos] + chr(text_sum) + result[sum_pos:]

#   return result
    
# def decrypt_text(text):

#   sum_pos = (sum(map(ord, text)) + SALT3) % (len(text) - 2)
#   state = np.random.RandomState(int(hashlib.sha256((str(ord(text[sum_pos])) + SALT2).encode()).hexdigest(), 16) % MAX_RANDOM)
#   text = text[:sum_pos] + text[sum_pos + 1:]
#   char_map = dict(zip(state.permutation(CRYPT_CHARS), CRYPT_CHARS))

#   base = len(CRYPT_CHARS) + 1
#   result = ''
#   for char in text:
#     value = validate_unicode(ord(char), True)
#     while value:
#       result += CRYPT_CHARS[(value % base) - 1]
#       value //= base

#   result = ''.join(char_map[i] for i in result)
      
#   return result

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

class MaintenanceError(Exception):
  def __init__(self, interaction):
    self.message = 'GuildID: {} | UserID: {} | Data: {}'.format(
      interaction.guild_id,
      interaction.author.id,
      interaction.data
    )

async def maintenance_check(interaction):
  if interaction.client.maintenance:
    if interaction.author.id != '364487161250316289' or interaction.client.maintenance.endswith('...'):
      await interaction.response.send('The bot is currently in maintenance mode with the reason: `{}`. Try again later (after a few hours or a day) and you can check the progress by visiting the bot\'s support server.'.format(interaction.client.maintenance), ephemeral = True)
      raise MaintenanceError(interaction)
  return True

async def before_invoke_check(interaction):
  cache = interaction.client.users
  user = interaction.author
  cache[int(user.id)] = get_username(user), user.avatar.url
  return True

def is_admin(interaction):
  return bool(
    (
      interaction.guild_id
      and interaction.author.has_permission(discohook.Permission.administrator)
    ) or not interaction.guild_id
  )

def short_text(text, max_characters, shortest = False):
  a = text
  n = max_characters
  if shortest:
    b = '...'
  else:
    b = '\n... ({0} chars left)'
  if a and n < len(a):
    b = b.format(len(a)-n)
    a = a[:n-len(b)] + b
  return a

def check_premium(interaction):
  entitlements = interaction.payload.get('entitlements')
  for i in entitlements:
    if int(i['sku_id']) == constants.PREMIUM_SKU_ID:
      return True