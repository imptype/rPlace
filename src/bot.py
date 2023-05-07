import os
import traceback
import discohook
from .classes.database import Database
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

  # Attach constants
  app.constants = constants

  # Attach database
  app.db = Database(os.getenv('DB'))

  # Add canvas data to app on startup (cached)
  @app.on_event('startup')
  async def startup_event():
    app.grid = await app.db.dump()

  # Cleanup sessions on shutdown
  @app.on_event('shutdown')
  async def shutdown_event():
    await app.http.session.close()
    await app.db.close()

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
  
  # Add commands
  app.add_commands(
    help_command,
    canvas_command
  )

  # Return app object
  return app