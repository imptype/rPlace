import io
import asyncio
import discohook
from ..screens.explore import ExploreView
from ..utils.constants import COLOR_BLURPLE, CANVAS_SIZE
from ..utils.helpers import get_grid, draw_map

@discohook.button.new('Explore', emoji = '🔍', custom_id = 'explore:v0.0')
async def explore_button(interaction):
  await ExploreView(interaction).update()

@discohook.button.new(emoji = '🏆', custom_id = 'top:v0.0', style = discohook.ButtonStyle.green)
async def top_button(interaction):
  await interaction.response.send('clicked top button')

@discohook.button.new(emoji = '🔄', custom_id = 'refresh:v0.0')
async def refresh_button(interaction):
  await interaction.response.send('clicked refresh button')

class StartView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    if interaction:

      self.interaction = interaction
      self.embed = discohook.Embed(
        'Welcome to r/Place!',
        description = '\n'.join([
          'Canvas size: 1000x1000',
          '',
          'Click 🔍 **Explore** to start exploring!'
        ]),
        color = COLOR_BLURPLE
      )
    self.add_buttons(explore_button, top_button, refresh_button)

  async def setup(self): # ainit
    
    grid = await get_grid(self.interaction)

    def blocking():
      im = draw_map(grid, CANVAS_SIZE)
      buffer = io.BytesIO()
      im.save(buffer, 'PNG')
      return buffer

    # draw canvas
    buffer = await asyncio.to_thread(blocking)

    self.embed.set_image(discohook.File('map.png', content = buffer.getvalue()))
  
  async def send(self):
    await self.setup()
    await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self):
    await self.setup()
    await self.interaction.response.update_message(embed = self.embed, view = self)