import io
import asyncio
import discohook
from ..utils.helpers import get_grid, draw_map
from ..utils.constants import BOT_VERSION, CANVAS_SIZE, COLOR_BLURPLE
from . import start

@discohook.button.new('Back', emoji = '⬅️', custom_id = 'back:v{}'.format(BOT_VERSION))
async def back_button(interaction):
  await start.StartView(interaction).update()

@discohook.button.new(emoji = '1️⃣', custom_id = 'one:v{}'.format(BOT_VERSION))
async def one_button(interaction):
  await TopView(interaction).update(0)

@discohook.button.new(emoji = '2️⃣', custom_id = 'two:v{}'.format(BOT_VERSION))
async def two_button(interaction):
  await TopView(interaction).update(1)

@discohook.button.new(emoji = '3️⃣', custom_id = 'three:v{}'.format(BOT_VERSION))
async def three_button(interaction):
  await TopView(interaction).update(2)

@discohook.button.new(emoji = '4️⃣', custom_id = 'four:v{}'.format(BOT_VERSION))
async def four_button(interaction):
  await TopView(interaction).update(3)

class TopView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    if interaction:
      self.interaction = interaction
    else: # persistent
      self.add_buttons(back_button, one_button, two_button, three_button, four_button)
  
  async def setup(self, flag): # ainit

    # draw canvas, refresh_at doesn't really matter for top, acknowledge it takes time to update
    grid, _refresh_at = await get_grid(self.interaction)

    def blocking():
      im = draw_map(grid, CANVAS_SIZE)
      buffer = io.BytesIO()
      im.save(buffer, 'PNG')
      return buffer

    # draw canvas
    buffer = await asyncio.to_thread(blocking)

    if not flag:
      text = 'one'
    elif flag == 1:
      text = 'two'
    elif flag == 2:
      text = 'three'
    elif flag == 3:
      text = 'four'
    else:
      raise ValueError('Unhandled TopView flag:', flag)

    self.embed = discohook.Embed(
      'r/Place Rankings',
      description = text,
      color = COLOR_BLURPLE
    )
    self.embed.set_thumbnail(discohook.File('map.png', content = buffer.getvalue()))
    
    dynamic_one_button = discohook.Button(
      emoji = one_button.emoji,
      custom_id = one_button.custom_id + ':',
      disabled = not flag
    )
    
    dynamic_two_button = discohook.Button(
      emoji = two_button.emoji,
      custom_id = two_button.custom_id + ':',
      disabled = flag == 1
    )
    
    dynamic_three_button = discohook.Button(
      emoji = three_button.emoji,
      custom_id = three_button.custom_id + ':',
      disabled = flag == 2
    )
    
    dynamic_four_button = discohook.Button(
      emoji = four_button.emoji,
      custom_id = four_button.custom_id + ':',
      disabled = flag == 3
    )

    self.add_buttons(back_button, dynamic_one_button, dynamic_two_button, dynamic_three_button, dynamic_four_button)
  
  async def update(self, flag = 0):
    await self.setup(flag)
    await self.interaction.response.update_message(embed = self.embed, view = self)