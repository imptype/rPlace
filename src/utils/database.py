import time
from deta import Deta, Query, Record, Updater

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

  async def get_grid(self, local_id):
    query = Query()
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
    record = Record(
      key,
      local_id = local_id,
      **kwargs
    )
    await self.pixels.insert(record)

  async def update_tile(self, local_id, y, x, tile): # make sure row exists, db fetch prior
    key = get_key(local_id, y) # this is broken for local dms unsure why, bad chars in keys?
    q = Query()
    q.equals('key', key)
    results = await self.pixels.fetch([q])
    print('fetch results', results)
    updater = Updater()
    updater.set(str(x), tile)
    await self.pixels.update(key, updater)