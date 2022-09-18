"""
Test cog.
"""

import asyncio
import time
from discord.ext import commands
from ...utils.database import (
  getCell, 
  updateCell, 
  resetDatabase
)

class Test(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def start(self, ctx):

    questions = ['a', 'b', 'c', 'd']
    answers = ['1', '2', '3', '4']

    for i in range(len(questions)):
      try:
        await ctx.send(f"{questions[i]}")
        msg = await self.bot.wait_for(
            'message', 
            check = lambda message: message.author == ctx.author, 
            timeout = 20.0
          )
        while msg.content != answers[i]:
          await ctx.send(f"Try again: {questions[i]}")
          msg = await self.bot.wait_for(
            'message', 
            check = lambda message: message.author == ctx.author, 
            timeout = 20.0
          )   
      except asyncio.TimeoutError:
        await ctx.send("You took too long")
        return

  
    
  @commands.command()
  @commands.is_owner()
  async def get(self, ctx, x, y): 
    data = await getCell(x, y)
    print(data)
    await ctx.send(f'Data for cell ({x}, {y}): {data}')

  @commands.command()
  @commands.is_owner()
  async def update(self, ctx, x, y): 
    data = {"c" : 'ffbfbb'}
    data = await updateCell(x, y, data)
    await ctx.send(f'Updated cell ({x}, {y})')

  @commands.command()
  @commands.is_owner()
  async def reset(self, ctx): 
    await resetDatabase()
    await ctx.send('Reset database.')

def setup(bot):
  bot.add_cog(Test(bot))