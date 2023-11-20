import time
import deta

class Database(deta.Deta):
  def __init__(self, app, key):
    super().__init__(key)
    self.app = app
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