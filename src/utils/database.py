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

"""   self.test = self.base('test')#self.base('global') # or canvas
    self.size = 25

  async def reset(self):
    print('Resetting...')
    q = deta.Query()
    results = await self.test.fetch([q])
    data = await results.json()
    rows = data['items']
    if rows != []:
      print('Deleting rows...')
      for i, row in enumerate(rows):
        key = row['key']
        print(key, i, len(rows))
        await self.test.delete(key)
    print('Done reset!')

  async def setup(self):
    print('Setting up...')
    q = deta.Query()
    results = await self.test.fetch([q])
    data = await results.json()
    rows = data['items']
    if rows == []:
      print('Inserting rows...')
      n = self.size
      rows = [
        deta.Record(
          {
            x : None
            for x in range(n)
          },
          key = str(y)
        )
        for y in range(n)
      ]
      await self.test.insert(*rows)
    print('Done setup!')
  
  async def dump(self):
    print('Dumping...')
    q = deta.Query()
    results = await self.test.fetch([q])
    data = await results.json()
    rows = sorted(data['items'], key = lambda x : int(x['key'])) # order-by key (Y), 62,500 loops
    if not rows or len(rows) != self.size: # rerun after setting up
      return None
    n = self.size
    grid = []
    for x in range(n):
      row = []
      for y in range(n):
        row.append(rows[y][str(x)])
      grid.append(row)
    print('Done dump!')
    return grid
  
  async def update(self, x, y, data): # key is treated as Y value, columns are X value
    print('Updating', x, y, '...')
    updater = deta.Updater()
    updater.set(str(x), data)
    await self.test.update(str(y), updater)
    print('Updated', x, y, '!')"""