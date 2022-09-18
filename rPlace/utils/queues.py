"""
Queues/waitlists for things that can "break", or for more efficiency like caching pygame images, effective when the bot gets very large, contains:
- UploadQueue   ; for discord channels designated to upload to discord
- DrawQueue     ; ensures Pillow is only drawing one image at a time
- DatabaseQueue ; execute/fetch data in database, adhering to max connections limits
"""

import asyncio
import asyncpg
import discord
import os
from .functions import getchChannel

class UploadQueue:
  def __init__(self):
    self.channel = os.getenv('CDN_CHANNEL')

  async def upload(self, bot, byteObj):
    channel = await getchChannel(bot, self.channel)
    byteObj.seek(0)
    message = await channel.send(file = discord.File(fp = byteObj, filename = 'Map.png'))
    return message.attachments[0].url

class DrawQueue:
  def __init__(self):
    self.lock = asyncio.Lock()
    self.loop = asyncio.get_event_loop()
  
  async def doTask(self, func, *data):
    async with self.lock:
      byteObj = await self.loop.run_in_executor(None, func, *data)
      return byteObj


class DatabaseQueue:
  def __init__(self):
    self.pool = asyncio.get_event_loop().run_until_complete(
      asyncpg.create_pool(
        dsn = os.getenv('DATABASE_URL'),
        max_size = 20
      )
    )

  async def execute(self, sql, fetch = False):
    print(sql)
    async with self.pool.acquire() as con:
      if fetch:
        res = await con.fetch(sql)
      else:
        res = await con.execute(sql)
      return res