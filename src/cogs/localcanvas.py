import discohook
from ..screens.start import StartView

@discohook.command.slash('local-canvas', description = 'Draw art on your server\'s canvas!',
  integration_types = [
    discohook.ApplicationIntegrationType.user,
    discohook.ApplicationIntegrationType.guild
  ],
  contexts = [
    discohook.InteractionContextType.guild,
    discohook.InteractionContextType.bot_dm,
    discohook.InteractionContextType.private_channel
  ]
)
async def local_canvas_command(interaction):
  await StartView(interaction).send()