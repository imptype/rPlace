import time
import deta

class Database(deta.Deta):
  def __init__(self, key):
    super().__init__(key)
    self.test = self.base('test')#self.base('global') # or canvas

  async def setup(self):
    print('Setting up...')
    q = deta.Query()
    results = await self.test.fetch([q])
    data = await results.json()
    rows = data['items']
    if rows == []:
      print('Inserting rows...')
      n = 250
      rows = []
      for y in range(n):
        row = {0 : y + 1} # y 1, 2, 3, 4
        row.update({
          x + 1 : None # x 1, 2, 3
          for x in range(n)
        })
        rows.append(deta.Record(row))
      await self.test.insert(*rows)
    print('Done setup!')
  
  async def dump(self):
    print('Dumping...')
    q = deta.Query()
    results = await self.test.fetch([q])
    data = await results.json()
    rows = data['items']
    grid = {}
    for row in rows:
      y = row.pop('0')
      del row['key']
      grid[y] = row
    print('Done dump!')
    return grid