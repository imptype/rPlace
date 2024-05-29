import io
import asyncio
import discohook
from PIL import Image

@discohook.button.new('clear', custom_id = 'clear_button:v3.7')
async def clear_button(interaction):
  await interaction.response.update_message('cleared attachments', files = None)

@discohook.command.slash('test', description = 'Test stuff!')
async def test_command(interaction):

  def blocking():
    im = Image.new('RGB', (1000, 500), (0, 255, 255)) # color is cyan
    buffer = io.BytesIO()
    im.save(buffer, 'PNG')
    return buffer

  buffer = await asyncio.to_thread(blocking)
  file = discohook.File('color.png', content = buffer.getvalue())

  view = discohook.View()
  view.add_buttons(clear_button)
  await interaction.response.send(file = file, view = view)