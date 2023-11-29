import io
import string
import asyncio
from operator import itemgetter
from collections import defaultdict
import discohook
from ..utils.helpers import get_grid, draw_map, is_local, revert_text, get_guild_data, get_user_data #, convert_text
from ..utils.constants import BOT_VERSION, CANVAS_SIZE, COLOR_BLURPLE
from . import start

@discohook.button.new('Back To Home', emoji = '⬅️', custom_id = 'back:v{}'.format(BOT_VERSION))
async def back_button(interaction):

  # parse last refresh timestamp on canvas
  refresh_at = int(interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])
  
  grid, new_refresh_at = await get_grid(interaction)

  skip_draw = refresh_at >= new_refresh_at # didnt do an update = dont update image
  
  refresh_data = grid, new_refresh_at, skip_draw
  await start.StartView(interaction).update(refresh_data)

# pagination is unused for now
"""@discohook.button.new(emoji = '1️⃣', custom_id = 'one:v{}'.format(BOT_VERSION))
async def one_button(interaction):
  await TopView(interaction).update(0)

@discohook.button.new(emoji = '2️⃣', custom_id = 'two:v{}'.format(BOT_VERSION))
async def two_button(interaction):
  await TopView(interaction).update(1)

@discohook.button.new(emoji = '3️⃣', custom_id = 'three:v{}'.format(BOT_VERSION))
async def three_button(interaction):
  await TopView(interaction).update(2)

@discohook.button.new(emoji = '4️⃣', custom_id = 'four:v{}'.format(BOT_VERSION))
async def four_button(interaction):
  await TopView(interaction).update(3)"""

class TopView(discohook.View):
  def __init__(self, interaction = None):
    super().__init__()
    if interaction:
      self.interaction = interaction
    else: # persistent
      # self.add_buttons(back_button, one_button, two_button, three_button, four_button)
      self.add_buttons(back_button)
  
  async def setup(self): # ainit

    """if not flag:
      text = 'one'
    elif flag == 1:
      text = 'two'
    elif flag == 2:
      text = 'three'
    elif flag == 3:
      text = 'four'
    else:
      raise ValueError('Unhandled TopView flag:', flag)"""

    is_local_check = is_local(self.interaction)
    if is_local_check: # /local-canvas
      if self.interaction.guild_id: # /local-canvas in guild
        flag = 1
      else: # /local-canvas in DMs
        flag = 0
    else: # /canvas
      if self.interaction.guild_id: # /canvas in guild
        flag = 2
      else: # /canvas in DMs
        flag = 1
    
    # get grid
    grid, new_refresh_at = await get_grid(self.interaction)
    
    # benchmarks 
    # 100 0.0007
    # 1k 0.002-0.003
    # 10k 0.02
    # 100k 0.5
    # 1mil 5 seconds
    """import time
    import random
    now = time.time()
    print('start', now)
    grid = {
      y : {
        str(x) : [random.randint(0, 0xffffff), 1701275921 + random.randint(0, 12341), random.randint(0, 414244), convert_text(str(random.randint(164487161250316289, 2004487161250316289)), string.digits), convert_text(str(random.randint(164487161250316289, 2004487161250316289)), string.digits)]
        for x in range(100)
      }
      for y in range(100)
    }
    print('grid', time.time() - now)"""
    
    # flatten grid so we can do operations on it :/
    n = 3 # how many of each to show
    guilds = defaultdict(int) # id : count, needs value sorting
    users = defaultdict(int) # id : count, needs value sorting
    colors = defaultdict(int)# color : count, needs value sorting
    locations = [] # up to 3
    oldest = [] # up to 3
    for y in grid:
      for x in grid[y]:
        if flag:
          if flag == 2: # [0 color, 1 timestamp, 2 count, 3 userid/None when local canvas, 4 guildid/None when local canvas or global canvas dms]
            guilds[grid[y][x][4]] += 1
          users[grid[y][x][3]] += 1
        colors[grid[y][x][0]] += 1
        if len(locations) != n:
          locations.append((int(x), y, grid[y][x][2]))
        elif grid[y][x][2] > locations[-1][2]: # bigger than smallest
          p = n - 1 # insert position
          for i, v in enumerate(locations[:-1]):
            if grid[y][x][2] > v[2]:
              p = i
              break
          locations.insert(p, (int(x), y, grid[y][x][2]))
          del locations[-1]
        if len(oldest) != n:
          oldest.append((int(x), y, grid[y][x][1]))
        elif grid[y][x][1] < oldest[-1][2]: # smaller than biggest
          p = n - 1 # insert position
          for i, v in enumerate(oldest[:-1]):
            if grid[y][x][1] < v[2]:
              p = i
              break
          oldest.insert(p, (int(x), y, grid[y][x][1]))
          del oldest[-1]
      
    guilds = {revert_text(k, string.digits) : v for i, (k, v) in enumerate(sorted(guilds.items(), key = itemgetter(1), reverse = True)) if i < n}
    users = {revert_text(k, string.digits) : v for i, (k, v) in enumerate(sorted(users.items(), key = itemgetter(1), reverse = True)) if i < n}
    colors = {k: v for i, (k, v) in enumerate(sorted(colors.items(), key = itemgetter(1), reverse = True)) if i < n}
    # print('end', time.time() - now)

    async def task(snowflake_id, count, flag = False): # false = guild, true = user
      coro = get_user_data if flag else get_guild_data
      return flag, snowflake_id, count, await coro(self.interaction, snowflake_id)

    tasks = [
      task(k, v)
      for k, v in guilds.items()
    ] + [
      task(k, v, True)
      for k, v in users.items()
    ]

    results = await asyncio.gather(*tasks) # do top user and guild fetches at the same time
    for inner_flag, snowflake_id, count, data in results:
      if inner_flag:
        table = users
      else:
        table = guilds
      table[snowflake_id] = (count, data)

    print(guilds, users, colors, locations, oldest, sep = '\n')

    def get_rank(i):
      if i == 0:
        return '🥇'
      elif i == 1:
        return '🥈'
      elif i == 2:
        return '🥉'
      else:
        raise ValueError('Unhandled TopView.get_rank flag', i)
    
    texts = []
    empty = 'No data is available yet.'
    if flag:
      if flag == 2:
        texts.append('**Top Guilds (Most Pixels Placed)**')
        if guilds:
          texts.append('\n'.join(
          '{} [{}](https://discord.com/servers/{}) - {:,}x or {}%'.format(
            get_rank(i),
            '`{}`'.format(guild_data[0]) if guild_data else '*`Unknown Server`*',
            guild_id,
            count, 
            round(count / CANVAS_SIZE, 2)
          ) for i, (guild_id, (count, guild_data)) in enumerate(guilds.items())
        ))
        else:
          texts.append(empty)
        texts.append('')

      texts.append('**Top Users (Most Pixels Placed)**')
      if users:
        texts.append('\n'.join(
          '{} [{}](https://discord.com/users/{}) - {:,}x or {}%'.format(
            get_rank(i),
            '`{}`'.format(user_data[0]) if user_data else '`*Unknown User*`',
            user_id,
            count, 
            round(count / CANVAS_SIZE, 2)
          ) for i, (user_id, (count, user_data)) in enumerate(users.items())
        ))
      else:
        texts.append(empty)
      texts.append('')
    
    texts.append('**Top Colors (Most Frequent Pixels)**')
    if colors:
      texts.append('\n'.join(
        '{} [`#{:06x}`](https://coolors.co/{:06x}) - {}x or {}%'.format(
          get_rank(i), k, k, v, round(v / CANVAS_SIZE, 2)
        ) for i, (k, v) in enumerate(colors.items())
      ))
    else:
      texts.append(empty)
    texts.append('')
    
    texts.append('**Most Popular Pixels (X, Y)**')
    if locations:
      texts.append('\n'.join(
        '{} `({}, {})` - {:,}x places'.format(
          get_rank(i), x, y, c
        ) for i, (x, y, c) in enumerate(locations)
      ))
    else:
      texts.append(empty)
    texts.append('')
    
    texts.append('**Oldest Pixels (X, Y)**')
    if oldest:
      texts.append('\n'.join(
        '{} `({}, {})` - <t:{}:R>'.format(
          get_rank(i), x, y, t
        ) for i, (x, y, t) in enumerate(oldest)
      ))
    else:
      texts.append(empty)
    texts.append('')

    self.embed = discohook.Embed(
      'r/Place Statistics',
      description = '\n'.join(texts),
      color = COLOR_BLURPLE
    )

    # draw new canvas if refresh has happened
    refresh_at = int(self.interaction.message.data['components'][0]['components'][0]['custom_id'].split(':')[-1])

    if refresh_at >= new_refresh_at: # didnt do an update, skip draw
      self.embed.set_thumbnail('attachment://map.png')
    else:

      def blocking():
        im = draw_map(grid, CANVAS_SIZE)
        buffer = io.BytesIO()
        im.save(buffer, 'PNG')
        return buffer

      # draw canvas
      buffer = await asyncio.to_thread(blocking)

      self.embed.set_thumbnail(discohook.File('map.png', content = buffer.getvalue()))
    
    dynamic_back_button = discohook.Button(
      back_button.label,
      emoji = back_button.emoji,
      custom_id = '{}:{}'.format(back_button.custom_id, new_refresh_at)
    )
    self.add_buttons(dynamic_back_button)
    
    """dynamic_one_button = discohook.Button(
      emoji = one_button.emoji,
      custom_id = one_button.custom_id + ':',
      disabled = not flag
    )
    
    dynamic_two_button = discohook.Button(
      emoji = two_button.emoji,
      custom_id = two_button.custom_id + ':',
      disabled = flag == 1
    )
    
    dynamic_three_button = discohook.Button(
      emoji = three_button.emoji,
      custom_id = three_button.custom_id + ':',
      disabled = flag == 2
    )
    
    dynamic_four_button = discohook.Button(
      emoji = four_button.emoji,
      custom_id = four_button.custom_id + ':',
      disabled = flag == 3
    )

    self.add_buttons(back_button, dynamic_one_button, dynamic_two_button, dynamic_three_button, dynamic_four_button)"""
  
  async def update(self):
    await self.setup()
    await self.interaction.response.update_message(embed = self.embed, view = self)