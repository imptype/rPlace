import time
import discohook
from . import start
from ..extras import constants, utils

async def move(interaction, x, y):
  cursor = utils.get_cursor(interaction)
  pos_x, pos_y = cursor[:2]
  pos_x += x
  if pos_x == interaction.client.db.size:
    return await interaction.response('Max!', ephemeral = True)
  elif pos_x == -1:
    return await interaction.response('Max!', ephemeral = True)
  pos_y += y
  if pos_y == interaction.client.db.size:
    return await interaction.response('Max!', ephemeral = True)
  elif pos_y == -1:
    return await interaction.response('Max!', ephemeral = True)
  cursor = (pos_x, pos_y, *cursor[2:])
  embed = utils.get_explore_embed(interaction, pos_x, pos_y)
  view = ExploreView(interaction, cursor)
  file = await utils.draw_map(interaction, cursor)
  await interaction.update_message(embed = embed, view = view, file = file)

@discohook.button(emoji = '↖️', custom_id = 'upleft:v0.0')
async def upleft_button(interaction):
  cursor = utils.get_cursor
  await move(interaction, -1, 1)

@discohook.button(emoji = '⬆️', custom_id = 'up:v0.0')
async def up_button(interaction):
  await move(interaction, 0, 1)

@discohook.button(emoji = '↗️', custom_id = 'upright:v0.0')
async def upright_button(interaction):
  await move(interaction, 1, 1)

class ColorModal(discohook.Modal):
  def __init__(self, interaction = None):
    pass

color_modal = discohook.Modal('Color Modal')
color_modal.add_field(
  'Color', '1', required = True, 
  hint = 'A hex string like "#ffab12" or a number <= 16777215.',
  min_length = 1, max_length = 8
)
color_modal.custom_id = 'colormodal:v0.0'
async def color_callback(interaction):
  x = interaction.data['components'][0]['components'][0]['value']
  try:
    color = int(x) if x.isnumeric() else int(x.lstrip('#'), base = 16)
  except:
    return await interaction.response('Value `{}` is not a color!'.format(x), ephemeral = True)
  if not 0 <= color <= 256 ** 3 - 1:
    return await interaction.response('Color `{}` is out of range!'.format(x), ephemeral = True)
  #await interaction.response('received modal {}'.format(color))
  cursor = utils.get_cursor(interaction)
  cursor = (*cursor[:-1], color)
  embed = utils.get_explore_embed(interaction, *cursor[:2])
  view = ExploreView(interaction, cursor)
  file = await utils.draw_map(interaction, cursor)
  await interaction.update_message(embed = embed, view = view, file = file)  
color_modal.callback = color_callback

@discohook.button('Color: #000000', custom_id = 'color:v0.0', style = discohook.ButtonStyle.grey)
async def color_button(interaction):
  await interaction.send_modal(color_modal)

@discohook.button(emoji = '⬅️', custom_id = 'left:v0.0')
async def left_button(interaction):
  await move(interaction, -1, 0)

@discohook.button(emoji = '🆗', custom_id = 'place:v0.0')
async def place_button(interaction):
  cooldown = interaction.client.cooldowns.get(interaction.author.id)
  if cooldown and cooldown + 20 > time.time():
    return await interaction.response(utils.locale_text(interaction, 'cooldown_text'), ephemeral = True)
  cursor = utils.get_cursor(interaction)
  x, y = cursor[:2]
  c = cursor[-1]
  data = {
    'c' : c,
    'u' : interaction.author.id,
    's' : interaction.guild_id,
    't' : int(time.time())
  }
  await interaction.client.db.update(x, y, data) # update db
  interaction.client.grid[x][y] = data # update cache
  interaction.client.cooldowns[interaction.author.id] = time.time() # update cooldowns
  embed = utils.get_explore_embed(interaction, x, y)
  view = ExploreView(interaction, cursor)
  file = await utils.draw_map(interaction, cursor)
  await interaction.update_message(embed = embed, view = view, file = file)  

@discohook.button(emoji = '➡️', custom_id = 'right:v0.0')
async def right_button(interaction):
  await move(interaction, 1, 0)

@discohook.button('Jump to (X, Y)', style = discohook.ButtonStyle.grey, custom_id = 'jump:v0.0')
async def jump_button(interaction):
  await interaction.response(utils.locale_text(interaction, 'wip'), ephemeral = True)

@discohook.button(emoji = '↙️', custom_id = 'downleft:v0.0')
async def downleft_button(interaction):
  await move(interaction, -1, -1)

@discohook.button(emoji = '⬇️', custom_id = 'down:v0.0')
async def down_button(interaction):
  await move(interaction, 0, -1)

@discohook.button(emoji = '↘️', custom_id = 'downright:v0.0')
async def downright_button(interaction):
  await move(interaction, 1, -1)

@discohook.button('Back To Home', style = discohook.ButtonStyle.grey, custom_id = 'return:v0.0')
async def return_button(interaction):
  file = await interaction.client.utils.draw_map(interaction)
  embed = utils.get_start_embed(interaction)
  await interaction.update_message(embed = embed, view = start.view, file = file)

step_options = [
  discohook.SelectOption(str(i), str(i))
  for i in [1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 100, 150, 200, 256]
]
@discohook.select(step_options, placeholder = 'Step Size: X', custom_id = 'stepselect:v0.0')
async def step_select(interaction, values):
  await interaction.response(utils.locale_text(interaction, 'wip'), ephemeral = True)
  """step = int(values[0])
  cursor = utils.get_cursor(interaction)
  cursor = (*cursor[:3], step, cursor[-1])
  embed = utils.get_explore_embed(interaction, *cursor[:2])
  view = ExploreView(interaction, cursor)
  file = await utils.draw_map(interaction, cursor)
  await interaction.update_message(embed = embed, view = view, file = file) """

zoom_options = [
  discohook.SelectOption('{0}x{0}'.format(i), str(i))
  for i in [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]#, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51]
]
@discohook.select(zoom_options, placeholder = 'Zoom: XxX', custom_id = 'zoomselect:v0.0')
async def zoom_select(interaction, values):
  zoom = int(values[0])
  cursor = utils.get_cursor(interaction)
  cursor = (*cursor[:2], zoom, *cursor[-2:])
  embed = utils.get_explore_embed(interaction, *cursor[:2])
  view = ExploreView(interaction, cursor)
  file = await utils.draw_map(interaction, cursor)
  await interaction.update_message(embed = embed, view = view, file = file)

class ExploreView(discohook.View):
  def __init__(self, interaction = None, cursor = None): # View is persistent if args not given
    super().__init__()

    # Use right button custom ids and labels if cursor exists
    if interaction: # cursor is x y z s c

      # Place button
      custom_id = place_button.custom_id + ':' + ':'.join(map(str, cursor))
      dynamic_place_button = discohook.Button(emoji = '🆗', custom_id = custom_id) # .callback points to place_button

      zoom, step, color = cursor[2:]

      # Color button (dynamic label)
      label = utils.locale_text(interaction, 'color_button').format(color)
      custom_id = color_button.custom_id + ':dynamic' # so it uses the other callback
      dynamic_color_button = discohook.Button(label, custom_id = custom_id, style = discohook.ButtonStyle.grey)

      # Jump button (dynamic label)
      label = utils.locale_text(interaction, 'jump_button')
      custom_id = jump_button.custom_id + ':dynamic'
      dynamic_jump_button = discohook.Button(label, custom_id = custom_id, style = discohook.ButtonStyle.grey)

      # Return button (dynamic label)
      label = utils.locale_text(interaction, 'return_button')
      custom_id = return_button.custom_id + ':dynamic'
      dynamic_return_button = discohook.Button(label, custom_id = custom_id, style = discohook.ButtonStyle.grey)

      # Step select (dynamic placeholder)
      placeholder = utils.locale_text(interaction, 'step_select').format(step)
      custom_id = step_select.custom_id + ':dynamic'
      dynamic_step_select = discohook.Select(step_options, placeholder = placeholder, custom_id = custom_id)

      # Zoom select (dynamic placeholder)
      placeholder = utils.locale_text(interaction, 'zoom_select').format(zoom)
      custom_id = zoom_select.custom_id + ':dynamic'
      dynamic_zoom_select = discohook.Select(zoom_options, placeholder = placeholder, custom_id = custom_id)

    else:
      dynamic_place_button = place_button
      dynamic_color_button = color_button
      dynamic_jump_button = jump_button
      dynamic_return_button = return_button
      dynamic_step_select = step_select
      dynamic_zoom_select = zoom_select

    # Add components
    self.add_button_row(upleft_button, up_button, upright_button, dynamic_color_button)
    self.add_button_row(left_button, dynamic_place_button, right_button, dynamic_jump_button)
    self.add_button_row(downleft_button, down_button, downright_button, dynamic_return_button)
    self.add_select_menu(dynamic_step_select)
    self.add_select_menu(dynamic_zoom_select)