import discohook
from ..utils.constants import COLOR_BLURPLE

@discohook.command.slash('test', description = 'Test stuff!', 
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
async def test_command(interaction):
  await interaction.response.send('test command in dms')