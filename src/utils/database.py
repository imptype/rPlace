import io
import time
import asyncio
import datetime
import discohook
from deta import Deta, Query, Record, Updater
from ..utils.helpers import convert_text, to_chunks, get_grid, draw_map
from ..utils.constants import CANVAS_SIZE

def get_key(local_id, y):
  y_key = str(y).zfill(3)
  if local_id:
    key = '{} {}'.format(y_key, local_id)
  else:
    key = y_key
  return key

class Database(Deta):
  def __init__(self, app, key, loop = None):
    super().__init__(key, loop = loop)
    self.app = app
    self.names = ['pixels', 'logs', 'config', 'cooldowns'] # config reserved for snapshots/meta
    for name in self.names:
      setattr(self, name, self.base(name))

  async def get_grid(self, local_id = None):
    query = Query()
    if local_id:
      local_id = convert_text(local_id) # saves storage, ignore None
    query.equals('local_id', local_id)
    
    grid = {}
    configs = {
      'exist' : False, # when updating row, if y0 row exists, this will be True
      'local' : bool(local_id) # used for draw grid/skip the reset check
    }
    results = (await self.pixels.fetch([query]))['items']
    if results:
      # extract configs from first record [Y0]
      if results[0]['key'].startswith('000'): # ensure it is Y 0
        configs['size'] = results[0].pop('size', CANVAS_SIZE)
        if isinstance(configs['size'], int): # legacy sizes
          configs['size'] = (configs['size'], configs['size'])
        configs['cooldown'] = results[0].pop('cooldown', None)
        configs['reset'] = results[0].pop('reset', 0)
        configs['flip'] = results[0].pop('flip', 0)
        configs['spawn'] = results[0].pop('spawn', None)
        configs['allowed'] = results[0].pop('allowed', None) # id is string because > 16
        configs['whiteout'] = results[0].pop('whiteout', None)
        configs['noedit'] = results[0].pop('noedit', 0)
        configs['exist'] = True
      for record in results:
        y = record['key'].split(' ')[0] # incase local id exists, it just gets the Y value
        y = int(''.join([y[:-1].lstrip('0'), y[-1]])) # convert 000, 020 to 0, 20
        del record['key']
        del record['local_id']
        grid[y] = record
    return grid, configs
  
  async def update_configs(self, local_id, exists, config, value):
    assert local_id, 'not allowed for global canvas'
    key = get_key(local_id, 0)
    if exists:
      updater = Updater()
      updater.set(config, value)
      await self.pixels.update(key, updater)
    else:
      kwargs = {config : value}
      local_id = convert_text(local_id) # saves storage
      record = Record(key, local_id = local_id, **kwargs)
      await self.pixels.insert(record)
  
  async def create_row(self, local_id, y, x, tile):
    key = get_key(local_id, y)
    kwargs = {str(x) : tile}
    if local_id:
      local_id = convert_text(local_id) # saves storage
    record = Record(key, local_id = local_id, **kwargs)
    await self.pixels.insert(record)

  async def update_tile(self, local_id, y, x, tile): # make sure row exists, db fetch prior
    key = get_key(local_id, y) # compressed is broken for local dms unsure why, bad chars in keys?
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
    await asyncio.gather(self.handle_logs(), self.handle_logs(True)) # global and local separately

  async def take_snapshot(self):
    (grid, configs) = await self.get_grid()

    def blocking(): # saving is also stuffed here due to blocking
      im = draw_map(grid, configs)
      buffer = io.BytesIO()
      im.save(buffer, 'PNG')
      return buffer

    # draw canvas
    buffer = await asyncio.to_thread(blocking)

    # args
    now = int(time.time())
    content = '<t:{}:R>'.format(now)
    image_file = discohook.File('map.png', content = buffer.getvalue())

    # send to hourly / this is used for testing usually
    message = await self.app.hour_webhook.send(content, file = image_file, wait = True)
    if not self.app.test:
      await message.crosspost()

    # check if new day or week
    d = datetime.datetime.fromtimestamp(now)
    if 17 < d.hour < 22: # saves unnecessary db reads, between 6:00PM-10:00PM GMT

      query = Query()
      key = 'snap'
      query.equals('key', key)
      record = (await self.config.fetch([query]))['items']
      if record:
        record = record[0]['value']
      else: # first time
        record = {
          'day' : -1,
          'month' : -1
        }
        await self.config.insert(Record(key, value = record))

      # update new day
      if d.month != record['month'] or d.day != record['day']:
        if self.app.test:
          print('send day snapshot')
        else:
          await (await self.app.day_webhook.send(content, file = image_file, wait = True)).crosspost()
        
        # update new week here too
        if d.weekday() == 5: # only on saturdays
          if self.app.test:
            print('send week snapshot')
          else:
            await (await self.app.week_webhook.send(content, file = image_file, wait = True)).crosspost()
        
        record['day'] = d.day
        record['month'] = d.month

        updater = Updater()
        updater.set('value', record)
        await self.config.update(key, updater)
  
  async def get_cooldown(self, key):
    query = Query()
    query.equals('key', key)
    results = (await self.cooldowns.fetch([query], limit = 1))['items']
    if results:
      return results[0]['__expires'] # name of ends_at

  async def add_cooldown(self, key, ends_at):
    record = Record(key, expire_at = datetime.datetime.fromtimestamp(ends_at))
    await self.cooldowns.insert(record)