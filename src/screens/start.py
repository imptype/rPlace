import discohook
from .explore import ExploreView
from ..extras import constants, utils

@discohook.button('Explore', emoji = '🔍', custom_id = 'explore:v0.0')
async def explore_button(interaction):
  cursor = 0, 0, 11, 1, 0x000000 # (x pos, y pos, zoom, step size, color)
  embed = utils.get_explore_embed(interaction, *cursor[:2])
  view = ExploreView(interaction, cursor)
  file = await utils.draw_map(interaction, cursor)
  await interaction.update_message(embed = embed, view = view, file = file)

view = discohook.View()
view.add_button_row(explore_button)