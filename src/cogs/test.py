import discohook

class TestModal(discohook.Modal):
  def __init__(self):
    super().__init__('Test Modal')
    self.add_field('Input Text', 'text', required = True)

  async def callback(self, interaction, *args): # self, interaction, text):
    await interaction.response('text: {}'.format(args))
    

fields = [discohook.TextInput('Input Text', 'text', required = True)]
@discohook.modal('Test Modal', fields)
async def test_modal(interaction, text):
  await interaction.response('text:' + text)

@discohook.button('click me')
async def test_button(interaction):
  
  #modal = TestModal()
  await interaction.send_modal(test_modal)

@discohook.command('test', 'test stuff')
async def test_command(interaction):
  view = discohook.View()
  view.add_buttons(test_button)
  await interaction.response(view = view)