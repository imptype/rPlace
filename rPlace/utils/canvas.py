"""
Drawing with pillow, contains:
- blocking ; code to be run in executor/anything to do with pillow
- draw     ; draws the 2d grid with color
"""

from .functions import immutify
from .queues import DrawQueue, UploadQueue
import numpy as np
from PIL import Image
import io
from pprint import pprint
import json

uploadQueue = UploadQueue()
drawQueue = DrawQueue()
cache = {}
cursorColor = (0, 187, 212) #(100, 100, 100)
cursorPixels = (
  # Top left
  (0, 0), 
  (1, 0), 
  (2, 0), 
  (0, 1),
  (0, 2),

  #Top right
  (5, 0), 
  (6, 0), 
  (7, 0),
  (7, 1),
  (7, 2),

  #Bottom Left
  (0, 5),
  (0, 6),
  (0, 7),
  (1, 7),
  (2, 7),

  #Bottom right
  (7, 5),
  (7, 6),
  (5, 7),
  (6, 7),
  (7, 7)
)


# Return file like object of the image.
def blocking(grid, cursor = None, zoom = None):
  im = Image.fromarray(np.array(grid).astype('uint8')).convert('RGB')

  # If its a section
  if cursor:
    height = len(grid)
    width = len(grid[0])
    im = im.resize((width * 8, height * 8), Image.Resampling.NEAREST)

    for p in cursorPixels:
      im.putpixel((cursor[0]*8 + p[0], height*8 -(cursor[1]+1)*8 + p[1]), cursorColor)

  width, height = im.size
  if width < 1024 and height < 1024:
    im = im.resize((1024, 1024), Image.Resampling.NEAREST)
  
  byteObj = io.BytesIO()
  im.save(byteObj, 'PNG')
  return byteObj
  
async def draw(bot, *data):
  dataFs = immutify(data)
  if dataFs in cache:
    url = cache[dataFs]['Url']
  else:
    byteObj = await drawQueue.doTask(blocking, *data)
    url = await uploadQueue.upload(bot, byteObj)
    cache[dataFs] = {
      'Url' : url
    }
  return url