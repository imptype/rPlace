import discohook
from ..screens.start import StartView

@discohook.command('canvas', 'interact with the global canvas!')
async def canvas_command(interaction):
  interaction.client.utils.before_invoke(interaction)
  view = StartView(interaction)
  await interaction.response(embed = await view.embed(), view = view, file = await view.draw())