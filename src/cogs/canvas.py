import discohook
from ..screens.start import StartView

@discohook.command.slash('canvas', description = 'Draw art on the global canvas!',
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
async def canvas_command(interaction):
  await StartView(interaction).send()