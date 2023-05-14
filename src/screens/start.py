import discohook
from .explore import ExploreView
from ..extras import constants, utils

@discohook.button('explore_button', emoji = '🔍', custom_id = 'explore:v0.0')
async def explore_button(interaction):
  utils.before_invoke(interaction)
  cursor = 0, 0, 11, 1, 0x000000 # start cursor values, (x pos, y pos, zoom, step size, color)
  view = ExploreView(interaction, cursor)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw())

@discohook.button(emoji = '🔄', custom_id = 'refresh:v0.0')
async def refresh_button(interaction):
  utils.before_invoke(interaction)
  view = StartView(interaction)
  await interaction.update_message(embed = await view.embed(), view = view, file = await view.draw())

class StartView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    self.interaction = interaction
    if interaction:
      dynamic_explore_button = utils.locale_button(interaction, explore_button)
    else:
      dynamic_explore_button = explore_button
    self.add_buttons(dynamic_explore_button, refresh_button)

  async def embed(self):
    interaction = self.interaction
    embed = discohook.Embed(
      title = utils.locale_text(interaction, 'welcome_title'),
      description = '\n'.join([
        utils.locale_text(interaction, 'welcome_line_1').format(interaction.client.db.size),
        '',
        utils.locale_text(interaction, 'welcome_line_2')
      ]),
      color = constants.COLOR_BLURPLE
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

  async def draw(self): # without cursor
    return await utils.draw_map(self.interaction)