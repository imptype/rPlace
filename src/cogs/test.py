import discohook

@discohook.command.slash('test', description = 'Test stuff!')
async def test_command(interaction):
  await interaction.response.send('test!')