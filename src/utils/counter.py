"""
Modified version of ExpiringCache from R.Danny Bot.
- Min refresh interval, prevents unnecessary refreshing.
"""

import time
import asyncio

class ExpiringCounter(dict): 
  def __init__(self, seconds): 
    super().__init__() 
    self.time_to_live = seconds 
    self.min_interval = 30
    self.last_refresh = 0
    self.refresh_lock = asyncio.Lock()

  async def refresh(self): 
    now = time.monotonic()
    if self.last_refresh + self.min_interval > now:
      return
    async with self.refresh_lock:
      if self.last_refresh + self.min_interval > now:
        return # if others are waiting to access
      self.last_refresh = now
      for key, timestamp in tuple(self.items()):
        if now > timestamp + self.time_to_live:
          del self[key]
    
  async def update(self, key): 
    await self.refresh()
    super().__setitem__(key, time.monotonic()) 