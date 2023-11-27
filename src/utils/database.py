import time
import string
import asyncio
from deta import Deta, Query, Record, Updater
from ..utils.helpers import convert_text, to_chunks

def get_key(local_id, y):
  y_key = str(y).zfill(3)
  if local_id:
    key = '{} {}'.format(y_key, local_id)
  else:
    key = y_key
  return key

class Database(Deta):
  def __init__(self, app, key):
    super().__init__(key)
    self.app = app
    self.pixels = self.base('pixels')
    self.logs = self.base('logs')

  async def get_grid(self, local_id):
    query = Query()
    if local_id:
      local_id = convert_text(local_id, string.digits) # saves storage, ignore None
    query.equals('local_id', local_id)
    
    grid = {}
    for record in (await self.pixels.fetch([query]))['items']:
      y = record['key'].split(' ')[0] # incase local id exists, it just gets the Y value
      y = int(''.join([y[:-1].lstrip('0'), y[-1]])) # convert 000, 020 to 0, 20
      del record['key']
      del record['local_id']
      grid[y] = record
    return grid
  
  async def create_row(self, local_id, y, x, tile):
    key = get_key(local_id, y)
    kwargs = {str(x) : tile}
    if local_id:
      local_id = convert_text(local_id, string.digits) # saves storage
    record = Record(
      key,
      local_id = local_id,
      **kwargs
    )
    await self.pixels.insert(record)

  async def update_tile(self, local_id, y, x, tile): # make sure row exists, db fetch prior
    key = get_key(local_id, y) # this is broken for local dms unsure why, bad chars in keys?
    updater = Updater()
    updater.set(str(x), tile)
    await self.pixels.update(key, updater)
  
  async def record_log(self, username, user_id, x, y, color, guild_name, guild_id, local): # explicit
    key = str(int(time.time() * 10 ** 7)) # ensures unique key with nice timestamp
    record = Record(
      key,
      username = username,
      user_id = user_id,
      x = x,
      y = y,
      color = color,
      guild_name = guild_name,
      guild_id = guild_id,
      local = local
    )
    await self.logs.insert(record)

  async def handle_logs(self, local = False):
    query = Query()
    query.equals('local', local)
    records = (await self.logs.fetch([query]))['items']
    texts = {
      record['key'] : '<t:{}:R> `{}` | `{}` updated `({}, {})` to `#{:06x}` from {}'.format(
        int(int(record['key']) / 10 ** 7),
        record['username'],
        record['user_id'],
        record['x'],
        record['y'],
        record['color'],
        '{} | `{}`'.format(
          '`{}`'.format(record['guild_name']) if record['guild_name'] else '*Unknown Server*',
          record['guild_id']
        ) if record['guild_id'] else 'DMs'
      )
      for record in records
    }
    if texts:
      chunks = []
      temp = {}
      c = 0
      n = 2000 # max length of discord message, can change to embed later 31x for more characters (62000)
      d = '\n'
      for k in texts:
        if c + len(texts[k]) + len(d) > n:
          c = len(texts[k])
          chunks.append(temp)
          temp = {k : texts[k]}
        else:
          temp[k] = texts[k]
          c += len(texts[k])
      chunks.append(temp)

      ratelimit = 5 # 5 messages per 5 sec
      cooldown = 5
      rate_chunks = to_chunks(chunks, ratelimit)

      if local:
        webhook = self.app.local_webhook
      else:
        webhook = self.app.global_webhook

      for i, rate_chunk in enumerate(rate_chunks):
        if i:
          if i == 3: # to be safe/avoid resending, do max 3 times
            return (len(records), 'not done')
          await asyncio.sleep(cooldown) # hit rate limit, need to wait
        
        async def handle(chunk):
          # send
          content = '\n'.join(chunk.values())
          await webhook.send(content)

          # delete all log keys in it
          await asyncio.gather(*[self.logs.delete(k) for k in chunk.keys()])
        
        for chunk in rate_chunk:
          await handle(chunk) # this is slower but maintains order
        #await asyncio.gather(*[handle(chunk) for chunk in rate_chunk])
    
    return len(records)

  async def refresh_logs(self):
    print('start refresh')
    a, b = await asyncio.gather(self.handle_logs(), self.handle_logs(True)) # global and local separately
    print('end refresh {} {}'.format(a, b))