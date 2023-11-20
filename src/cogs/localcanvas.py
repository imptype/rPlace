import discohook
from ..screens.start import StartView

@discohook.command.slash('local-canvas', description = 'Interact with the local server\'s canvas!')
async def local_canvas_command(interaction):
  await StartView(interaction).send()