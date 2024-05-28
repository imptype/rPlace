import discohook
from ..utils.helpers import get_grid
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
  import time
  now = int(time.time())
  await interaction.response.send('test in 3 seconds {0} <t:{0}:R>'.format(now))
