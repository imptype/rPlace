"""
Database related functions, contains:
Default functions:
- tableExists     ; checks if the table exists
- deleteTable     ; deletes the table if exists
- createTable     ; creates the table, and does insertCells()
- insertCells     ; inserts y-axis cells
Custom functions:
- setupDatabase   ; setups the table, creates it the first time
- resetDatabase   ; recreates/resets the table by force
- updateCell      ; updates the given x, y cell
- getCell         ; gets a value from the given x, y cell
- getDatabaseData ; gets all data from database and parses into a 2d array of dicts/Nones.
"""

import json
from .queues import DatabaseQueue

table = 'canvas'
index = 'yaxis'
canvasSize = 250, 250 # max 1599 wide

try:
  db = DatabaseQueue()
except:
  raise Exception('Database URL, from .env file, is invalid.')
  

async def tableExists():
  return (await db.execute(f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table}'", fetch = True))[0]

async def deleteTable():
  await db.execute(f'DROP TABLE IF EXISTS {table}')

async def insertCells():
  rowData = ', '.join([f'({i + 1})' for i in range(canvasSize[1])])
  await db.execute(f'INSERT INTO {table} ({index}) VALUES {rowData}')
  
async def createTable():
  await deleteTable()
  columns = ', '.join([f'"{i + 1}" JSONB' for i in range(canvasSize[0])])
  await db.execute(f'CREATE TABLE {table} ({index} INT, {columns})'),
  await insertCells()

# Custom functions

async def setupDatabase():
  if not (await tableExists()):
    await createTable()
    print(f'Created new {table} table')

async def resetDatabase():
  await createTable()
  print(f'Recreated new {table} table')
  
async def getCell(x, y):
  res = (await db.execute(f'SELECT "{x}" FROM {table} WHERE {index} = {y}', fetch = True))[0][x]
  if res:
    return json.loads(res)

async def updateCell(x, y, data):
  await db.execute(f'UPDATE {table} SET "{x}" = \'{json.dumps(data)}\' WHERE {index} = {y}')

async def getDatabaseData():
  res = await db.execute(f'SELECT * FROM {table}', fetch = True)
  height = len(res)
  width = len(list(res[0].keys())) - 1
  grid = [[None] * height for _ in range(width)]
  for row in res:
    y = row[index]
    for cell in row.items():
      if cell[0] != index:
        x = int(cell[0])
        if cell[1]:
          grid[x - 1][y - 1] = json.loads(cell[1])
  return grid