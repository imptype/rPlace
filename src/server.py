import os
import aiohttp
import asyncio
import contextlib
import discohook
from starlette.applications import Starlette
from starlette.responses import Response
from .utils import database

def run():

  # Lifespan to attach .client.session and .db attribute, cancel + shutdown is for local testing
  @contextlib.asynccontextmanager
  async def lifespan(app):
    async with aiohttp.ClientSession('https://discord.com') as session:
      setattr(app, 'http', discohook.https.HTTPClient(None, os.getenv('TOKEN'), session)) # for referencing in database.py
      async with database.Database(app, os.getenv('DB')) as app.db:
        try:
          yield
        except asyncio.CancelledError:
          print('Ignoring cancelled error. (CTRL+C)')
        else:
          print('Closed without errors.')
        finally:
          await app.http.session.close() # close http session

  # Define app
  app = Starlette(lifespan = lifespan)
  app.test = bool(os.getenv('test'))

  # Attach webhooks
  app.global_webhook = discohook.PartialWebhook.from_url(app, os.getenv('GLOBAL'))
  app.local_webhook = discohook.PartialWebhook.from_url(app, os.getenv('LOCAL'))
  app.hour_webhook = discohook.PartialWebhook.from_url(app, os.getenv('HOUR'))
  app.day_webhook = discohook.PartialWebhook.from_url(app, os.getenv('DAY'))
  app.week_webhook = discohook.PartialWebhook.from_url(app, os.getenv('WEEK'))

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
    
  # Test route
  if app.test:
    @app.route('/test')
    async def test(request):
      print('Test')
      await app.db.take_snapshot()
      return Response()

  # Return app object
  return app