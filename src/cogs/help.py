import discohook

@discohook.command('help', 'shows commands list and tutorial')
async def help_command(interaction):
  await interaction.response('Hey, the only command available is `/canvas`, to explore and re-color pixels on the global canvas.')

  #if interaction.author.id == '364487161250316289':
  #  await interaction.client.db.setup()