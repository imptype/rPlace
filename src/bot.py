import os
import traceback
import discohook
from .cogs.help import help_command
from .cogs.canvas import canvas_command
from . import constants

def run():
  
  # Define the bot
  app = discohook.Client(
    application_id = int(os.getenv('ID')),
    public_key = os.getenv('KEY'),
    token = os.getenv('TOKEN')
  )

  # Attach error handler
  log_channel_id = os.getenv('LOG')
  @app.on_error
  async def on_error(interaction, error):
    if interaction.responded:
      await interaction.followup('Sorry, an error has occured (after responding).')
    else:
      await interaction.response('Sorry, an error has occured.')
    text = ''.join(traceback.TracebackException.from_exception(error).format())
    await app.send_message(log_channel_id, text[:2000])
    print(text)
  
  # Attach constants
  app.constants = constants
  
  # Add commands
  app.add_commands(
    help_command,
    canvas_command
  )

  # Return app object
  return app