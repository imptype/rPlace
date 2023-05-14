import discohook

@discohook.command('help', 'shows commands list and tutorial')
async def help_command(interaction):
  interaction.client.utils.before_invoke(interaction)
  await interaction.response(interaction.client.utils.locale_text(interaction, 'help_text'))

  # This is secretly used to reset the canvas.
  # if interaction.author.id == '364487161250316289':
  #   await interaction.client.db.reset()
  #   await interaction.client.db.setup()
  #   interaction.client.grid = await interaction.client.db.dump()