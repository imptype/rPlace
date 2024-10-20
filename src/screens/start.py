import io
import asyncio
import discohook
from PIL import Image
from ..screens.explore import ExploreView
from ..screens.top import TopView
from ..screens.settings import SettingsView
from ..utils.constants import COLOR_BLURPLE, CANVAS_SIZE, BOT_VERSION, IMAGE_SIZE
from ..utils.helpers import get_grid, draw_map, get_local_id, is_admin

@discohook.button.new('Explore', emoji = '🔍', custom_id = 'explore:v{}'.format(BOT_VERSION))
async def explore_button(interaction):
  await ExploreView(interaction).update()

@discohook.button.new('Statistics', emoji = '🏅', custom_id = 'top:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.green)
async def top_button(interaction):
  await TopView(interaction).update()

@discohook.button.new('Settings [Admin]', emoji = '🛠️', custom_id = 'settings:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.red)
async def settings_button(interaction):
  await SettingsView(interaction).update()

@discohook.button.new(emoji = '🔄', custom_id = 'refresh:v{}'.format(BOT_VERSION))
async def refresh_button(interaction):

  # parse last refresh timestamp on canvas
  refresh_at = int(interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])
  
  grid_data, defer_response, new_refresh_at = await get_grid(interaction)

  skip_draw = refresh_at >= new_refresh_at # didnt do an update = dont update image

  refresh_data = grid_data, defer_response, new_refresh_at, skip_draw
  await StartView(interaction).update(refresh_data)

class StartView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    if interaction:
      self.interaction = interaction
    else: # persistent
      self.add_buttons(explore_button, top_button, settings_button, refresh_button)

  async def setup(self, refresh_data = None, expired_defer_response = None): # ainit
    
    if refresh_data: # coming back from settings/top
      (grid, configs), self.defer_response, refresh_at, skip_draw = refresh_data
    else: # not from refresh_button or top back button or expired
      (grid, configs), self.defer_response, refresh_at = await get_grid(self.interaction, defer_response = expired_defer_response)
      skip_draw = False

    has_expired = isinstance(expired_defer_response, bool) or bool(expired_defer_response)

    local_id = get_local_id(self.interaction)
    
    if local_id:
      if self.interaction.guild_id:
        title = 'your Server Canvas'
      else:
        title = 'your Personal Canvas'
    else:
        title = 'the Global Canvas'
    
    size = configs.get('size') or CANVAS_SIZE
    text = '' if has_expired else '\n\nClick 🔍 **Explore** to start exploring!'

    self.embed = discohook.Embed(
      'Welcome to {}!'.format(title),
      description = 'Canvas size: {}x{}'.format(*size) + text,
      color = COLOR_BLURPLE
    )
    if has_expired:
      self.embed.set_footer('Interaction has expired, run the command again.')

    if skip_draw:
      self.embed.set_image('attachment://map.png')
    else:
      def blocking():
        im = draw_map(grid, configs)
        factor = IMAGE_SIZE // max(size)
        resize = (size[0] * factor, size[1] * factor)
        if size != resize:
          im = im.resize(resize, Image.Resampling.NEAREST)
        buffer = io.BytesIO()
        im.save(buffer, 'PNG')
        return buffer

      # draw canvas
      buffer = await asyncio.to_thread(blocking)

      self.embed.set_image(discohook.File('map.png', content = buffer.getvalue()))
    
    # stuff custom id of refreshed at in this button
    dynamic_explore_button = discohook.Button(
      explore_button.label,
      emoji = explore_button.emoji,
      custom_id = '{}:{}'.format(explore_button.custom_id, refresh_at)
    )

    is_admin_check = bool(local_id and is_admin(self.interaction)) # checks if they can edit canvas
    
    if has_expired:
      if is_admin_check:
        dynamic_settings_button = discohook.Button(
          settings_button.label,
          emoji = settings_button.emoji,
          style = settings_button.style,
          custom_id = '{}:{}'.format(settings_button.custom_id, refresh_at)
        )
        self.add_buttons(dynamic_settings_button) # only button they see is settings
    else:
      if is_admin_check:
        self.add_buttons(dynamic_explore_button, top_button, settings_button, refresh_button)
      else:
        self.add_buttons(dynamic_explore_button, top_button, refresh_button)
  
  async def send(self):
    await self.setup()
    if self.defer_response or self.interaction.responded: # if grid reloaded, it has to be deferred, responded is temp fix for defer on creation, unsure
      # this is meant to be self.defer_response.send(), lib put followup in interaction.response
      await self.interaction.response.followup(embed = self.embed, view = self)
    else:
      await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self, refresh_data = None, expired_defer_response = None):
    await self.setup(refresh_data, expired_defer_response)
    if self.defer_response:
      await self.defer_response.edit(embed = self.embed, view = self)
    else:
      await self.interaction.response.update_message(embed = self.embed, view = None if expired_defer_response else self)