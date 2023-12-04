import discohook

@discohook.button.new('click me', custom_id = 'buttonasdasdas:v3.2_d')
async def test_button(interaction):
  response = await interaction.response.defer() # <- how to send a new "bot is thinking..." message
  await response.send('edited') # and edit it afterwards?

@discohook.command.slash('test', description = 'Test stuff!')
async def test_command(interaction):
  if interaction.author.id != '364487161250316289':
    return interaction.response.send('Denied')

  view = discohook.View()
  view.add_buttons(test_button)
  await interaction.response.send('content', view = view)