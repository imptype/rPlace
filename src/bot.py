import os
import json
import asyncio
import traceback
import discohook
from .extras import constants, database, utils, counter
from .cogs.help import help_command
from .cogs.canvas import canvas_command
# from .cogs.test import test_command
from .screens.start import StartView
from .screens.explore import ExploreView, color_modal, jump_modal

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
  # Simulate startup event with middleware since deta can't see it
  lock = asyncio.Lock()
  @app.middleware('http') # @app.on_event('startup')
  async def startup_event(request, call_next):
    async with lock:
      if not hasattr(app, 'grid'):
        app.grid = await app.db.dump()
    return await call_next(request)

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

  # Load locale texts
  app.texts = {}
  langs = ['en', 'fr']
  for lang in langs:
    path = 'src/texts/{}.json'.format(lang)
    with open(path) as f:
      app.texts[lang] = json.loads(f.read())

  # Attach caches
  app.cooldowns = {} # userid : time (currently unused, reserved for future use?)
  app.guilds = {} # serverid : None|Guild
  app.users = {} # userid : None|PartialUser
  app.active_users = counter.ExpiringCounter(60) # by userid in move, pop after 1 min of inactivity
  app.active_pixels = counter.ExpiringCounter(60) # by place button's interactionid, pop after 1 min 

  # Load persistent view/components
  app.load_components(StartView())
  app.load_components(ExploreView())
  app.active_components[color_modal.custom_id] = color_modal
  app.active_components[jump_modal.custom_id] = jump_modal

  # Add commands
  app.add_commands(
    help_command,
    canvas_command,
    # test_command
  )

  # Return app object
  return app