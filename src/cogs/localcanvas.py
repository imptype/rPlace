import discohook
from ..screens.start import StartView

@discohook.command.slash('local-canvas', description = 'Draw art on your server\'s canvas!')
async def local_canvas_command(interaction):
  await StartView(interaction).send()