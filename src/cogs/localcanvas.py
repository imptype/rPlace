import discohook

@discohook.command.slash('local-canvas', description = 'Interact with the local server\'s canvas!')
async def local_canvas_command(interaction):
  await interaction.response.send('local canvas!')