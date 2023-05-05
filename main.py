import os
import json

# Load configs for local hosting
try:
  with open('config.json') as f: 
    config = json.loads(f.read())
  for key, value in config.items():
    os.environ[key] = value
except:
  pass

# Validate pass
if os.getenv('PASS') != '1234':
  exit()

from src.bot import run

print('''
        ______  _                  _ 
  _ __ / /  _ \| | __ _  ___ ___  | |
 | '__/ /| |_) | |/ _` |/ __/ _ \ | |
 | | / / |  __/| | (_| | (_|  __/ |_|
 |_|/_/  |_|   |_|\__,_|\___\___| (_)
''')

app = run()
