import io
import asyncio
import discohook
from ..screens.explore import ExploreView
from ..utils.constants import COLOR_BLURPLE, CANVAS_SIZE, BOT_VERSION
from ..utils.helpers import get_grid, draw_map

@discohook.button.new('Explore', emoji = '🔍', custom_id = 'explore:v{}'.format(BOT_VERSION))
async def explore_button(interaction):
  await ExploreView(interaction).update()

@discohook.button.new(emoji = '🏅', custom_id = 'top:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.green)
async def top_button(interaction):
  await interaction.response.send('clicked top button')

@discohook.button.new(emoji = '🔄', custom_id = 'refresh:v{}'.format(BOT_VERSION))
async def refresh_button(interaction):

  # parse last refresh timestamp on canvas
  refresh_at = int(interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])
  
  grid, new_refresh_at = await get_grid(interaction, with_refresh = True)

  if refresh_at == new_refresh_at: # didnt do an update
    return await interaction.response.send('Already up to date.', ephemeral = True)
  
  refresh_data = grid, new_refresh_at
  await StartView(interaction).update(refresh_data)

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
    else: # persistent
      self.add_buttons(explore_button, top_button, refresh_button)

  async def setup(self, refresh_data = None): # ainit
    
    if refresh_data:
      grid, refresh_at = refresh_data
    else: # not from refresh_button
      grid, refresh_at = await get_grid(self.interaction, with_refresh = True)

    def blocking():
      im = draw_map(grid, CANVAS_SIZE)
      buffer = io.BytesIO()
      im.save(buffer, 'PNG')
      return buffer

    # draw canvas
    buffer = await asyncio.to_thread(blocking)

    self.embed.set_image(discohook.File('map.png', content = buffer.getvalue()))
    
    # stuff custom id of refreshed at in this button
    dyanmic_explore_button = discohook.Button(
      explore_button.label,
      emoji = explore_button.emoji,
      custom_id = '{}:{}'.format(explore_button.custom_id, refresh_at)
    )
    self.add_buttons(dyanmic_explore_button, top_button, refresh_button)
  
  async def send(self):
    await self.setup()
    await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self, refresh_data = None):
    await self.setup(refresh_data)
    await self.interaction.response.update_message(embed = self.embed, view = self)