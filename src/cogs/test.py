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
  await interaction.response.send('test command in dms')

  grid, configs = await interaction.client.db.get_grid()
  import json
  with open('test.json', 'w') as f:
    json.dump(grid, f)