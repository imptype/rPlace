import discohook

@discohook.command.slash('test', description = 'Test stuff!')
async def test_command(interaction):
  if interaction.author.id != '364487161250316289':
    return interaction.response.send('Denied')
  await interaction.response.send('test!')
  await interaction.client.db.take_snapshot()