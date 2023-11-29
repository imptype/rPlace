import io
import asyncio
import discohook
from . import start
from ..utils.helpers import draw_map, get_grid
from ..utils.constants import BOT_VERSION, COLOR_RED, CANVAS_SIZE

@discohook.button.new('Back To Home', emoji = '⬅️', custom_id = 'settings_back:v{}'.format(BOT_VERSION))
async def back_button(interaction):

  # parse last refresh timestamp on canvas
  refresh_at = int(interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])
  
  grid, new_refresh_at = await get_grid(interaction)

  skip_draw = refresh_at >= new_refresh_at # didnt do an update = dont update image
  
  refresh_data = grid, new_refresh_at, skip_draw
  await start.StartView(interaction).update(refresh_data)

@discohook.button.new('Resize Canvas', emoji = '📐', custom_id = 'settings_resize:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.red)
async def resize_button(interaction):
  await interaction.response.send('click resize')

@discohook.button.new('Set Cooldown', emoji = '⏰', custom_id = 'settings_cooldown:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.red)
async def cooldown_button(interaction):
  await interaction.response.send('click set cooldown')

@discohook.button.new('Set Allowed Role', emoji = '👤', custom_id = 'settings_role:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.red)
async def allowed_button(interaction):
  await interaction.response.send('click set allowed role')

class SettingsView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    if interaction:
      self.interaction = interaction
    else: # persistent
      self.add_buttons(back_button, resize_button, cooldown_button, allowed_button)

  async def setup(self): # ainit
    self.embed = discohook.Embed(
      'r/Place Local Settings',
      description = '\n'.join([
        'This is a __**work in progress**__. In the near future, you\'ll be able to do the following to configure your local canvas:',
        '',
        '**[1] Resizing Canvas**',
        'Resizes the local canvas anywhere between 3x3 to 1000x1000. Pixel data outside of the new resized region will persist and will return if you decide to resize back.',
        '',
        '**[2] Setting a cooldown**',
        'Set a cooldown between None to 24 hours. A cooldown means if someone placed a pixel, they will have to wait that amount of time before they can place another one again.',
        '',
        '**[3] Set allowed/whitelisted role**',
        'If you set this, only people with this role can actually place pixels. This is useful if you want people to be able to spectate but not be able to overwrite pixels.'
      ]),
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
    self.add_buttons(dynamic_back_button, resize_button, cooldown_button, allowed_button)
  
  async def update(self):
    await self.setup()
    await self.interaction.response.update_message(embed = self.embed, view = self)