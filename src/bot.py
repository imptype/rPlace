import os
import json
import aiohttp
import asyncio
import datetime
import traceback
import contextlib
import multiprocessing
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
from .screens.settings import SettingsView, resize_modal, cooldown_modal

def run():
  
  # Lifespan to attach .db attribute, cancel + shutdown is for local testing
  @contextlib.asynccontextmanager
  async def lifespan(app):
    async with aiohttp.ClientSession('https://discord.com', loop = asyncio.get_running_loop()) as session:
      await app.http.session.close()
      app.http.session = session # monkeypatch in async environment for gunicorn
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
    app.errors.append(str(error))

    # Ignore
    if isinstance(error, discohook.errors.CheckFailure):
      return print('Ignoring check failure', str(interaction.author), interaction.data['custom_id'].split(':')[0])
    elif isinstance(error, NotImplementedError):
      return print('Ignoring component not found', str(interaction.author), interaction.data)
    elif isinstance(error, helpers.MaintenanceError):
      return print('Ignoring maintenance failure', error.message)
      
    # Build error text with local variable values
    trace = tuple(traceback.TracebackException.from_exception(error).format())
    text = trace[0].rstrip() + '\n'
    frame = error.__traceback__.tb_next
    for i in trace[1:-2]:
      text += i # File ...
      for i, (k, v) in enumerate(frame.tb_frame.f_locals.items()):
        text += '\t{} = {}\n'.format(k, helpers.short_text(repr(v), 10000))
        if i > 100:
          text += '\t{} skipped.'.format(len(frame.tb_frame.f_locals) - 100)
          break
      frame = frame.tb_next
    text += ''.join(trace[-2:])
    print(text)

    # Respond and log
    if interaction.responded:
      respond = interaction.response.followup('Sorry, an error has occured (after responding).')
    else:
      respond = interaction.response.send('Sorry, an error has occured.')
    log = error_log_webhook.send('Test' if app.test else None, file = discohook.File('error.txt', content = text.encode()))
    await asyncio.gather(respond, log)

  # Set custom ID parser
  @app.custom_id_parser()
  async def custom_id_parser(interaction, custom_id):
    await helpers.maintenance_check(interaction)
    await helpers.before_invoke_check(interaction)
    #if custom_id.startswith(':'): (unused)
    #  custom_id = helpers.decrypt_text(custom_id[1:]) # ignore the first ':'
    #  interaction.data['custom_id'] = custom_id # update modal custom_id
    name, version = custom_id.split(':')[:2]
    if version.removeprefix('v') != app.version:
      await interaction.response.send('Message is outdated, please run the command again. (`{}` vs `v{}`)'.format(version, app.version))
      return
    if not interaction.from_originator:
      await interaction.response.send('This is not your interaction, please run your own instance of the command.', ephemeral = True)
      return
    if name.startswith('admin_') and not helpers.is_admin(interaction):
      await interaction.response.send('You do not have administrator permissions anymore so you cannot interact with this component.')
      return
    return ':'.join([name, version])

  # Set before invoke (if lifespan didn't work on serverless instance)
  @app.before_invoke()
  async def before_invoke(interaction): # force new sessions every request is the only way to fix it atm
    if interaction.kind != discohook.InteractionType.ping and not app.test:
      loop = asyncio.get_event_loop()
      #if app.http.session._loop != loop:
      app.http.session = aiohttp.ClientSession('https://discord.com', loop = loop)
      
      #if not hasattr(app, 'db'): # lifespan did not work
      app.db = database.Database(app, os.getenv('DB'), loop = loop)

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
  app.tops = {} # local_id : (top data), saves processing and currently has delays in updating
  app.locks = {} # local_id : asyncio.Lock, reload map one at a time
  app.cooldowns = {} # local_id:user_id : ends_at timestamp

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
  app.load_components(SettingsView())
  app.active_components[color_modal.custom_id] = color_modal
  app.active_components[jump_modal.custom_id] = jump_modal
  app.active_components[resize_modal.custom_id] = resize_modal
  app.active_components[cooldown_modal.custom_id] = cooldown_modal

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
        'Workers: {}'.format(multiprocessing.cpu_count() * 2 + 1),
        'Extra: {}'.format(app.http.session._loop == asyncio.get_running_loop()),
        'Test: {}'.format(app.test),
        '',
        'Pixels Cache:\n  {}'.format('\n  '.join([
          '{}: {}'.format(local_id, grid) # len so readable
          for local_id, grid in app.pixels.items()
        ])),
        'Users Cache:\n  {}'.format('\n  '.join([
          '{}: {}'.format(user_id, user_data)
          for user_id, user_data in app.users.items()
        ])),
        'Guilds Cache:\n  {}'.format('\n  '.join([
          '{}: {}'.format(guild_id, guild_data)
          for guild_id, guild_data in app.guilds.items()
        ])),
        'Refreshes Cache:\n  {}'.format('\n  '.join([
          '{}: {}'.format(local_id, timestamp)
          for local_id, timestamp in app.refreshes.items()
        ])),
        'Tops Cache:\n  {}'.format('\n  '.join([
          '{}: {}'.format(local_id, top_data)
          for local_id, top_data in app.tops.items()
        ])),
        'Locks Cache:\n  {}'.format('\n  '.join([
          '{}: {}'.format(local_id, lock)
          for local_id, lock in app.locks.items()
        ])),
        'Errors: {}'.format(json.dumps(app.errors, indent = 2)),
      ])
    )

  # Return app object
  return app