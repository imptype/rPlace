import discohook
from . import start # .start.StartView is circular import
from ..utils.constants import COLOR_BLURPLE

@discohook.button.new(emoji = '↖️', custom_id = 'upleft:v0.0')
async def upleft_button(interaction):
  await interaction.response.send('clicked upleft')

@discohook.button.new(emoji = '⬆️', custom_id = 'up:v0.0')
async def up_button(interaction):
  await interaction.response.send('clicked up')

@discohook.button.new(emoji = '↗️', custom_id = 'upright:v0.0')
async def upright_button(interaction):
  await interaction.response.send('clicked upright')

@discohook.modal.new('Color Modal', fields = [discohook.TextInput('test', 'test')], custom_id = 'color_modal:v0.0')
async def color_modal(interaction, test):
  await interaction.response.send('submit color modal {}'.format(test))

@discohook.button.new('Color: #000000', custom_id = 'color:v0.0', style = discohook.ButtonStyle.grey)
async def color_button(interaction):
  await interaction.response.send_modal(color_modal)

@discohook.button.new(emoji = '⬅️', custom_id = 'left:v0.0')
async def left_button(interaction):
  await interaction.response.send('clicked left')

@discohook.button.new(emoji = '🆗', custom_id = 'place:v0.0')
async def place_button(interaction):
  await interaction.response.send('clicked place')

@discohook.button.new(emoji = '➡️', custom_id = 'right:v0.0')
async def right_button(interaction):
  await interaction.response.send('clicked right')

@discohook.modal.new('Jump Modal', fields = [discohook.TextInput('test', 'test')], custom_id = 'jump_modal:v0.0')
async def jump_modal(interaction, test):
  await interaction.response.send('submit jump modal {}'.format(test))

@discohook.button.new('Jump to (X, Y)', style = discohook.ButtonStyle.grey, custom_id = 'jump:v0.0')
async def jump_button(interaction):
  await interaction.response.send('clicked jump')

@discohook.button.new(emoji = '↙️', custom_id = 'downleft:v0.0')
async def downleft_button(interaction):
  await interaction.response.send('clicked downleft')

@discohook.button.new(emoji = '⬇️', custom_id = 'down:v0.0')
async def down_button(interaction):
  await interaction.response.send('clicked down')

@discohook.button.new(emoji = '↘️', custom_id = 'downright:v0.0')
async def downright_button(interaction):
  await interaction.response.send('clicked downright')

@discohook.button.new('Back To Home', style = discohook.ButtonStyle.grey, custom_id = 'return:v0.0')
async def return_button(interaction):
  await start.StartView(interaction).update()

step_options = [
  discohook.SelectOption(str(i), str(i))
  for i in [1, 2, 3, 4, 5, 10, 15, 20, 25]#, 50, 100, 150, 200, 256]
]
@discohook.select.text(step_options, placeholder = 'step_select', custom_id = 'step_select:v0.0')
async def step_select(interaction, values):
  await interaction.response.send('clicked step select {}'.format(values))

zoom_options = [
  discohook.SelectOption('{0}x{0}'.format(i), str(i))
  for i in [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]#, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51]
]
@discohook.select.text(zoom_options, placeholder = 'zoom_select', custom_id = 'zoom_select:v0.0')
async def zoom_select(interaction, values):
  await interaction.response.send('clicked zoom select {}'.format(values))

class ExploreView(discohook.View):
  def __init__(self, interaction = None): # View is persistent if args not given
    super().__init__()

    if interaction:
      self.interaction = interaction

      self.embed = discohook.Embed(
        'Selecting Tile (X, Y)',
        description = '\n'.join([
          '🎨 #000000',
          '🧍 imptype + dm hyperlink userid',
          '🏠 bots support + invite link in future?',
          '⏰ <t:123 :>'
        ]),
        color = COLOR_BLURPLE
      )
    
    self.add_buttons(upleft_button, up_button, upright_button, color_button)
    self.add_buttons(left_button, place_button, right_button, jump_button)
    self.add_buttons(downleft_button, down_button, downright_button, return_button)
    self.add_select(step_select)
    self.add_select(zoom_select)

  async def update(self): # need a setup above here to ainit
    await self.interaction.response.update_message(embed = self.embed, view = self)