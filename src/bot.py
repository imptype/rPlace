import os
import json
import asyncio
import datetime
import traceback
import contextlib
import discohook
from starlette.responses import Response, PlainTextResponse
from .utils import constants, database, helpers, counter
from .cogs.ping import ping_command
from .cogs.help import help_command
from .cogs.canvas import canvas_command
from .cogs.localcanvas import local_canvas_command
from .cogs.test import test_command
from .screens.start import StartView
from .screens.explore import ExploreView, color_modal, jump_modal

def run():
  
  # Lifespan to attach extra .session and .db attributes, cancel + shutdown is for local testing
  @contextlib.asynccontextmanager
  async def lifespan(app):
    async with database.Database(app, os.getenv('DB')) as app.db:
      try:
        yield
      except asyncio.CancelledError:
        print('Ignoring cancelled error. (CTRL+C)')
      else:
        print('Closed without errors.')
      finally:
        await app.http.session.close() # close bot session

  # Define the bot
  app = discohook.Client(
    application_id = int(os.getenv('ID')),
    public_key = os.getenv('KEY'),
    token = os.getenv('TOKEN'),
    password = os.getenv('PASS'),
    lifespan = lifespan
  )

  # Attach error handler
  app.errors = []
  error_log_webhook = discohook.PartialWebhook.from_url(app, os.getenv('LOG'))
  @app.on_interaction_error()
  async def on_error(interaction, error):
    if isinstance(error, discohook.errors.CheckFailure):
      return print('Ignoring check failure', str(interaction.author), interaction.data['custom_id'].split(':')[0])
    if interaction.responded:
      await interaction.response.followup('Sorry, an error has occured.')
    else:
      await interaction.response.send('Sorry, an error has occured (after responding).')
    trace = tuple(traceback.TracebackException.from_exception(error).format())
    app.errors.append(trace)
    text = ''.join(trace)
    print(text)
    await error_log_webhook.send(text[:2000])

  # Set custom ID parser
  @app.custom_id_parser()
  async def custom_id_parser(interaction, custom_id):
    if interaction.author.id != '364487161250316289':
      return await interaction.response.send('The bot is under maintenance, you may report to the support server for details!')
    return ':'.join(custom_id.split(':')[:2]) # name:v0.0 returned

  # Attach helpers and constants, might be helpful
  app.constants = constants
  app.helpers = helpers

  # Load locale texts
  app.texts = {}
  langs = ['en', 'fr']
  for lang in langs:
    path = 'src/texts/{}.json'.format(lang)
    with open(path) as f:
      app.texts[lang] = json.loads(f.read())

  # Attach caches
  #app.cooldowns = {} # userid : time (currently unused, reserved for future use?)
  #app.guilds = {} # serverid : None|Guild
  #app.users = {} # userid : None|PartialUser
  #app.active_users = counter.ExpiringCounter(60) # by userid in move, pop after 1 min of inactivity
  #app.active_pixels = counter.ExpiringCounter(60) # by place button's interactionid, pop after 1 min 

  # Set bot deployed at timestamp (unused)
  # app.deployed_at

  # Set bot started at timestamp
  app.started_at = datetime.datetime.utcnow()

  # Set bot version
  app.version = '2.2'

  # Set if bot is test or not
  app.test = bool(os.getenv('test'))

  # Set if the bot is in maintenance or not, contains reason too
  app.maintenance = os.getenv('MAIN')

  # Load persistent view/components
  app.load_components(StartView())
  app.load_components(ExploreView())
  app.active_components[color_modal.custom_id] = color_modal
  app.active_components[jump_modal.custom_id] = jump_modal

  # Add commands
  app.add_commands(
    ping_command,
    help_command,
    canvas_command,
    local_canvas_command
  )
  if app.test:
    app.add_commands(test_command)

  # Return app object
  return app