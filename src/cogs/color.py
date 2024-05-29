import discohook
from ..screens.color import ColorView

@discohook.command.slash('color', description = 'Generate a color!',
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
async def color_command(interaction):
  await ColorView(interaction).send()
