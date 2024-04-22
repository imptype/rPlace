import io
import time
import random
import asyncio
import discohook
import numpy as np
from PIL import Image
from . import start # .start.StartView is circular import
from ..utils.constants import COLOR_BLURPLE, CANVAS_SIZE, IMAGE_SIZE, BOT_VERSION, COLOR_RED, DEFAULT_SPAWN
from ..utils.helpers import get_grid, is_local, get_user_data, get_guild_data, convert_text, revert_text, draw_map, get_username, get_local_id#, encrypt_text

def get_values(interaction):
  c = interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')
  return (
    int(c[2]), # x
    int(c[3]), # y
    list(map(int, c[4].split('_'))), # zoom xy, list because values can be adjusted
    int(c[5]), # step
    int(c[6]), # color
    tuple(map(int, c[7].split('_'))), # size xy
    int(c[8]), # cooldown
    int(c[9]), # refresh at
    int(c[10]), # timestamp
  )

async def move(interaction, dx, dy):
  x, y, zoom, step, color, osize, _cooldown, refresh_at, _timestamp = get_values(interaction)
  ox, oy, oz = x, y, zoom

  # apply step magnitude
  dx *= step
  dy *= step

  # get grid size to get border, we use get so we can do skip draw here if same position
  grid_data, defer_response, new_refresh_at = await get_grid(interaction)
  size = grid_data[1].get('size') or CANVAS_SIZE
  xborder = size[0] - 1
  yborder = size[1] - 1

  # apply and fix if it goes beyond borders
  x += dx
  if x < 0:
    x = 0
  elif x > xborder:
    x = xborder

  y += dy
  if y < 0:
    y = 0
  elif y > yborder:
    y = yborder

  # apply fix for zoom if zoom is bigger than canvas size
  if zoom[0] > size[0]:
    zoom[0] = size[0]
  if zoom[1] > size[1]:
    zoom[1] = size[1]

  # reuse zoom, step and color in new data
  data = x, y, zoom, step, color, refresh_at
  skip_draw = x == ox and y == oy and size == osize and zoom == oz # still at same position of same map size, race condition, skip drawing
  refresh_data = grid_data, defer_response, new_refresh_at, skip_draw
  await ExploreView(interaction).update(data, refresh_data)

@discohook.button.new(emoji = '↖️', custom_id = 'upleft:v{}'.format(BOT_VERSION))
async def upleft_button(interaction):
  await move(interaction, -1, 1)

@discohook.button.new(emoji = '⬆️', custom_id = 'up:v{}'.format(BOT_VERSION))
async def up_button(interaction):
  await move(interaction, 0, 1)

@discohook.button.new(emoji = '↗️', custom_id = 'upright:v{}'.format(BOT_VERSION))
async def upright_button(interaction):
  await move(interaction, 1, 1)

color_field = discohook.TextInput('Color', 'color', hint = 'A hex string like "#ffab12" or a number <= 16777215', min_length = 1, max_length = 8, required = True)
@discohook.modal.new('Color Modal', fields = [], custom_id = 'color_modal:v{}'.format(BOT_VERSION))
async def color_modal(interaction, color):
  
  # validate timestamp
  try:
    x, y, zoom, step, old_color, _size, _cooldown, refresh_at, timestamp = get_values(interaction)
    assert int(interaction.data['custom_id'].split(':')[-1]) == int(timestamp) # compares ms timestamp with ms timestamp
  except: # index error = wrong screen, assert error = wrong timestamp
    return await interaction.response.send('The Color Modal has expired!', ephemeral = True)
  
  # validate input
  try:
    parsed_color = int(color) if color.isdecimal() else int(color.lstrip('#'), base = 16)
  except:
    return await interaction.response.send('Color `{}` is not a color!'.format(color), ephemeral = True)

  # validate range
  if not 0 <= parsed_color <= 256 ** 3 - 1:
    return await interaction.response.send('Color `{}` is out of range!'.format(color), ephemeral = True)

  # validate new color
  if parsed_color == old_color:
    return await interaction.response.send('Color `{}` is already selected!'.format(color), ephemeral = True)

  # all good, update view
  data = x, y, zoom, step, parsed_color, refresh_at
  await ExploreView(interaction).update(data)

@discohook.button.new('Color: #000000', custom_id = 'color:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.grey)
async def color_button(interaction):
  modal = discohook.Modal(
    color_modal.title,
    custom_id = '{}:{}'.format(color_modal.custom_id, get_values(interaction)[-1])    
  )
  modal.rows.append(color_field.to_dict())
  await interaction.response.send_modal(modal)

@discohook.button.new(emoji = '⬅️', custom_id = 'left:v{}'.format(BOT_VERSION))
async def left_button(interaction):
  await move(interaction, -1, 0)

def cooldown_embed(interaction, ends_at, remaining, code = 1):
  embed = interaction.message.embeds[0]
  if embed.color == COLOR_RED: # already updated embed cooldown message = trim description
    embed.description = '\n'.join(embed.description.split('\n')[:-3])
  else:
    embed.color = COLOR_RED
  embed.description += '\n\n' + '\n'.join([
    'You are on a cooldown{}'.format('!' * code),
    'Ends: <t:{}:R> (`{:.2f}s`)'.format(ends_at, remaining)
  ])
  embed.set_image('attachment://map.png')
  return embed

@discohook.button.new(emoji = '🆗', custom_id = 'place:v{}'.format(BOT_VERSION))
async def place_button(interaction):
  x, y, zoom, step, color, _size, cooldown, _refresh_at, _timestamp = get_values(interaction)

  # check cooldown here, can be out of date though but saves a request
  local_id = get_local_id(interaction) # needed so we're able to skip 1 more request
  if cooldown: # exists, greater than 0
    key = '{}{}'.format('{}:'.format(local_id) if local_id else '', interaction.author.id)
    ends_at = interaction.client.cooldowns.get(key, 0)
    now = time.time()
    if ends_at > now:
      return await interaction.response.update_message(embed = cooldown_embed(interaction, ends_at, ends_at - now))
  
  (grid, configs), defer_response, refresh_at, local_id = await get_grid(interaction, True) # force refresh

  whiteout = configs.get('whiteout')
  if whiteout: # override with whiteout color
    color = whiteout

  noedit = configs.get('noedit') or 0
  if noedit:
    return await interaction.response.send('The server admin has disabled everyone from editing the canvas.', ephemeral = True)
    
  allowed = configs.get('allowed') or None
  if allowed and allowed not in interaction.author.roles:
    return await interaction.response.send('You can\'t place because you don\'t have the whitelisted role <@&{0}> | `{0}` !'.format(allowed), ephemeral = True)

  size = configs.get('size') or CANVAS_SIZE
  xborder = size[0] - 1
  yborder = size[1] - 1

  # if flip enabled, affix y
  flip = configs.get('flip') or 0
  original_y = y # used for after placing, get the correct position even when flipped
  if flip:
    y = yborder - y

  # if place is outside of border, just do move instead, race condition when u resize grid size
  if x < 0 or x > xborder or y < 0 or y > yborder or zoom[0] > size[0] or zoom[1] > size[1]:
    return await move(interaction, 0, 0) # magnitude doesnt matter

  row = grid.get(y)
  x_key = str(x)
  if row: # reuse this bool value for later, and wont be empty, will be None or have values in it
    tile = row.get(x_key)
  else:    
    row = {}
    grid[y] = row
    tile = None

  # tile updated or already the color uses these, cooldown doesn't to save drawing time
  data = x, original_y, zoom, step, color, refresh_at
  refresh_data = (grid, configs), defer_response, refresh_at, False
  
  # validate tile is not already the same color, rare case if place button is outdated, and validate not using same reset
  reset = configs.get('reset') or 0
  if tile and tile[0] == color and ((not reset and len(tile) == configs['count']) or tile[-1] == reset):
    return await ExploreView(interaction).update(data, refresh_data, (x, y, color))

  # recheck cooldown with updated db cooldown, happens when no cooldown vs newly added cooldown
  cooldown = configs.get('cooldown') or 0 # 0 or a number
  if cooldown: # global cooldown might have cooldown in future

    # if they own the premium, ignore this if cooldown is less than 1 min long too

    # check if user is in cache, prevents one extra request
    key = '{}{}'.format('{}:'.format(local_id) if local_id else '', interaction.author.id)
    ends_at = interaction.client.cooldowns.get(key, 0)
    now = time.time()
    if ends_at > now: # still on cooldown, the below prevents unnecessary drawing too
      if defer_response:
        method = defer_response.edit
      else:
        method = interaction.response.update_message      
      return await method(embed = cooldown_embed(interaction, ends_at, ends_at - now, 2))
    # triple confirm with fetch db
    ends_at = await interaction.client.db.get_cooldown(key)
    if ends_at:
      interaction.client.cooldowns[key] = ends_at
      if defer_response:
        method = defer_response.edit
      else:
        method = interaction.response.update_message
      return await method(embed = cooldown_embed(interaction, ends_at, ends_at - now, 3))
    # insert into db and continue
    ends_at = int(time.time() + cooldown) # db limits int sizes
    await interaction.client.db.add_cooldown(key, ends_at)
    interaction.client.cooldowns[key] = ends_at

  # overwrite tile, just increment count [0 color, 1 timestamp, 2 count, 3 userid:None, 4 guildidNone]
  if tile:
    count = tile[2] + 1 # not combined with above to check the cooldown
  else:
    count = 0

  timestamp = int(time.time()) # in seconds, specifically for the pixel
  
  is_local_check = is_local(interaction)
  if is_local_check: # /local-canvas
    if interaction.guild_id: # /local-canvas in guild
      tile = [color, timestamp, count, convert_text(interaction.author.id)]
    else: # /local-canvas in DMs
      tile = [color, timestamp, count]
  else: # /canvas
    if interaction.guild_id: # /canvas in guild
      tile = [color, timestamp, count, convert_text(interaction.author.id), convert_text(interaction.guild_id)]
    else: # /canvas in DMs
      tile = [color, timestamp, count, convert_text(interaction.author.id)]

  # if reset exists, append that to the end
  if reset:
    tile.append(reset)

  # update database with new tile or create row if it does not exist
  if row or (not y and configs) : # row exists or if configs exist if y0
    task1 = interaction.client.db.update_tile(local_id, y, x, tile)
  else:
    task1 = interaction.client.db.create_row(local_id, y, x, tile)
  
  # update row/cache
  row[x_key] = tile
  task2 = ExploreView(interaction).update(data, refresh_data)

  # record log
  guild_name = None
  if interaction.guild_id:
    guild_data = await get_guild_data(interaction, interaction.guild_id)
    guild_name = guild_data[0] if guild_data else False
  
  task3 = interaction.client.db.record_log(
    get_username(interaction.author),
    interaction.author.id,
    x,
    y,
    color,
    guild_name,
    interaction.guild_id,
    is_local_check
  )

  # do all at once, reduce execution time
  await asyncio.gather(task1, task2, task3)

@discohook.button.new(emoji = '➡️', custom_id = 'right:v{}'.format(BOT_VERSION))
async def right_button(interaction):
  await move(interaction, 1, 0)

jump_fields = [
  discohook.TextInput('X', 'x', hint = 'A number in the range of 0-{}', min_length = 1, max_length = 3, required = True),
  discohook.TextInput('Y', 'y', hint = 'A number in the range of 0-{}', min_length = 1, max_length = 3, required = True)
]
@discohook.modal.new('Jump Modal', fields = [], custom_id = 'jump_modal:v{}'.format(BOT_VERSION))
async def jump_modal(interaction, x, y):

  # validate timestamp
  try:
    old_x, old_y, zoom, step, color, _size, _cooldown, refresh_at, timestamp = get_values(interaction) # message values
    assert int(interaction.data['custom_id'].split(':')[-1]) == timestamp # compares ms timestamp with ms timestamp
  except: # index error = wrong screen, assert error = wrong timestamp
    return await interaction.response.send('The Jump Modal has expired!', ephemeral = True)

  # validate integers, accepts numbers from other languages
  if not x.isdecimal():
    return await interaction.response.send('X coordinate `{}` is not a number!'.format(x), ephemeral = True)
  elif not y.isdecimal():
    return await interaction.response.send('Y coordinate `{}` is not a number!'.format(y), ephemeral = True)
  x = int(x)
  y = int(y)
  
  # validate new x y coords
  if x == old_x and y == old_y:
    return await interaction.response.send('You are already at tile `({}, {})`!'.format(x, y), ephemeral = True)

  (grid, configs), defer_response, new_refresh_at = await get_grid(interaction)
  size = configs.get('size') or CANVAS_SIZE
  xborder = size[0] - 1
  yborder = size[1] - 1
  
  # validate in range before using cached grid, included because of the above, so this is rare
  if not 0 <= x <= xborder:
    return await interaction.response.send('X coordinate `{}` is out of range!'.format(x), ephemeral = True)
  elif not 0 <= y <= yborder:
    return await interaction.response.send('Y coordinate `{}` is out of range!'.format(y), ephemeral = True)

  # always draw because jumping to new x and y coordinate while not going out of border is ensured
  skip_draw = False

  # all good, update view
  data = x, y, zoom, step, color, refresh_at
  refresh_data = (grid, configs), defer_response, new_refresh_at, skip_draw
  await ExploreView(interaction).update(data, refresh_data)

@discohook.button.new('Jump to (X, Y)', style = discohook.ButtonStyle.grey, custom_id = 'jump:v{}'.format(BOT_VERSION))
async def jump_button(interaction):

  # we use cached size here because modal response time is strictly 3 seconds
  # and we partially validate size on modal callback and it's forced when you attempt to place anyway
  _x, _y, _zoom, _step, _color, size, _cooldown, _refresh_at, timestamp = get_values(interaction)
  borders = (size[0] - 1, size[1] - 1) # xborder, yborder

  modal = discohook.Modal(
    jump_modal.title,
    custom_id = '{}:{}'.format(jump_modal.custom_id, timestamp)
  )
  for i, v in enumerate(jump_fields):
    modal.add_field(
      v.label,
      v.field_id,
      hint = v.hint.format(borders[i]),
      min_length = v.min_length,
      max_length = v.max_length,
      required = v.required
    )
  await interaction.response.send_modal(modal)

@discohook.button.new(emoji = '↙️', custom_id = 'downleft:v{}'.format(BOT_VERSION))
async def downleft_button(interaction):
  await move(interaction, -1, -1)

@discohook.button.new(emoji = '⬇️', custom_id = 'down:v{}'.format(BOT_VERSION))
async def down_button(interaction):
  await move(interaction, 0, -1)

@discohook.button.new(emoji = '↘️', custom_id = 'downright:v{}'.format(BOT_VERSION))
async def downright_button(interaction):
  await move(interaction, 1, -1)

@discohook.button.new('Back To Home', style = discohook.ButtonStyle.grey, custom_id = 'return:v{}'.format(BOT_VERSION))
async def return_button(interaction):
  await start.StartView(interaction).update() # cant skip draw here because image changes in size

step_sizes = (1, 2, 3, 4, 5, 10, 20, 50, 100, 250)
step_options = [
  discohook.SelectOption(str(i), str(i)) 
  for i in step_sizes
]
@discohook.select.text(step_options, custom_id = 'step_select:v{}'.format(BOT_VERSION))
async def step_select(interaction, values):

  # using this to validate wouldn't matter anyway
  x, y, zoom, old_step, color, _size, _cooldown, refresh_at, _timestamp = get_values(interaction)
  step = int(values[0])
  
  # validate new step
  if step == old_step:
    return await interaction.response.send('Step size `{}` is already selected!'.format(step), ephemeral = True)

  # update view, refresh data is handled over there
  data = x, y, zoom, step, color, refresh_at
  await ExploreView(interaction).update(data)

zoom_sizes = (3, 7, 11, 15, 19, 25, 49, 75, 99, 127)
zoom_options = [
  discohook.SelectOption('{0}x{0}'.format(i), '{}_{}'.format(i, i))
  for i in zoom_sizes
]
@discohook.select.text(zoom_options, placeholder = 'zoom_select', custom_id = 'zoom_select:v{}'.format(BOT_VERSION))
async def zoom_select(interaction, values):
  x, y, old_zoom, step, color, _size, _cooldown, refresh_at, _timestamp = get_values(interaction)
  zoom = list(map(int, values[0].split('_')))
  
  # validate new zoom
  if zoom == old_zoom:
    return await interaction.response.send('Zoom `{}x{}` is already selected!'.format(*zoom), ephemeral = True)

  # get cached grid size before we draw it to see if it goes beyond border
  grid_data, defer_response, new_refresh_at = await get_grid(interaction)

  size = grid_data[1].get('size') or CANVAS_SIZE
  xborder = size[0] - 1
  yborder = size[1] - 1

  # fix if it goes beyond new borders
  if zoom[0] > size[0]: # drawing would be out of bounds otherwise
    zoom[0] = size[0] # no need to ensure odd because section draw is smart
  if zoom[1] > size[1]:
    zoom[1] = size[1]

  # validate new zoom again, rare
  if zoom == old_zoom:
    if defer_response:
      method = defer_response.send
    else:
      method = interaction.response.send
    return await method('Zoom `{}x{}` is already selected!!'.format(*zoom), ephemeral = True)
  
  if x < 0:
    x = 0
  elif x > xborder:
    x = xborder

  if y < 0:
    y = 0
  elif y > yborder:
    y = yborder

  # reuse zoom, step and color in new data
  skip_draw = False # because we changed zoom size, skip draw is always false
  refresh_data = grid_data, defer_response, new_refresh_at, skip_draw
  
  # update view
  data = x, y, zoom, step, color, refresh_at
  await ExploreView(interaction).update(data, refresh_data)

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

  async def setup(self, data, refresh_data, extra): # ainit

    if data:
      x, y, zoom, step, color, old_refresh_at = data
    else: # default, first move
      x = 0 # currently not hardcoded with DEFAULT_SPAWN since its unnecessary
      y = 0
      zoom = [11, 11]
      step = 1
      color = 0
    timestamp = int(time.time() * 10 ** 7) # create new timestamp
      
    if refresh_data: # from button place, movement (border checks), jump modal (border checks), zoom select (update border checks before redraw)
      (grid, configs), self.defer_response, refresh_at, skip_draw = refresh_data # refresh comparison is skipped, see below, because we just updated grid from place
    else:
      (grid, configs), self.defer_response, refresh_at = await get_grid(self.interaction) # can be inaccurate/not updated/go back in time so we check again
      skip_draw = False
      if data: # only if data exists/clicked component on this view, step select, color modal have a chance not to refresh
        if old_refresh_at > refresh_at: # if old/second instance greater than current refresh, it means current/first instance is outdated
          (grid, configs), self.defer_response, refresh_at, _local_id = await get_grid(self.interaction, force = True)
        else:
          skip_draw = True

    flip = configs.get('flip') or 0
    size = configs.get('size') or CANVAS_SIZE # can sneakily be None, unreliant with db
    spawn = configs.get('spawn') or DEFAULT_SPAWN
    whiteout = configs.get('whiteout')
    if whiteout: # override color to be this instead
      color = whiteout
    xborder = size[0] - 1
    yborder = size[1] - 1
    if not data: # only if canvas started:
      if spawn != DEFAULT_SPAWN:
        if spawn[0] == '?':
          x = random.randint(0, xborder)
        else:
          x = int(spawn[0])
          if x > xborder:
            x = xborder
        if spawn[1] == '?':
          y = random.randint(0, yborder)
        else:
          y = int(spawn[-1])
          if y > yborder:
            y = yborder          
      if flip:
        y = yborder # start from top instead of at 0
    if flip:
      vy = yborder - y
    else:
      vy = y # visually y, not same for y used in border checks, only used to get the selected pixel
    
    pixel = grid.get(vy, {}).get(str(x))
    reset = configs.get('reset') or 0

    # [0 color, 1 timestamp, 2 count, 3 userid/None when local canvas, 4 guildid/None when local canvas or global canvas dms]
    thumbnail_url = None
    if pixel and ((not reset and len(pixel) == configs['count']) or pixel[-1] == reset): # dont show data if pixels placed before reset
      place_disabled = color == pixel[0] # selecting same color

      text = '🎨 #{:06x}'.format(pixel[0])

      if self.interaction.guild_id: # not in dms

        user_id = revert_text(pixel[3])
        tasks = [get_user_data(self.interaction, user_id)]

        is_local_check = is_local(self.interaction)
        if not is_local_check: # not local canvas command
          if len(pixel) == 5: # from user DMs, 0 1 2 3, 4 guild id not included
            guild_id = revert_text(pixel[4])
            tasks.append(get_guild_data(self.interaction, guild_id))
        
        results = await asyncio.gather(*tasks) # point is to save time by doing both requests at the same time
        
        user_data = results[0] # contains username, avatar_url else None
        text += '\n🧍 {} | <@{}>'.format(
          user_data[0] if user_data else '*Unknown User*', # deleted accounts probably
          user_id
        )

        if is_local_check: # if local guild canvas, show user avatar url as thumbnail
          if len(pixel) == 4: # local canvas in guild
            if user_data:
              thumbnail_url = user_data[1]
        else: # this is global canvas, include guild as well, no matter if DMs
          if len(pixel) == 4: # from user DMs, 0 1 2 3, guild id not included
            guild_text = '*Bot\'s DMs*'
          else:
            guild_data = results[1] # None or Name, Hash
            if guild_data:
              guild_name, icon_hash = guild_data
              thumbnail_url = 'https://cdn.discordapp.com/icons/{}/{}.png'.format(guild_id, icon_hash)
            else:
              guild_name = '*Unknown Server*'
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
      'Selecting Tile ({}, {})'.format(x, vy),
      description = text,
      color = COLOR_RED if extra else COLOR_BLURPLE
    )
    if extra: # same color from place
      self.embed.description += '\n\n' + 'The tile `({}, {})` is already the color `#{:06x}`!'.format(x, y, color)
    if thumbnail_url:
      self.embed.set_thumbnail(thumbnail_url)

    if not data: # not sure if this is needed here
      if zoom[0] > size[0]:
        zoom[0] = size[0] # fix starter zoom
      if zoom[1] > size[1]:
        zoom[1] = size[1]
    cooldown = configs.get('cooldown') or 0 # same here

    if skip_draw: # saves redrawing pointlessly if it hasn't refreshed
      self.embed.set_image('attachment://map.png')
    else:
      # calculate pointer cursor
      radiusx = zoom[0]//2
      radiusy = zoom[1]//2
      
      pointer = [radiusx, radiusy]

      startx = x - radiusx
      if startx < 0:
        startx = 0
        pointer[0] = x
      elif x + radiusx > xborder:
        startx = size[0] - zoom[0]
        pointer[0] = zoom[0] - (size[0] - x)

      starty = y - radiusy
      if starty < 0:
        starty = 0
        pointer[1] = zoom[1] - 1 - y
      elif y + radiusy > yborder:
        starty = size[1] - zoom[1]
        pointer[1] = yborder - y

      # draw canvas
      app = self.interaction.client
      def blocking():
        sconfigs = configs.copy()
        sconfigs['size'] = zoom # needed for the "reset" attribute
        bim = draw_map(grid, sconfigs, startx, starty)

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

        factor = IMAGE_SIZE // max(size)
        resize = (zoom[0] * factor, zoom[1] * factor)
        if size != resize:
          im = im.resize(resize, Image.Resampling.NEAREST)        
        buffer = io.BytesIO()
        im.save(buffer, 'PNG')
        return buffer
      
      buffer = await asyncio.to_thread(blocking)

      # get pixel data from grid above and format it into the embed below 
      self.embed.set_image(discohook.File('map.png', content = buffer.getvalue()))

    dynamic_upleft_button = discohook.Button(
      emoji = upleft_button.emoji,
      custom_id = '{}:{}:{}:{}:{}:{}:{}:{}:{}:{}'.format(upleft_button.custom_id, x, y, '_'.join(map(str, zoom)), step, color, '_'.join(map(str, size)), cooldown, refresh_at, timestamp),
      disabled = not x or y == yborder
    )
    
    dynamic_up_button = discohook.Button(
      emoji = up_button.emoji,
      custom_id = up_button.custom_id + ':',
      disabled = y == yborder
    )
        
    dynamic_upright_button = discohook.Button(
      emoji = upright_button.emoji,
      custom_id = upright_button.custom_id + ':',
      disabled = x == xborder or y == yborder
    )
        
    dynamic_left_button = discohook.Button(
      emoji = left_button.emoji,
      custom_id = left_button.custom_id + ':',
      disabled = not x
    )
        
    dynamic_right_button = discohook.Button(
      emoji = right_button.emoji,
      custom_id = right_button.custom_id + ':',
      disabled = x == xborder
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
      disabled = x == xborder or not y
    )
    
    noedit = configs.get('noedit') or 0
    allowed = configs.get('allowed') or None
    dynmaic_place_button = discohook.Button(
      emoji = place_button.emoji,
      custom_id = place_button.custom_id + ':',
      disabled = bool(noedit) or place_disabled or (allowed and allowed not in map(lambda x: x.id, self.interaction.author.roles))
    )

    dynamic_color_button = discohook.Button(
      'Color: #{:06x}'.format(color),
      custom_id = color_button.custom_id + ':',
      style = color_button.style,
      disabled = whiteout is not None
    )

    dynamic_step_select = discohook.Select(
      discohook.SelectType.text,
      placeholder = 'Step Size: {}'.format(step),
      custom_id = step_select.custom_id + ':'      
    )
    options = []
    max_size = max(size)
    for option in step_select.options:
      if int(option.value) < max_size:
        options.append(option)
      else:
        options.append(discohook.SelectOption(str(max_size), str(max_size)))
        break
    dynamic_step_select.options = options

    dynamic_zoom_select = discohook.Select(
      discohook.SelectType.text,
      placeholder = 'Zoom: {}x{}'.format(*zoom),
      custom_id = zoom_select.custom_id + ':'      
    )
    options = []
    small_size = min(size)
    small_index = int(size[0] > size[1])
    for option in zoom_select.options:
      zoom_value = int(option.value.split('_')[0])
      if zoom_value < small_size: # add square
        options.append(option)
      else:
        zoom_values = (
          small_index and zoom_value or size[0],
          small_index and size[1] or zoom_value
        )
        if zoom_value < max_size:
          options.append(discohook.SelectOption('{}x{}'.format(*zoom_values), '_'.join(map(str, zoom_values))))
        else:
          options.append(discohook.SelectOption('{}x{}'.format(*size), '_'.join(map(str, size))))
          break
    dynamic_zoom_select.options = options
      
    self.add_buttons(dynamic_upleft_button, dynamic_up_button, dynamic_upright_button, dynamic_color_button)
    self.add_buttons(dynamic_left_button, dynmaic_place_button, dynamic_right_button, jump_button)
    self.add_buttons(dynamic_downleft_button, dynamic_down_button, dynamic_downright_button, return_button)
    self.add_select(dynamic_step_select)
    self.add_select(dynamic_zoom_select)

  async def update(self, data = None, refresh_data = None, extra = None): # done in update function, saves pointer memory maybe
    await self.setup(data, refresh_data, extra) # refresh_data is any component here, excludes from startview
    if self.defer_response: # extra is pixel was already placed, it needs refresh
      await self.defer_response.edit(embed = self.embed, view = self)
    else:
      await self.interaction.response.update_message(embed = self.embed, view = self)