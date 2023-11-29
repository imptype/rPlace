import os
import json
import asyncio
import datetime
import traceback
import contextlib
import discohook
from starlette.responses import PlainTextResponse, Response
from .utils import constants, database, helpers
from .cogs.ping import ping_command
from .cogs.help import help_command
from .cogs.canvas import canvas_command
from .cogs.localcanvas import local_canvas_command
from .cogs.test import test_command
from .screens.start import StartView
from .screens.explore import ExploreView, color_modal, jump_modal
from .screens.top import TopView

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
    elif isinstance(error, NotImplementedError):
      return print('Ignoring component not found', str(interaction.author), interaction.data)
    elif isinstance(error, helpers.MaintenanceError):
      return print('Ignoring maintenance failure', error.message)
    if interaction.responded:
      await interaction.response.followup('Sorry, an error has occured (after responding).')
    else:
      await interaction.response.send('Sorry, an error has occured.')
    trace = tuple(traceback.TracebackException.from_exception(error).format())
    app.errors.append(trace)
    text = ''.join(trace)
    print(text)
    await error_log_webhook.send(text[:2000])

  # Set custom ID parser
  @app.custom_id_parser()
  async def custom_id_parser(interaction, custom_id):
    await helpers.maintenance_check(interaction)
    await helpers.before_invoke_check(interaction)
    name, version = custom_id.split(':')[:2]
    if version.removeprefix('v') != app.version:
      await interaction.response.send('Message is outdated, please run the command again. (`{}` vs `v{}`)'.format(version, app.version))
      return
    if not interaction.from_originator:
      await interaction.response.send('This is not your interaction, please run your own instance of the command.', ephemeral = True)
    return ':'.join([name, version])

  # Attach other webhooks
  app.global_webhook = discohook.PartialWebhook.from_url(app, os.getenv('GLOBAL'))
  app.local_webhook = discohook.PartialWebhook.from_url(app, os.getenv('LOCAL'))
  app.hour_webhook = discohook.PartialWebhook.from_url(app, os.getenv('HOUR'))
  app.day_webhook = discohook.PartialWebhook.from_url(app, os.getenv('DAY'))
  app.week_webhook = discohook.PartialWebhook.from_url(app, os.getenv('WEEK'))

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

  # Attach configs
  app.cursor = None # stores pillow cursor image to be reused

  # Attach cache
  app.pixels = {} # local_id : grid, this is always updated on pixel placement, not for movement debounce of 1 min though
  app.users = {} # userid : name, avatar_url|None # not hash because supported by lib
  app.guilds = {} # guildid : name, icon hash|None
  app.refreshes = {} # local_id : int(timestamp) # indicates whether canvas was refreshed or not

  # Set bot started at timestamp
  app.started_at = datetime.datetime.utcnow()

  # Set bot version
  app.version = constants.BOT_VERSION

  # Set if bot is test or not
  app.test = bool(os.getenv('test'))

  # Set if the bot is in maintenance or not, contains reason too
  app.maintenance = os.getenv('MAIN')

  # Load persistent view/components
  app.load_components(StartView())
  app.load_components(ExploreView())
  app.load_components(TopView())
  app.active_components[color_modal.custom_id] = color_modal
  app.active_components[jump_modal.custom_id] = jump_modal

  # Add commands
  commands = (
    ping_command,
    help_command,
    canvas_command,
    local_canvas_command
  )
  for command in commands:
    command.checks.append(helpers.maintenance_check)
    command.checks.append(helpers.before_invoke_check)
  app.add_commands(*commands)
  
  # Add test command
  if app.test: # does not have maintenance lock, and locked to server anyway
    app.add_commands(test_command)

  # Attach / route for debugging
  @app.route('/', methods = ['GET'])
  async def root(request):
    return PlainTextResponse(
      '\n'.join([
        'Started: {}'.format(app.started_at),
        '',
        'Test: {}'.format(app.test),
        '',
        'Pixels Cache: \n  {}'.format('  \n'.join([
          '{}: {}'.format(local_id, grid) # len so readable
          for local_id, grid in app.pixels.items()
        ])),
        'Stats Cache: {}'.format(0),
        '',
        'Errors: {}'.format(json.dumps(app.errors, indent = 2)),
      ])
    )

  # Actions handler
  @app.route('/__space/v0/actions', methods = ['POST'])
  async def actions(request):
    data = await request.json()
    event = data['event']
    if event['id'] == 'check':
      await app.db.refresh_logs()
    elif event['id'] == 'snap':
      await app.db.take_snapshot()
    else:
      raise ValueError('Unhandled action id', data)
    return Response()

  # Return app object
  return app