import discohook

@discohook.button(emoji = '↖️', custom_id = 'upleft:v0.0')
async def upleft_button(interaction):
  await interaction.response('click {}'.format(interaction.client.utils.get_button_name(interaction)))

@discohook.button(emoji = '⬆️', custom_id = 'up:v0.0')
async def up_button(interaction):
  await interaction.response('click {}'.format(interaction.client.utils.get_button_name(interaction)))

@discohook.button(emoji = '↗️', custom_id = 'upright:v0.0')
async def upright_button(interaction):
  await interaction.response('click {}}'.format(interaction.client.utils.get_button_name(interaction)))

@discohook.button(emoji = '⬅️', custom_id = 'left:v0.0')
async def left_button(interaction):
  await interaction.response('click {}'.format(interaction.client.utils.get_button_name(interaction)))

@discohook.button(emoji = '🆗', custom_id = 'place:v0.0')
async def place_button(interaction):
  await interaction.response('click {}'.format(interaction.client.utils.get_button_name(interaction)))

@discohook.button(emoji = '➡️', custom_id = 'right:v0.0')
async def right_button(interaction):
  await interaction.response('click {}'.format(interaction.client.utils.get_button_name(interaction)))

@discohook.button(emoji = '↙️', custom_id = 'downleft:v0.0')
async def downleft_button(interaction):
  await interaction.response('click {}'.format(interaction.client.utils.get_button_name(interaction)))

@discohook.button(emoji = '⬇️', custom_id = 'down:v0.0')
async def down_button(interaction):
  await interaction.response('click {}'.format(interaction.client.utils.get_button_name(interaction)))

@discohook.button(emoji = '↘️', custom_id = 'downright:v0.0')
async def downright_button(interaction):
  await interaction.response('click {}'.format(interaction.client.utils.get_button_name(interaction)))

explore_view = discohook.View()
explore_view.add_button_row(upleft_button, up_button, upright_button)#, color_button)
explore_view.add_button_row(left_button, place_button, right_button)#, jump_button)
explore_view.add_button_row(downleft_button, down_button, downright_button)#, return_button)
#explore_view.add_select_menu(step_select)
#explore_view.add_select_menu(zoom_select)

"""
@discohook.button('Color: #000000', custom_id = 'color:v0.0', style = discohook.ButtonStyle.grey)
async def color_button(interaction):
  await interaction.response('click {} {}'.format(get_component(interaction)['emoji']['name']))

@discohook.button(label = 'Jump to (X, Y)', style = discohook.ButtonStyle.grey)
async def jump_button(interaction):
  pass
  
@discohook.button(label = 'Back To Home', style = discohook.ButtonStyle.grey)
async def return_button(interaction):
  pass

@select([SelectOption('test', '1')], placeholder = 'Step Size: X')
async def step_select(interaction):
  pass

@select([SelectOption('test', '1')], placeholder = 'Zoom Size: XxY')
async def zoom_select(interaction):
  pass"""