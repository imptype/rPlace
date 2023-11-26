import time
from deta import Deta, Query

class Database(Deta):
  def __init__(self, app, key):
    super().__init__(key)
    self.app = app
    self.pixels = self.base('pixels')

  async def get_grid(self, local_id):
    query = Query()
    if local_id:
      query.equals('local_id', local_id)
    
    grid = {}
    for record in (await self.pixels.fetch([query]))['items']:
      k = record['key']
      k = int(''.join([k[:-1].lstrip('0'), k[-1]])) # convert 000, 020 to 0, 20
      del record['key']
      if local_id:
        del record['local_id']
      grid[k] = record
    return grid

  async def create_row(self, local_id, y, x, tile):
    pass

  async def update_tile(self, local_id, y, x, tile): # make sure row exists, db fetch prior
    updater = Updater()
    y_key = str(y).zfill(3) # max 999
    key = '{} {}'.format(y_key, local_id)
    updater.equals('key')
    updater.equals('local_id', local_id)
    pass
  
  async def update_tile(self, local_id, y, tile):
    record = Record(
      str(y).zfill(3),
      **row # x are strs with array values
    )

    print('this is record', record.payload)