import io
import asyncio
import discohook
import numpy as np
from PIL import Image
from . import start # .start.StartView is circular import
from ..utils.constants import COLOR_BLURPLE, CANVAS_SIZE, IMAGE_SIZE
from ..utils.helpers import get_grid

@discohook.button.new(emoji = '↖️', custom_id = 'upleft:v0.0')
async def upleft_button(interaction):
  await interaction.response.send('clicked upleft')

@discohook.button.new(emoji = '⬆️', custom_id = 'up:v0.0')
async def up_button(interaction):
  await interaction.response.send('clicked up')

@discohook.button.new(emoji = '↗️', custom_id = 'upright:v0.0')
async def upright_button(interaction):
  await interaction.response.send('clicked upright')

@discohook.modal.new('Color Modal', fields = [discohook.TextInput('test', 'test')], custom_id = 'color_modal:v0.0')
async def color_modal(interaction, test):
  await interaction.response.send('submit color modal {}'.format(test))

@discohook.button.new('Color: #000000', custom_id = 'color:v0.0', style = discohook.ButtonStyle.grey)
async def color_button(interaction):
  await interaction.response.send_modal(color_modal)

@discohook.button.new(emoji = '⬅️', custom_id = 'left:v0.0')
async def left_button(interaction):
  await interaction.response.send('clicked left')

@discohook.button.new(emoji = '🆗', custom_id = 'place:v0.0')
async def place_button(interaction):
  await interaction.response.send('clicked place')

@discohook.button.new(emoji = '➡️', custom_id = 'right:v0.0')
async def right_button(interaction):
  await interaction.response.send('clicked right')

@discohook.modal.new('Jump Modal', fields = [discohook.TextInput('test', 'test')], custom_id = 'jump_modal:v0.0')
async def jump_modal(interaction, test):
  await interaction.response.send('submit jump modal {}'.format(test))

@discohook.button.new('Jump to (X, Y)', style = discohook.ButtonStyle.grey, custom_id = 'jump:v0.0')
async def jump_button(interaction):
  await interaction.response.send_modal(jump_modal)

@discohook.button.new(emoji = '↙️', custom_id = 'downleft:v0.0')
async def downleft_button(interaction):
  await interaction.response.send('clicked downleft')

@discohook.button.new(emoji = '⬇️', custom_id = 'down:v0.0')
async def down_button(interaction):
  await interaction.response.send('clicked down')

@discohook.button.new(emoji = '↘️', custom_id = 'downright:v0.0')
async def downright_button(interaction):
  await interaction.response.send('clicked downright')

@discohook.button.new('Back To Home', style = discohook.ButtonStyle.grey, custom_id = 'return:v0.0')
async def return_button(interaction):
  await start.StartView(interaction).update()

step_options = [
  discohook.SelectOption(str(i), str(i))
  for i in [1, 2, 3, 4, 5, 10, 15, 20, 25]#, 50, 100, 150, 200, 256]
]
@discohook.select.text(step_options, placeholder = 'step_select', custom_id = 'step_select:v0.0')
async def step_select(interaction, values):
  await interaction.response.send('clicked step select {}'.format(values))

zoom_options = [
  discohook.SelectOption('{0}x{0}'.format(i), str(i))
  for i in [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]#, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51]
]
@discohook.select.text(zoom_options, placeholder = 'zoom_select', custom_id = 'zoom_select:v0.0')
async def zoom_select(interaction, values):
  await interaction.response.send('clicked zoom select {}'.format(values))

class ExploreView(discohook.View):
  def __init__(self, interaction = None): # View is persistent if args not given
    super().__init__()

    if interaction:
      self.interaction = interaction

      self.embed = discohook.Embed(
        'Selecting Tile (X, Y)',
        description = '\n'.join([
          '🎨 #000000',
          '🧍 imptype + dm hyperlink userid',
          '🏠 bots support + invite link in future?',
          '⏰ <t:123 :>'
        ]),
        color = COLOR_BLURPLE
      )
    
    self.add_buttons(upleft_button, up_button, upright_button, color_button)
    self.add_buttons(left_button, place_button, right_button, jump_button)
    self.add_buttons(downleft_button, down_button, downright_button, return_button)
    self.add_select(step_select)
    self.add_select(zoom_select)

  async def setup(self, data = None): # ainit
  
    grid = await get_grid(self.interaction)

    custom_id = 'upleft:v0.0:999:997:11:1:ff0000:1700782616111'

    cursor = tuple(map(int, custom_id.split(':')[2:5]))

    # calculate pointer cursor
    x, y, zoom = cursor[:3]
    radius = int(zoom/2)
    pointer = [radius] * 2

    startx = x - radius
    if startx < 0:
      startx = 0
      pointer[0] = x
    elif x + radius > CANVAS_SIZE - 1:
      startx = CANVAS_SIZE - zoom
      pointer[0] = zoom - (CANVAS_SIZE - x)

    starty = y - radius
    if starty < 0:
      starty = 0
      pointer[1] = y
    elif y + radius > CANVAS_SIZE - 1:
      starty = CANVAS_SIZE - zoom
      pointer[1] = CANVAS_SIZE - y - 1

    # draw canvas
    a = np.empty((zoom, zoom, 3), np.uint8)
    for i in range(zoom):
      y_key = starty + i
      if y_key in grid:
        pass # doesnt exist yet, no idea
      else: # new grids
        a[i] = np.full((zoom, 3), 255)

    bim = Image.fromarray(a)
    app = self.interaction.client

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
    
    def blocking():
      im = bim.resize(np.array(bim.size) * n, Image.Resampling.NEAREST)
      im.paste(app.cursor, tuple(np.array(pointer) * n), app.cursor)  # assuming max size doesn't exceed 128, this is fine
      return im.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST)

    im = await asyncio.to_thread(blocking)
    buffer = io.BytesIO()
    im.save(buffer, 'PNG')

    self.embed.set_image(discohook.File('map.png', content = buffer.getvalue()))

  async def update(self, data = None):
    await self.setup(data)
    await self.interaction.response.update_message(embed = self.embed, view = self)