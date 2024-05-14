import time
import discohook

@discohook.command.slash('ping', description = 'Ping test the bot!',
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
async def ping_command(interaction):
  created_at = interaction.created_at
  now = time.time()
  since = now - created_at
  content = 'Pong! Latency: `{:.2f}ms`'.format(since * 1000)
  await interaction.response.send(content)