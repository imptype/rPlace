import discohook

@discohook.command.slash('test', description = 'Test stuff!')
async def test_command(interaction):
  await interaction.response.send('did /test')
  print(interaction.author.joined_at)