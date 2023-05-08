import discohook
from ..screens import start

@discohook.command('canvas', 'interact with the global canvas!')
async def canvas_command(interaction):
  file = await interaction.client.utils.draw_map(interaction)
  embed = interaction.client.utils.get_start_embed(interaction)
  await interaction.response(embed = embed, view = start.view, file = file)