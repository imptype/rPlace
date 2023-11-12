import time
import discohook
from . import start # .start.StartView is circular import
from ..extras import constants, utils

async def move(interaction, x, y):
  utils.before_invoke(interaction)
  await interaction.client.active_users.update(int(interaction.author.id))

  cursor = utils.get_cursor(interaction)
  border = interaction.client.db.size - 1 # 240 is the last stepable tile
  before = pos_x, pos_y = cursor[:2]
  step = cursor[-2]
  x *= step
  y *= step

  pos_x += x
  if pos_x > border: # went over
    pos_x = border
  elif pos_x < 0: # went under
    pos_x = 0

  pos_y += y
  if pos_y > border:
    pos_y = border
  elif pos_y < 0:
    pos_y = 0

  if before == (pos_x, pos_y): # no movement = reached border
    return await interaction.response(utils.locale_text(interaction, 'reached_border'), ephemeral = True)

  cursor = (pos_x, pos_y, *cursor[2:])
  view = ExploreView(interaction, cursor)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw())

@discohook.button(emoji = '↖️', custom_id = 'upleft:v0.0')
async def upleft_button(interaction):
  await move(interaction, -1, 1)

@discohook.button(emoji = '⬆️', custom_id = 'up:v0.0')
async def up_button(interaction):
  await move(interaction, 0, 1)

@discohook.button(emoji = '↗️', custom_id = 'upright:v0.0')
async def upright_button(interaction):
  await move(interaction, 1, 1)

@discohook.modal('Color Modal', [], custom_id = 'colormodal:v0.0')
async def color_modal(interaction, x):
  utils.before_invoke(interaction)
  try:
    color = int(x) if x.isnumeric() else int(x.lstrip('#'), base = 16)
  except:
    return await interaction.response(utils.locale_text(interaction, 'color_number_error', x), ephemeral = True)
  if not 0 <= color <= 256 ** 3 - 1:
    return await interaction.response(utils.locale_text(interaction, 'color_range_error', x), ephemeral = True)
  cursor = utils.get_cursor(interaction)
  cursor = (*cursor[:-1], color)
  view = ExploreView(interaction, cursor)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw()) 

@discohook.button('color_button', custom_id = 'color:v0.0', style = discohook.ButtonStyle.grey)
async def color_button(interaction):
  utils.before_invoke(interaction)
  modal = discohook.Modal(color_modal.title, custom_id = color_modal.custom_id + ':dynamic') # callback should point up above
  modal.add_field(
    utils.locale_text(interaction, 'color_input'), 'x', required = True,
    hint = utils.locale_text(interaction, 'color_hint'),
    min_length = 1, max_length = 8
  )
  await interaction.send_modal(modal) 

@discohook.button(emoji = '⬅️', custom_id = 'left:v0.0')
async def left_button(interaction):
  await move(interaction, -1, 0)

@discohook.button(emoji = '🆗', custom_id = 'place:v0.0')
async def place_button(interaction):
  utils.before_invoke(interaction)
  #cooldown = interaction.client.cooldowns.get(interaction.author.id)
  #if cooldown and cooldown + 20 > time.time():
  #  return await interaction.response(utils.locale_text(interaction, 'cooldown_text'), ephemeral = True)
  cursor = utils.get_cursor(interaction)
  x, y = cursor[:2]
  c = cursor[-1]
  tile = interaction.client.grid[x][y]
  if tile and c == tile['c']:
    return await interaction.response(utils.locale_text(interaction, 'same_color', x, y, c), ephemeral = True)
  data = {
    'c' : c,
    'u' : interaction.author.id, # store as str because deta.space can't hold big numbers
    's' : interaction.guild_id,
    't' : int(time.time())
  }
  await interaction.client.db.update(x, y, data) # update db
  interaction.client.grid[x][y] = data # update cache
  #interaction.client.cooldowns[interaction.author.id] = time.time() # update cooldowns
  await interaction.client.active_pixels.update(int(interaction.id)) # update pixels placed counter
  view = ExploreView(interaction, cursor)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw())  

@discohook.button(emoji = '➡️', custom_id = 'right:v0.0')
async def right_button(interaction):
  await move(interaction, 1, 0)

@discohook.modal('Jump Modal', [], custom_id = 'jumpmodal:v0.0')
async def jump_modal(interaction, x, y):
  utils.before_invoke(interaction)
  if not x.isnumeric():
    return await interaction.response(utils.locale_text(interaction, 'coord_number_error', 'X', x), ephemeral = True)
  elif not y.isnumeric():
    return await interaction.response(utils.locale_text(interaction, 'coord_number_error', 'Y', y), ephemeral = True)
  x = int(x)
  y = int(y)
  border = interaction.client.db.size - 1
  if not 0 <= x <= border:
    return await interaction.response(utils.locale_text(interaction, 'coord_range_error', 'X', x), ephemeral = True)
  elif not 0 <= y <= border:
    return await interaction.response(utils.locale_text(interaction, 'coord_range_error', 'Y', y), ephemeral = True)
  cursor = utils.get_cursor(interaction)
  cursor = (x, y, *cursor[2:])
  view = ExploreView(interaction, cursor)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw())  

@discohook.button('jump_button', style = discohook.ButtonStyle.grey, custom_id = 'jump:v0.0')
async def jump_button(interaction):
  utils.before_invoke(interaction)
  modal = discohook.Modal(jump_modal.title, custom_id = jump_modal.custom_id + ':dynamic')
  border = interaction.client.db.size - 1
  for i in ('X', 'Y'):
    modal.add_field(
      i, i.lower(), required = True,
      hint = utils.locale_text(interaction, 'jump_hint', border),
      min_length = 1, max_length = len(str(border))
    )
  await interaction.send_modal(modal)

@discohook.button(emoji = '↙️', custom_id = 'downleft:v0.0')
async def downleft_button(interaction):
  await move(interaction, -1, -1)

@discohook.button(emoji = '⬇️', custom_id = 'down:v0.0')
async def down_button(interaction):
  await move(interaction, 0, -1)

@discohook.button(emoji = '↘️', custom_id = 'downright:v0.0')
async def downright_button(interaction):
  await move(interaction, 1, -1)

@discohook.button('return_button', style = discohook.ButtonStyle.grey, custom_id = 'return:v0.0')
async def return_button(interaction):
  utils.before_invoke(interaction)
  view = start.StartView(interaction)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw())

step_options = [
  discohook.SelectOption(str(i), str(i))
  for i in [1, 2, 3, 4, 5, 10, 15, 20, 25]#, 50, 100, 150, 200, 256]
]
@discohook.select(step_options, placeholder = 'step_select', custom_id = 'stepselect:v0.0')
async def step_select(interaction, values):
  utils.before_invoke(interaction)
  step = int(values[0])
  cursor = utils.get_cursor(interaction)
  cursor = (*cursor[:3], step, cursor[-1])
  view = ExploreView(interaction, cursor)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw())

zoom_options = [
  discohook.SelectOption('{0}x{0}'.format(i), str(i))
  for i in [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]#, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51]
]
@discohook.select(zoom_options, placeholder = 'zoom_select', custom_id = 'zoomselect:v0.0')
async def zoom_select(interaction, values):
  utils.before_invoke(interaction)
  zoom = int(values[0])
  cursor = utils.get_cursor(interaction)
  cursor = (*cursor[:2], zoom, *cursor[-2:])
  view = ExploreView(interaction, cursor)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw())

class ExploreView(discohook.View):
  def __init__(self, interaction = None, cursor = None): # View is persistent if args not given
    super().__init__()
    self.interaction = interaction

    # Use right button custom ids and labels if cursor exists
    if interaction: # cursor is x y z s c

      # Place button
      self.cursor = cursor = cursor or utils.get_cursor(interaction)
      custom_id = place_button.custom_id + ':' + ':'.join(map(str, cursor))
      dynamic_place_button = discohook.Button(emoji = '🆗', custom_id = custom_id) # .callback points to place_button

      # Make buttons with locale (dynamic) button labels
      zoom, step, color = cursor[2:]
      dynamic_color_button = utils.locale_button(interaction, color_button, color)
      dynamic_jump_button = utils.locale_button(interaction, jump_button)
      dynamic_return_button = utils.locale_button(interaction, return_button)
      dynamic_step_select = utils.locale_select(interaction, step_select, step)
      dynamic_zoom_select = utils.locale_select(interaction, zoom_select, zoom)

    else:
      # If view is persistent
      dynamic_place_button = place_button
      dynamic_color_button = color_button
      dynamic_jump_button = jump_button
      dynamic_return_button = return_button
      dynamic_step_select = step_select
      dynamic_zoom_select = zoom_select

    # Add components
    self.add_buttons(upleft_button, up_button, upright_button, dynamic_color_button)
    self.add_buttons(left_button, dynamic_place_button, right_button, dynamic_jump_button)
    self.add_buttons(downleft_button, down_button, downright_button, dynamic_return_button)
    self.add_select(dynamic_step_select)
    self.add_select(dynamic_zoom_select)

  async def embed(self): # won't ever be called if it's persistent
    interaction = self.interaction
    cursor = self.cursor
    x, y = cursor[:2]

    title = utils.locale_text(interaction, 'explore_title').format(x, y)
    tile = interaction.client.grid[x][y]    
    if tile:
      user_id = int(tile['u'])
      if user_id in interaction.client.users:
        user = interaction.client.users[user_id]
      else:
        resp = await interaction.client.http.fetch_user(str(user_id))
        data = await resp.json()
        user = discohook.User(data, interaction.client)
        interaction.client.users[user_id] = user
      guild_id = int(tile['s'])
      if guild_id in interaction.client.guilds:
        guild = interaction.client.guilds[guild_id]
      else:
        try:
          guild = await interaction.client.fetch_guild(str(guild_id))
        except: # not mutual server with the bot
          guild = None
        interaction.client.guilds[guild_id] = guild
      guild_name = guild.name if guild else '*Unknown Server*'
      description = '\n'.join([
        '🎨 #{:06x}'.format(tile['c']),
        '🧍 {}'.format(user),
        '🏠 {}'.format(guild_name),
        '⏰ <t:{}:R>'.format(tile['t'])
      ])
    else:
      description = utils.locale_text(interaction, 'empty_tile')
      
    embed = discohook.Embed(
      title = title,
      description = description,
      color = interaction.client.constants.COLOR_BLURPLE
    )
    embed.image('attachment://map.png')
    active_users = len(interaction.client.active_users)
    suffix1 = utils.plural_suffix(active_users)
    if active_users == 1:
      verb = utils.locale_text(interaction, 'singular_verb')
    else:
      verb = utils.locale_text(interaction, 'plural_verb')
    active_pixels = len(interaction.client.active_pixels)
    suffix2 = utils.plural_suffix(active_pixels)
    embed.footer(utils.locale_text(interaction, 'live_text', active_users, suffix1, verb, active_pixels, suffix2))

    return embed

  async def draw(self):
    return await utils.draw_map(self.interaction, self.cursor)