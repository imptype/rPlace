import discohook
from ..views.startview import start_view

@discohook.command('canvas', 'interact with the global canvas!')
async def canvas_command(interaction):
  embed = discohook.Embed(
    title = 'Welcome to r/Place!',
    description = '\n'.join([
      'Canvas Size: 250x250',
      '',
      'Click 🔍 to explore.'
    ]),
    color = interaction.client.constants.COLOR_BLURPLE
  )
  await interaction.response(embed = embed, view = start_view)