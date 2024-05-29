import io
import random
import asyncio
import discohook
from PIL import Image
from ..utils.constants import COLOR_BLURPLE, CANVAS_SIZE, BOT_VERSION

@discohook.button.new('Regenerate', custom_id = 'regenerate:v{}'.format(BOT_VERSION))
async def regenerate_button(interaction):
  await ColorView(interaction).update()

@discohook.button.new('Presets', custom_id = 'presets:v{}'.format(BOT_VERSION), style = discohook.ButtonStyle.green)
async def presets_button(interaction):
  await ColorView(interaction).update(2)

class ColorView(discohook.View):
  def __init__(self, interaction = None, code = 1):
    super().__init__()
    if interaction:
      self.interaction = interaction
    else:
      self.add_buttons(regenerate_button, presets_button)

  async def setup(self, code):
    if code == 1:
      color = random.randint(0, 0xFFFFFF)

      self.embed = discohook.Embed(
        'Color: `#{:06x}`'.format(color),
        color = color
      )

      def blocking():
        im = Image.new('RGB', (1000, 500), ((color >> 16) & 255, (color >> 8) & 255, color & 255))
        buffer = io.BytesIO()
        im.save(buffer, 'PNG')
        return buffer

      # draw color
      buffer = await asyncio.to_thread(blocking)
      self.embed.set_image(discohook.File('color.png', content = buffer.getvalue()))

      dynamic_presets_button = presets_button
    elif code == 2:
      self.embed = discohook.Embed(
        'Color Presets',
        color = COLOR_BLURPLE
      )
      self.embed.set_image('https://media.discordapp.net/attachments/995453283885920356/1245333248910032988/colors.png')
      
      dynamic_presets_button = discohook.Button(
        presets_button.label,
        custom_id = presets_button.custom_id + ':',
        style = presets_button.style,
        disabled = True
      )
    else:
      raise ValueError('unsupported code', code)
    
    self.add_buttons(regenerate_button, dynamic_presets_button)

  async def send(self, code = 1):
    await self.setup(code)
    await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self, code = 1):
    await self.setup(code)
    await self.interaction.response.update_message(embed = self.embed, view = self, files = None)