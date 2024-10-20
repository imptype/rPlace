import os
import json
import time
import aiohttp
import asyncio
import datetime
import traceback
import threading
import contextlib
import multiprocessing
import discohook
from starlette.responses import PlainTextResponse, JSONResponse, Response
#from starlette.middleware import Middleware
#from starlette.middleware.base import BaseHTTPMiddleware
from .utils import constants, database, helpers
from .cogs.ping import ping_command
from .cogs.help import help_command
from .cogs.canvas import canvas_command
from .cogs.localcanvas import local_canvas_command
from .cogs.preview import preview_command
from .cogs.color import color_command
from .cogs.test import test_command
from .screens.start import StartView
from .screens.explore import ExploreView, color_modal, jump_modal
from .screens.top import TopView
from .screens.settings import SettingsView, resize_modal, cooldown_modal, reset_modal, spawn_modal, allowed_modal, whiteout_modal, expire_modal
from .screens.color import ColorView

# using custom vercel runtime
#expire_time = 5 # safe for deta

# class CustomMiddleware(BaseHTTPMiddleware):
#   # new session per threadid/event loop that uses same app instance
#   async def dispatch(self, request, call_next): # keeps session open until request is completed, 10 seconds
#     if not hasattr(request.app.http, 'initial_session'):
#       request.app.http.initial_session = request.app.http.session
#       request.app.http.sessions.append((time.time(), request.app.http.session)) # timed out too

#     now = time.time()

#     request.app.http.session = aiohttp.ClientSession('https://discord.com') # s[key]
#     request.app.http.sessions.append((now, request.app.http.session))

#     request.app.db = database.Database(request.app, os.getenv('DB')) # s[key]
#     request.app.dbs.append((now, request.app.db))

#     for sessions in (request.app.http.sessions, request.app.dbs): # cleanup
#       indexes_to_remove = []
#       for i, (timestamp, session) in enumerate(sessions):
#         if timestamp + expire_time < now:
#           await session.close()
#           indexes_to_remove.append(i)
#       for i in reversed(indexes_to_remove):
#         del sessions[i]
    
#     return await call_next(request)

def run():

  # discohook.Client.dbs = []
  # discohook.https.HTTPClient.sessions = []

  """# monkeypatch discohook.https.HTTPClient.session to use different sessions based on current thread id
  def getter(self):
    key = threading.get_ident()
    session = self.sessions.get(key)
    if not session:
      raise ValueError('session not found, is middleware active?')
    return session

  def setter(self, session):
    print('Closed initial session.')
    asyncio.ensure_future(session.close(), loop = session.loop) # schedule the close

  discohook.https.HTTPClient.sessions = {}
  discohook.https.HTTPClient.session = property(getter, setter)

  # monkey patch discohook.Client to use db using the right event loop, no initial session created with app
  def db(self):
    key = threading.get_ident()
    db = self.dbs.get(key)
    if not db:
      raise ValueError('db not found, is middleware active?')
    return db
  discohook.Client.dbs = {} # note this is a shared class attribute, will clash if we use multiple clients in the future
  discohook.Client.db = property(db)
  """
  # Lifespan to attach .db attribute, cancel + shutdown is for local testing
  @contextlib.asynccontextmanager
  async def lifespan(app):
    # app.http.session = session # monkeypatch in async environment for gunicorn
    async with database.Database(app, os.getenv('DB')) as app.db:
      try:
        yield
      finally:
        if app.http.session: # close bot session
          await app.http.session.close()

  # Define the bot
  app = discohook.Client(
    application_id = int(os.getenv('ID')),
    public_key = os.getenv('KEY'),
    token = os.getenv('TOKEN'),
    password = os.getenv('PASS'),
    lifespan = lifespan#,
    #middleware = [Middleware(CustomMiddleware)]
  )

  # Attach error handlers
  app.errors = []
  app.error_webhook = discohook.PartialWebhook.from_url(app, os.getenv('LOG'))
  @contextlib.asynccontextmanager
  async def handle_error(error, instance = None): # this formats the error and logs it
    # Build error text with local variable values
    text = '{}: {}'.format(type(error).__name__, str(error))
    text += '\n'
    text += '.'.join(map(lambda x: x.__name__, error.__class__.__mro__))
    text += '\n\n'
    if isinstance(instance, discohook.Interaction):
      interaction = instance
      text += 'Command: /{}'.format(interaction.payload['data']['name']) if interaction.type == 2 else 'Component: {}'.format(interaction.data['custom_id'])
      text += '\n'
      text += 'User: {} | {}, Guild: {}'.format(interaction.author.name, interaction.author.id, interaction.guild_id)
    else: # request object
      request = instance
      text += 'HTTP Exception: 500 Internal Server Error'
      text += '\n'
      text += 'Route: {}'.format(request.url.path)
    text += '\n\n'
    trace = tuple(traceback.TracebackException.from_exception(error).format())
    text += ''.join(trace)
    text += '\n\n'
    text += trace[0].rstrip() + '\n'
    frame = error.__traceback__.tb_next
    for i in trace[1:-2]:
      text += i # File ...
      for i, (k, v) in enumerate(frame.tb_frame.f_locals.items()):
        text += '\t{} = {}\n'.format(k, helpers.short_text(repr(v), 10000))
        if i > 100:
          text += '\t{} skipped.'.format(len(frame.tb_frame.f_locals) - 100)
          break
      frame = frame.tb_next
      if not frame:
        break
    text += ''.join(trace[-2:])
    print(text)

    now = datetime.datetime.utcnow()
    if isinstance(instance, discohook.Interaction):
      print('Now vs when:', datetime.datetime.fromtimestamp(interaction.created_at), now)
    else:
      print('Now:', now)
    
    # Respond and log
    content = 'Test ' if app.test else ''

    data = ['']
    yield data
    content += data[0]
    await app.error_webhook.send(content.strip(), file = discohook.File('error.txt', content = text.encode()))

  @app.on_interaction_error()
  async def on_interaction_error(interaction, error):
    app.errors.append(str(error))

    # Ignore
    if isinstance(error, discohook.errors.CheckFailure):
      return print('Ignoring check failure', str(interaction.author), interaction.data['custom_id'].split(':')[0])
    elif isinstance(error, NotImplementedError):
      return print('Ignoring component not found', str(interaction.author), interaction.data)
    elif isinstance(error, helpers.MaintenanceError):
      return print('Ignoring maintenance failure', error.message)
      
    async with handle_error(error, interaction) as hr:
      try:
        if interaction.responded:
          await interaction.response.followup('Sorry, an error has occurred (after responding).')
        else:
          await interaction.response.send('Sorry, an error has occurred.')
      except:
        hr[0] = '(failed)'
  
  @app.on_error()
  async def on_error(request, error):
    async with handle_error(error, request):
      return JSONResponse({error.__class__.__name__: str(error)}, 500)

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
  app.cooldowns = {} # local_id : user_id : ends_at timestamp

  # Set bot started at timestamp
  app.started_at = datetime.datetime.utcnow()

  # Set bot version
  app.version = constants.BOT_VERSION

  # Set if bot is test or not
  app.test = bool(os.getenv('test'))

  # Set if the bot is in maintenance or not, contains reason too
  app.maintenance = os.getenv('MAIN')

  # Load persistent view/components
  app.load_view(StartView())
  app.load_view(ExploreView())
  app.load_view(TopView())
  app.load_view(SettingsView())
  app.load_view(ColorView())
  app.active_components[color_modal.custom_id] = color_modal
  app.active_components[jump_modal.custom_id] = jump_modal
  app.active_components[resize_modal.custom_id] = resize_modal
  app.active_components[cooldown_modal.custom_id] = cooldown_modal
  app.active_components[reset_modal.custom_id] = reset_modal
  app.active_components[spawn_modal.custom_id] = spawn_modal
  app.active_components[allowed_modal.custom_id] = allowed_modal
  app.active_components[whiteout_modal.custom_id] = whiteout_modal
  app.active_components[expire_modal.custom_id] = expire_modal

  # Add commands
  commands = (
    ping_command,
    help_command,
    canvas_command,
    local_canvas_command,
    preview_command,
    #color_command
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
        'Extra: {}'.format(
          app.http.session.loop == asyncio.get_running_loop()
          if app.http.session else 'N/A'
        ),
        'Main: {}'.format(app.maintenance),
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