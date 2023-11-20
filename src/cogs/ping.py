import discohook

@discohook.command.slash('ping', description = 'Ping test the bot!')
async def ping_command(interaction):
  await interaction.response.send('ping!')