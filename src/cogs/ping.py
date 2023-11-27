import time
import discohook

@discohook.command.slash('ping', description = 'Ping test the bot!')
async def ping_command(interaction):
  created_at = interaction.created_at
  now = time.time()
  since = now - created_at
  content = 'Pong! Latency: `{:.2f}ms`'.format(since * 1000)
  await interaction.response.send(content)