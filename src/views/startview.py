import discohook
from .exploreview import explore_view

@discohook.button('Explore', emoji = '🔍')
async def explore_button(interaction):
  embed = discohook.Embed(
    title = 'Selecting tile (0, 0)',
    description = 'Nobody has painted here yet.',
    color = interaction.client.constants.COLOR_BLURPLE
  )
  await interaction.update_message(embed = embed, view = explore_view)

start_view = discohook.View()
start_view.add_button_row(explore_button)