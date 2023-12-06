import os
import json

# Load configs for local hosting
path = 'config.json'
if os.path.isfile(path): # <-- file won't exist in production
  with open(path) as f: 
    config = json.loads(f.read())
  for key, value in config.items():
    os.environ[key] = value
  os.environ['test'] = '1'

# Validate keys
keys = ('START', 'PASS', 'ID', 'KEY', 'TOKEN', 'LOG', 'DB', 'MAIN')
assert all(key in os.environ for key in keys), 'fail key'

# Validate pass
if os.getenv('START') != '123':
  exit()

from src.bot import run

if os.getenv('test'):
  print('''
         ______  _                  _ 
   _ __ / /  _ \| | __ _  ___ ___  | |
  | '__/ /| |_) | |/ _` |/ __/ _ \ | |
  | | / / |  __/| | (_| | (_|  __/ |_|
  |_|/_/  |_|   |_|\__,_|\___\___| (_)
  ''')

# Run the bot
app = run()