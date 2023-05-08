import os
import json
import traceback
import discohook
from .extras import constants, database, utils
from .cogs.help import help_command
from .cogs.canvas import canvas_command
from .screens.explore import ExploreView, color_modal

def run():
  
  # Define the bot
  app = discohook.Client(
    application_id = int(os.getenv('ID')),
    public_key = os.getenv('KEY'),
    token = os.getenv('TOKEN')
  )

  # Attach constants, database, helper functions
  app.constants = constants
  app.db = database.Database(os.getenv('DB'))
  app.utils = utils

  # Add canvas data to app on startup (cache)
  @app.on_event('startup')
  async def startup_event():
    app.grid = await app.db.dump()

  # Cleanup sessions on shutdown (for local hosting)
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

  # Set custom ID parser
  @app.custom_id_parser
  async def custom_id_parser(custom_id):
    if custom_id.startswith('place') or custom_id.endswith('dynamic'):
      return ':'.join(custom_id.split(':')[:2]) # e.g. place:V0.0 returned
    return custom_id

  # Load persistent view/components
  app.load_components(ExploreView())
  app.active_components[color_modal.custom_id] = color_modal

  # Load locale texts
  app.texts = {}
  langs = ['en', 'fr']
  for lang in langs:
    path = 'src/texts/{}.json'.format(lang)
    with open(path) as f:
      app.texts[lang] = json.loads(f.read())

  # Attach cooldown cache (userid: timestmap)
  app.cooldowns = {}

  # Add commands
  app.add_commands(
    help_command,
    canvas_command
  )

  # Return app object
  return app