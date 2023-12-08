import discohook
from ..screens.start import StartView

@discohook.command.slash('canvas', description = 'Draw on the global canvas!')
async def canvas_command(interaction):
  await StartView(interaction).send()