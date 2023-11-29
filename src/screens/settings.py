import io
import asyncio
import discohook
from . import start
from ..utils.helpers import draw_map, get_grid
from ..utils.constants import BOT_VERSION, COLOR_RED, CANVAS_SIZE

@discohook.button.new('Back To Home', emoji = '⬅️', custom_id = 'settingsback:v{}'.format(BOT_VERSION))
async def back_button(interaction):

  # parse last refresh timestamp on canvas
  refresh_at = int(interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])
  
  grid, new_refresh_at = await get_grid(interaction)

  skip_draw = refresh_at >= new_refresh_at # didnt do an update = dont update image
  
  refresh_data = grid, new_refresh_at, skip_draw
  await start.StartView(interaction).update(refresh_data)

class SettingsView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    if interaction:
      self.interaction = interaction
    else: # persistent
      self.add_buttons(back_button)

  async def setup(self): # ainit
    self.embed = discohook.Embed(
      'settings',
      description = 'desc',
      color = COLOR_RED
    )
    
    # get grid
    grid, new_refresh_at = await get_grid(self.interaction)

    # draw new canvas if refresh has happened from startview
    refresh_at = int(self.interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])

    if refresh_at >= new_refresh_at: # didnt do an update, skip draw
      self.embed.set_thumbnail('attachment://map.png')
    else:

      def blocking():
        im = draw_map(grid, CANVAS_SIZE)
        buffer = io.BytesIO()
        im.save(buffer, 'PNG')
        return buffer

      # draw canvas
      buffer = await asyncio.to_thread(blocking)

      self.embed.set_thumbnail(discohook.File('map.png', content = buffer.getvalue()))
    
    dynamic_back_button = discohook.Button(
      back_button.label,
      emoji = back_button.emoji,
      custom_id = '{}:{}'.format(back_button.custom_id, new_refresh_at)
    )
    self.add_buttons(dynamic_back_button)
  
  async def update(self):
    await self.setup()
    await self.interaction.response.update_message(embed = self.embed, view = self)