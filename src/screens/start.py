import discohook
from ..utils.constants import COLOR_BLURPLE

@discohook.button.new('Explore', emoji = '🔍', custom_id = 'explore:v0.0')
async def explore_button(interaction):
  await interaction.response.send('clicked explore button')

@discohook.button.new(emoji = '🏆', custom_id = 'top:v0.0', style = discohook.ButtonStyle.green)
async def top_button(interaction):
  await interaction.response.send('clicked top button')

@discohook.button.new(emoji = '🔄', custom_id = 'refresh:v0.0')
async def refresh_button(interaction):
  await interaction.response.send('clicked refresh button')

class StartView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    if interaction:
      self.interaction = interaction
      self.embed = discohook.Embed(
        'Welcome to r/Place!',
        description = '\n'.join([
          'Canvas size: 1000x1000',
          '',
          'Click 🔍 **Explore** to start exploring!'
        ]),
        color = COLOR_BLURPLE
      )
    self.add_buttons(explore_button, top_button, refresh_button)
  
  async def send(self):
    await self.interaction.response.send(embed = self.embed, view = self)