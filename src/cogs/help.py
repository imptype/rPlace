import discohook

@discohook.command.slash('help', description = 'shows commands list and tutorial')
async def help_command(interaction):
  await interaction.response.send('help!')