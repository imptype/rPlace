import discohook

@discohook.command.slash('canvas', description = 'Interact with the global canvas!')
async def canvas_command(interaction):
  await interaction.response.send('global canvas!')