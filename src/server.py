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
      setattr(app, 'http', discohook.https.HTTPClient(None, None, session)) # for referencing in database.py
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

  # Attach webhooks
  app.global_webhook = discohook.PartialWebhook.from_url(app, os.getenv('GLOBAL'))
  app.local_webhook = discohook.PartialWebhook.from_url(app, os.getenv('LOCAL'))

  # Actions handler
  @app.route('/__space/v0/actions', methods = ['POST'])
  async def actions(request):
    data = await request.json()
    event = data['event']
    if event['id'] == 'check':
      await app.db.refresh_logs()
    else:
      raise ValueError('Unhandled action id', data)
    return Response()

  # Return app object
  return app