import io
import asyncio
import discohook
from PIL import Image
import numpy as np

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