import io
import time
import asyncio
import discohook
from PIL import Image
from . import start, explore
from ..utils.helpers import draw_map, get_grid
from ..utils.constants import BOT_VERSION, COLOR_RED, CANVAS_SIZE, IMAGE_SIZE

@discohook.button.new('Back To Home', emoji = '⬅️', custom_id = 'admin_back:v{}'.format(BOT_VERSION))
async def back_button(interaction):

  # parse last refresh timestamp on canvas
  refresh_at = int(interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])
  
  grid_data, defer_response, new_refresh_at = await get_grid(interaction)

  skip_draw = refresh_at >= new_refresh_at # didnt do an update = dont update image
  
  refresh_data = grid_data, defer_response, new_refresh_at, skip_draw
  await start.StartView(interaction).update(refresh_data)

resize_field = discohook.TextInput('Size', 'size', hint = 'A number in the range of 3-1000', min_length = 1, max_length = 4, required = True)
@discohook.modal.new('Resize Modal', fields = [], custom_id = 'admin_resize_modal:v{}'.format(BOT_VERSION))
async def resize_modal(interaction, size):

  # validate timestamp
  try:
    timestamp, old_size, _cooldown, _allowed, _refresh_at = explore.get_values(interaction) # message values
    assert int(interaction.data['custom_id'].split(':')[-1]) == timestamp # compares ms timestamp with ms timestamp
  except: # index error = wrong screen, assert error = wrong timestamp
    return await interaction.response.send('The Resize Modal has expired!', ephemeral = True)

  # validate integers, accepts numbers from other languages
  if not size.isdecimal():
    return await interaction.response.send('Size `{}` is not a number!'.format(size), ephemeral = True)
  size = int(size)

  # validate new size prevent 2 request
  if size == old_size:
    return await interaction.response.send('The canvas is already the size `{}`! Reopen the menu if you think this message outdated.'.format(size), ephemeral = True)  
  
  # validate the range
  if not 3 <= size <= 1000:
    return await interaction.response.send('Size `{}` is out of range!'.format(size), ephemeral = True)

  # fetch up to date grid
  (grid, configs), defer_response, refresh_at, local_id = await get_grid(interaction, True)
  old_size = configs.get('size', CANVAS_SIZE)

  # validate new size again, prevent 1 request
  if size == old_size:
    return await interaction.response.send('The canvas is already the size `{}`!! Reopen the menu if you think this message outdated.'.format(size), ephemeral = True)  
  
  # update if y0 exists, extremely rare to error and autofixes on next move
  exists = 0 in grid
  await interaction.client.db.update_configs(local_id, exists, 'size', size)
  configs['size'] = size  

  # always draw because size changed
  skip_draw = False

  # all good, update view
  refresh_data = (grid, configs), defer_response, refresh_at, skip_draw
  await SettingsView(interaction).update(refresh_data)

@discohook.button.new('Resize Canvas', emoji = '📐', custom_id = 'admin_resize:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.red)
async def resize_button(interaction):
  modal = discohook.Modal(
    resize_modal.title,
    custom_id = '{}:{}'.format(resize_modal.custom_id, explore.get_values(interaction)[0])
  )
  modal.rows.append(resize_field.to_dict())
  await interaction.response.send_modal(modal)

@discohook.button.new('Set Cooldown', emoji = '⏰', custom_id = 'admin_cooldown:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.red)
async def cooldown_button(interaction):
  await interaction.response.send('click set cooldown')

@discohook.button.new('Set Allowed Role', emoji = '👤', custom_id = 'admin_role:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.red)
async def allowed_button(interaction):
  await interaction.response.send('click set allowed role')

class SettingsView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    if interaction:
      self.interaction = interaction
    else: # persistent
      self.add_buttons(back_button, resize_button, cooldown_button, allowed_button)

  async def setup(self, refresh_data): # ainit

    # get grid
    if refresh_data: # always forced if setting was updated
      (grid, configs), self.defer_response, new_refresh_at, skip_draw = refresh_data
    else:
      (grid, configs), self.defer_response, new_refresh_at = await get_grid(self.interaction)
      # draw new canvas if refresh has happened from startview
      refresh_at = int(self.interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])
      skip_draw = refresh_at >= new_refresh_at

    size = configs.get('size', CANVAS_SIZE)
    cooldown = configs.get('cooldown') or 0
    allowed = configs.get('allowed')

    self.embed = discohook.Embed(
      'r/Place Local Settings',
      description = '\n'.join([
        'This is a __**work in progress**__. In the near future, you\'ll be able to do the following to configure your local canvas:',
        '',
        '**[1] Resizing Canvas (Current Size: `{0}x{0}`)**'.format(size),
        'Resizes the local canvas anywhere between 3x3 to 1000x1000. Pixel data outside of the new resized region will persist and will return if you decide to resize back.',
        '',
        '**[2] Setting a cooldown (Current: `{} seconds`)**'.format(cooldown),
        'Set a cooldown between None to 24 hours. A cooldown means if someone placed a pixel, they will have to wait that amount of time before they can place another one again.',
        '',
        '**[3] Set allowed/whitelisted role (Current: {})**'.format('<@&{}>'.format(allowed) if allowed else 'N/A'),
        'If you set this, only people with this role can actually place pixels. This is useful if you want people to be able to spectate but not be able to overwrite pixels.'
      ]),
      color = COLOR_RED
    )

    if skip_draw: # didnt do an update, skip draw
      self.embed.set_thumbnail('attachment://map.png')
    else:

      def blocking():
        im = draw_map(grid, size)
        if size < CANVAS_SIZE:
          im = im.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST)
        buffer = io.BytesIO()
        im.save(buffer, 'PNG')
        return buffer

      # draw canvas
      buffer = await asyncio.to_thread(blocking)

      self.embed.set_thumbnail(discohook.File('map.png', content = buffer.getvalue()))
    
    dynamic_back_button = discohook.Button(
      back_button.label,
      emoji = back_button.emoji,
      custom_id = '{}:{}:{}:{}:{}:{}'.format(back_button.custom_id, int(time.time() * 10 ** 7), size, cooldown, allowed if allowed else 0, new_refresh_at)
    )
    self.add_buttons(dynamic_back_button, resize_button, cooldown_button, allowed_button)
  
  async def update(self, refresh_data = None):
    await self.setup(refresh_data)
    if self.defer_response:
      await self.defer_response.edit(embed = self.embed, view = self)
    else:
      await self.interaction.response.update_message(embed = self.embed, view = self)