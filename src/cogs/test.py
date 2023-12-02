import discohook

@discohook.command.slash('test', description = 'Test stuff!')
async def test_command(interaction):
  if interaction.author.id != '364487161250316289':
    return interaction.response.send('Denied')

  print('1')
  content = 'a' * 2001 # <- goes over the 2000 char limit in message content
  await interaction.response.send(content)