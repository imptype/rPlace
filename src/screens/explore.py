import io
import time
import string
import asyncio
import discohook
import numpy as np
from PIL import Image
from . import start # .start.StartView is circular import
from ..utils.constants import COLOR_BLURPLE, CANVAS_SIZE, IMAGE_SIZE
from ..utils.helpers import get_grid, is_local, get_username, get_guild_name, convert_text, revert_text, draw_map

BORDER = CANVAS_SIZE - 1

def get_values(interaction):
  return tuple(map(int, interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[2:]))

async def move(interaction, dx, dy):
  x, y, zoom, step, color, _timestamp = get_values(interaction)

  # apply step magnitude
  dx *= step
  dy *= step

  # apply and fix if it goes beyond borders
  x += dx
  if x < 0:
    x = 0
  elif x > BORDER:
    x = BORDER

  y += dy
  if y < 0:
    y = 0
  elif y > BORDER:
    y = BORDER

  # reuse zoom, step and color in new data
  data = x, y, zoom, step, color
  await ExploreView(interaction).update(data)

@discohook.button.new(emoji = '↖️', custom_id = 'upleft:v0.0')
async def upleft_button(interaction):
  await move(interaction, -1, 1)

@discohook.button.new(emoji = '⬆️', custom_id = 'up:v0.0')
async def up_button(interaction):
  await move(interaction, 0, 1)

@discohook.button.new(emoji = '↗️', custom_id = 'upright:v0.0')
async def upright_button(interaction):
  await move(interaction, 1, 1)


color_field = discohook.TextInput('Color', 'color', hint = 'A hex string like "#ffab12" or a number <= 16777215.', min_length = 1, max_length = 8, required = True)
@discohook.modal.new('Color Modal', fields = [], custom_id = 'color_modal:v0.0')
async def color_modal(interaction, color):
  
  # validate timestamp
  try:
    x, y, zoom, step, _color, timestamp = get_values(interaction)
    assert int(interaction.data['custom_id'].split(':')[-1]) == int(timestamp) # compares ms timestamp with ms timestamp
  except: # index error = wrong screen, assert error = wrong timestamp
    return await interaction.response.send('The Jump Modal has expired!', ephemeral = True)
  
  # validate input
  try:
    parsed_color = int(color) if color.isdecimal() else int(color.lstrip('#'), base = 16)
  except:
    return await interaction.response.send('Color `{}` is not a color!'.format(color), ephemeral = True)

  # validate range
  if not 0 <= parsed_color <= 256 ** 3 - 1:
    return await interaction.response.send('Color `{}` is out of range!'.format(color), ephemeral = True)
  
  # all good, update view
  data = x, y, zoom, step, parsed_color
  await ExploreView(interaction).update(data)

@discohook.button.new('Color: #000000', custom_id = 'color:v0.0', style = discohook.ButtonStyle.grey)
async def color_button(interaction):
  modal = discohook.Modal(
    color_modal.title,
    custom_id = '{}:{}'.format(color_modal.custom_id, get_values(interaction)[-1])    
  )
  modal.rows.append(color_field.to_dict())
  await interaction.response.send_modal(modal)

@discohook.button.new(emoji = '⬅️', custom_id = 'left:v0.0')
async def left_button(interaction):
  await move(interaction, -1, 0)

@discohook.button.new(emoji = '🆗', custom_id = 'place:v0.0')
async def place_button(interaction):
  x, y, zoom, step, color, _timestamp = get_values(interaction)
  
  grid, local_id = await get_grid(interaction, True) # force refresh

  row = grid.get(y)
  x_key = str(x)
  if row: # reuse this bool value for later, and wont be empty, will be None or have values in it
    tile = row.get(x_key)
  else:    
    row = {}
    grid[y] = row
    tile = None

  timestamp = int(time.time()) # in seconds, specifically for the pixel

  # overwrite tile, just increment count [0 color, 1 timestamp, 2 count, 3 userid:None, 4guildidNone]
  if tile:
    count = tile[2] + 1
  else:
    count = 0
  
  if is_local(interaction): # /local-canvas
    if interaction.guild_id: # /local-canvas in guild
      tile = [color, timestamp, count, convert_text(interaction.author.id, string.digits)]
    else: # /local-canvas in DMs
      tile = [color, timestamp, count]
  else: # /canvas
    if interaction.guild_id: # /canvas in guild
      tile = [color, timestamp, count, convert_text(interaction.author.id, string.digits), convert_text(interaction.guild_id, string.digits)]
    else: # /canvas in DMs
      tile = [color, timestamp, count, convert_text(interaction.author.id, string.digits)]

  # update database with new tile or create row if it does not exist
  if row:
    await interaction.client.db.update_tile(local_id, y, x, tile)
  else:
    await interaction.client.db.create_row(local_id, y, x, tile)
  
  # update row/cache
  row[x_key] = tile
  data = x, y, zoom, step, color
  await ExploreView(interaction).update(data)

@discohook.button.new(emoji = '➡️', custom_id = 'right:v0.0')
async def right_button(interaction):
  await move(interaction, 1, 0)

jump_fields = [
  discohook.TextInput('X', 'x', hint = 'A number in the range of 0-{}'.format(BORDER), min_length = 1, max_length = 3, required = True),
  discohook.TextInput('Y', 'y', hint = 'A number in the range of 0-{}'.format(BORDER), min_length = 1, max_length = 3, required = True)
]
@discohook.modal.new('Jump Modal', fields = [], custom_id = 'jump_modal:v0.0')
async def jump_modal(interaction, x, y):

  # validate timestamp
  try:
    _x, _y, zoom, step, color, timestamp = get_values(interaction)
    assert int(interaction.data['custom_id'].split(':')[-1]) == int(timestamp) # compares ms timestamp with ms timestamp
  except: # index error = wrong screen, assert error = wrong timestamp
    return await interaction.response.send('The Jump Modal has expired!', ephemeral = True)

  # validate integers, accepts numbers from other languages
  if not x.isdecimal():
    return await interaction.response.send('X coordinate `{}` is not a number!'.format(x), ephemeral = True)
  elif not y.isdecimal():
    return await interaction.response.send('Y coordinate `{}` is not a number!'.format(y), ephemeral = True)
  x = int(x)
  y = int(y)

  # validate in range, included because of the above, so this is rare
  if not 0 <= x <= BORDER:
    return await interaction.response.send('X coordinate `{}` is out of range!'.format(x), ephemeral = True)
  elif not 0 <= y <= BORDER:
    return await interaction.response.send('Y coordinate `{}` is out of range!'.format(y), ephemeral = True)
  
  # all good, update view
  data = x, y, zoom, step, color
  await ExploreView(interaction).update(data)

@discohook.button.new('Jump to (X, Y)', style = discohook.ButtonStyle.grey, custom_id = 'jump:v0.0')
async def jump_button(interaction):
  modal = discohook.Modal(
    jump_modal.title,
    custom_id = '{}:{}'.format(jump_modal.custom_id, get_values(interaction)[-1])    
  )
  for i in jump_fields:
    modal.rows.append(i.to_dict())
  await interaction.response.send_modal(modal)

@discohook.button.new(emoji = '↙️', custom_id = 'downleft:v0.0')
async def downleft_button(interaction):
  await move(interaction, -1, -1)

@discohook.button.new(emoji = '⬇️', custom_id = 'down:v0.0')
async def down_button(interaction):
  await move(interaction, 0, -1)

@discohook.button.new(emoji = '↘️', custom_id = 'downright:v0.0')
async def downright_button(interaction):
  await move(interaction, 1, -1)

@discohook.button.new('Back To Home', style = discohook.ButtonStyle.grey, custom_id = 'return:v0.0')
async def return_button(interaction):
  await start.StartView(interaction).update()

step_options = [1, 2, 3, 4, 5, 10, 20, 50, 100, 250]
@discohook.select.text([discohook.SelectOption('', '')], placeholder = 'Select a step size...', custom_id = 'step_select:v0.0')
async def step_select(interaction, values):
  await interaction.response.send('clicked step select {}'.format(values))

zoom_options = [
  discohook.SelectOption('{0}x{0}'.format(i), str(i))
  for i in [3, 7, 11, 15, 19, 25, 49, 75, 99, 128]#, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51]
]
@discohook.select.text(zoom_options, placeholder = 'zoom_select', custom_id = 'zoom_select:v0.0')
async def zoom_select(interaction, values):
  await interaction.response.send('clicked zoom select {}'.format(values))

class ExploreView(discohook.View):
  def __init__(self, interaction = None): # View is persistent if args not given
    super().__init__()

    if interaction:
      self.interaction = interaction

    else: # Persistent
      self.add_buttons(upleft_button, up_button, upright_button, color_button)
      self.add_buttons(left_button, place_button, right_button, jump_button)
      self.add_buttons(downleft_button, down_button, downright_button, return_button)
      self.add_select(step_select)
      self.add_select(zoom_select)

  async def setup(self, data = None): # ainit

    if data:
      x, y, zoom, step, color = data
    else: # default, first move
      x = 0
      y = 0
      zoom = 11
      step = 1
      color = 0
    timestamp = int(time.time() * 1000) # create new timestamp
      
    app = self.interaction.client
    grid = await get_grid(self.interaction)
    pixel = grid.get(y, {}).get(str(x))

    # [0 color, 1 timestamp, 2 count, 3 userid/None when local canvas, 4 guildid/None when local canvas or global canvas dms]
    if pixel:
      place_disabled = color == pixel[0] # selecting same color

      text = '🎨 #{:06x}'.format(pixel[0])

      if self.interaction.guild_id: # not in dms

        user_id = revert_text(pixel[3], string.digits)
        tasks = [get_username(self.interaction, user_id)]

        is_local_check = is_local(self.interaction)
        if is_local_check: # local canvas command
          if len(pixel) == 4: # local canvas within a guild            
            place_disabled = place_disabled and self.interaction.author.id == user_id
        else: # not local canvas command
          place_disabled = place_disabled and self.interaction.author.id == user_id
          if len(pixel) == 5: # from user DMs, 0 1 2 3, 4 guild id not included
            guild_id = revert_text(pixel[4], string.digits)
            tasks.append(get_guild_name(self.interaction, guild_id))
        
        results = await asyncio.gather(*tasks) # point is to save time by doing both requests at the same time
        
        username = results[0]
        text += '\n🧍 {} | <@{}>'.format(
          username or '*Unknown User*',
          user_id 
        )

        if not is_local_check: # this is global canvas, include guild as well, no matter if DMs
          if len(pixel) == 4: # from user DMs, 0 1 2 3, guild id not included
            guild_text = '*Bot\'s DMs*'
          else:
            guild_name = results[1] or '*Unknown Server*'
            url = 'https://discord.com/servers/{}'.format(guild_id)
            guild_text = '[{}]({})'.format(guild_name, url)
          text += '\n🏠 {}'.format(guild_text)

      text += '\n⏰ <t:{}:R>'.format(pixel[1])

    else:
      place_disabled = False
      if self.interaction.guild_id:
        text = 'Nobody has painted here yet.'
      else:
        text = 'You haven\'t painted here yet.'

    self.embed = discohook.Embed(
      'Selecting Tile ({}, {})'.format(x, y),
      description = text,
      color = COLOR_BLURPLE
    )

    # calculate pointer cursor
    radius = int(zoom/2)
    pointer = [radius] * 2

    startx = x - radius
    if startx < 0:
      startx = 0
      pointer[0] = x
    elif x + radius > BORDER:
      startx = CANVAS_SIZE - zoom
      pointer[0] = zoom - (CANVAS_SIZE - x)

    starty = y - radius
    if starty < 0:
      starty = 0
      pointer[1] = zoom - 1 - y
    elif y + radius > BORDER:
      starty = CANVAS_SIZE - zoom
      pointer[1] = BORDER - y

    # draw canvas
    def blocking():
      bim = draw_map(grid, zoom, startx, starty)

      # draw cursor if not cached
      n = 8 # cursor is 8px in size
      if not app.cursor:
        s = 3 # arrow width is 3px
        c = (0, 187, 212, 255) # blue tint
        a = np.full((n, n, 4), (0, 0, 0, 0), np.uint8)

        # widths, 3px top left, right, bottom, right
        a[0, :s] = c 
        a[-1, :s] = c
        a[0, -s:] = c
        a[-1, -s:] = c

        # heights, 2px
        a[1:s, 0] = c
        a[1:s, -1] = c
        a[-s:-1, 0] = c
        a[-s:-1, -1] = c

        cim = Image.fromarray(a)
        app.cursor = cim
      
      im = bim.resize(np.array(bim.size) * n, Image.Resampling.NEAREST)
      im.paste(app.cursor, tuple(np.array(pointer) * n), app.cursor)  # assuming max size doesn't exceed 128, this is fine
      im = im.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST)
      buffer = io.BytesIO()
      im.save(buffer, 'PNG')
      return buffer
    
    buffer = await asyncio.to_thread(blocking)

    # get pixel data from grid above and format it into the embed below 
    self.embed.set_image(discohook.File('map.png', content = buffer.getvalue()))

    dynamic_upleft_button = discohook.Button(
      emoji = upleft_button.emoji,
      custom_id = '{}:{}:{}:{}:{}:{}:{}'.format(upleft_button.custom_id, x, y, zoom, step, color, timestamp),
      disabled = not x or y == BORDER
    )
    
    dynamic_up_button = discohook.Button(
      emoji = up_button.emoji,
      custom_id = up_button.custom_id + ':',
      disabled = y == BORDER
    )
        
    dynamic_upright_button = discohook.Button(
      emoji = upright_button.emoji,
      custom_id = upright_button.custom_id + ':',
      disabled = x == BORDER or y == BORDER
    )
        
    dynamic_left_button = discohook.Button(
      emoji = left_button.emoji,
      custom_id = left_button.custom_id + ':',
      disabled = not x
    )
        
    dynamic_right_button = discohook.Button(
      emoji = right_button.emoji,
      custom_id = right_button.custom_id + ':',
      disabled = x == BORDER
    )
        
    dynamic_downleft_button = discohook.Button(
      emoji = downleft_button.emoji,
      custom_id = downleft_button.custom_id + ':',
      disabled = not x or not y
    )
        
    dynamic_down_button = discohook.Button(
      emoji = down_button.emoji,
      custom_id = down_button.custom_id + ':',
      disabled = not y
    )
        
    dynamic_downright_button = discohook.Button(
      emoji = downright_button.emoji,
      custom_id = downright_button.custom_id + ':',
      disabled = x == BORDER or not y
    )
    
    dynmaic_place_button = discohook.Button(
      emoji = place_button.emoji,
      custom_id = place_button.custom_id + ':',
      disabled = place_disabled
    )

    dynamic_color_button = discohook.Button(
      'Color: #{:06x}'.format(color),
      custom_id = color_button.custom_id + ':',
      style = color_button.style
    )

    dynamic_step_select = discohook.Select(
      discohook.SelectType.text,
      placeholder = 'Step Size: {}'.format(step),
      custom_id = step_select.custom_id + ':'      
    )
    dynamic_step_select.options = [
      discohook.SelectOption(str(i), str(i))
      for i in step_options
    ]
      
    self.add_buttons(dynamic_upleft_button, dynamic_up_button, dynamic_upright_button, dynamic_color_button)
    self.add_buttons(dynamic_left_button, dynmaic_place_button, dynamic_right_button, jump_button)
    self.add_buttons(dynamic_downleft_button, dynamic_down_button, dynamic_downright_button, return_button)
    self.add_select(dynamic_step_select)
    self.add_select(zoom_select)

  async def update(self, data = None): # done in update function, saves pointer memory maybe
    await self.setup(data)
    await self.interaction.response.update_message(embed = self.embed, view = self)