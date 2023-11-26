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

"""
async def draw_grid():
  im = Image.new('RGB', (1000, 1000), color = (255, 153, 255))
  im = im.resize((1024, 1024), Image.Resampling.NEAREST)
  
  # Save
  buffer = io.BytesIO()
  im.save(buffer, 'PNG')
  return buffer
"""
'''
def get_button_name(interaction):
  for row in interaction.payload['message']['components']:
    for component in row['components']:
      if component['custom_id'] == interaction.data['custom_id']:
        return component['emoji']['name']

def get_cursor(interaction):
  for row in interaction.payload['message']['components']:
    for component in row['components']:
      if component['custom_id'].startswith('place'):
        return tuple(map(int, component['custom_id'].split(':')[2:]))

def blocking(grid, cursor = None): # pillow blocking code

  # Create image with numpy array directly
  im = Image.fromarray(np.array(grid).astype('uint8')).convert('RGB')

  # Draw cursor if exists
  if cursor:
    border = len(grid)
    im = im.resize((border * 8, border * 8), Image.Resampling.NEAREST)
    x, y = cursor[:2]
    color = (0, 187, 212) # (100, 100, 100)
    pixels = [
      (0, 0), (1, 0), (2, 0), (0, 1), (0, 2), # top left
      (5, 0), (6, 0), (7, 0), (7, 1), (7, 2), # top right
      (0, 5), (0, 6), (0, 7), (1, 7), (2, 7), # bottom left
      (7, 5), (7, 6), (5, 7), (6, 7), (7, 7)  # bottom right
    ]
    for p in pixels:
      im.putpixel((x*8 + p[0], border*8 -(y+1)*8 + p[1]), color)

  # Resize to decent quality
  width, height = im.size
  if width < 1024 and height < 1024:
    im = im.resize((1024, 1024), Image.Resampling.NEAREST)
  
  # Save
  buffer = io.BytesIO()
  im.save(buffer, 'PNG')
  return buffer

def convert_cell(i):
  """
  Converts cell of json data into RGB tuple
  """
  if isinstance(i, dict):
    return ((i['c'] >> 16) & 255, (i['c'] >> 8) & 255, i['c'] & 255)
  return (255, 255, 255)

def convert_grid(old_grid):
  """
  Converts grid/section of json data into grid of colors
  Pillow draws from up-down, so that's why it's reversed
  """
  n = len(old_grid)
  grid = [[None] * n for _ in range(n)]
  for y, row in enumerate(old_grid):
    for x, cell in enumerate(row):
      grid[x][y] = convert_cell(cell)
  return list(reversed(grid))

def get_section(grid, cursor):
  """
  Do some math to get a section of the grid
  Position is renamed to pointer because it's being adjusted by zoom
  """
  x, y, zoom = cursor[:3]
  border = len(grid)
  radius = int(zoom/2)
  pointer = [radius] * 2
  startx = x - radius
  if startx < 0:
    startx = 0
    pointer[0] = x
  elif x + radius > border - 1:
    startx = border - zoom
    pointer[0] = zoom - (border - x)
  starty = y - radius
  if starty < 0:
    starty = 0
    pointer[1] = y
  elif y + radius > border - 1:
    starty = border - zoom
    pointer[1] = zoom - (border - y)
  section = np.array(grid)[startx:startx+zoom, starty:starty+zoom].tolist()
  return section, (*pointer, zoom, *cursor[3:])

async def draw_map(interaction, cursor = None):
  """
  cursor : (x, y, z, s, c) - if empty it means draw whole map
  """
  grid = interaction.client.grid
  if cursor:
    grid, cursor = get_section(grid, cursor)
  loop = asyncio.get_event_loop()
  grid = convert_grid(grid)
  buffer = await loop.run_in_executor(None, blocking, grid, cursor)
  buffer.seek(0)
  return discohook.File('map.png', content = buffer)

def locale_text(interaction, key, *format_args):
  text = interaction.client.texts.get(interaction.locale, interaction.client.texts['en'])[key]
  if format_args:
    text = text.format(*format_args)
  return text

def locale_button(interaction, button, *format_args):
  label = locale_text(interaction, button.label)
  if format_args:
    label = label.format(*format_args)
  custom_id = button.custom_id + ':dynamic'
  return discohook.Button(label, url = button.url, style = button.style, disabled = button.disabled, emoji = button.emoji, custom_id = custom_id)

def locale_select(interaction, select, *format_args):
  placeholder = locale_text(interaction, select.placeholder)
  if format_args:
    placeholder = placeholder.format(*format_args)
  custom_id = select.custom_id + ':dynamic'
  return discohook.Select(select.options, placeholder = placeholder, custom_id = custom_id) 

def before_invoke(interaction):
  interaction.client.users[int(interaction.author.id)] = interaction.author
  # guilds are only cached when fetched because interaction data only holds guild id
  # interaction.client.guilds[int(interaction.guild_id)] = interaction.guild

def plural_suffix(n):
  if n == 1:
    return ''
  return 's'

'''