import io
import asyncio
import discohook
from PIL import Image
from ..utils.helpers import get_grid, draw_map, get_user_data, get_guild_data
from ..utils.constants import COLOR_BLURPLE, COLOR_ORANGE, COLOR_RED, IMAGE_SIZE, CANVAS_SIZE

@discohook.command.slash('preview', description = 'Preview another server\'s canvas!',
  options = [
    discohook.Option.string(
      'server_id', 'The Server ID. Right-click the server to get the ID.',
      required = True,
      min_length = 17,
      max_length = 20
    ),
  ],
  integration_types = [
    discohook.ApplicationIntegrationType.user,
    discohook.ApplicationIntegrationType.guild
  ],
  contexts = [
    discohook.InteractionContextType.guild,
    discohook.InteractionContextType.bot_dm,
    discohook.InteractionContextType.private_channel
  ]
)
async def preview_command(interaction, server_id):
  if not server_id.isdecimal():
    return await interaction.response.send('`{}` is not a server ID. Read https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID#h_01HRSTXPS5FSFA0VWMY2CKGZXA'.format(server_id))

  (grid, configs), defer_response, refresh_at = await get_grid(interaction, override_local_id = server_id)

  keys = set(grid.keys())
  keys.discard(0)

  if grid and (keys or grid[0]): # grid exists such that any other column exists apart from y 0
    
    share = configs.get('share') or 0

    if share:
      embed = discohook.Embed(
        'Canvas Is Private',
        description = 'The server ID by `{}` has set their canvas to private.'.format(server_id),
        color = COLOR_ORANGE
      )

    else:

      size = configs.get('size') or CANVAS_SIZE

      if keys and 0 in grid:
        i = iter(grid.values())
        next(i)
        tile = next(iter(next(i).values())) # avoid empty 0 row for config values
      else:
        tile = next(iter(next(iter(grid.values())).values()))

      if len(tile) > 3 and isinstance(tile[-1], int): # ignore reset values
        offset = 1
      else:
        offset = 0
      
      n = len(tile) - offset

      if n == 3:
        user_data = await get_user_data(interaction, server_id)
        if user_data:
          name, icon = user_data
        else:
          name, icon = 'Unknown User', None
      elif n == 4:
        guild_data = await get_guild_data(interaction, server_id)
        if guild_data:
          name, icon = guild_data
          icon = 'https://cdn.discordapp.com/icons/{}/{}.png'.format(server_id, icon) # icon hash
        else:
          name, icon = 'Unknown Server', None
      else:
        raise ValueError('unexpected tile count', tile)

      reset = configs.get('reset')
      count = configs.get('count')

      tile_count = sum(
        1
        for y in grid
        if y < size[1]
        for x in grid[y]
        if int(x) < size[0] and ((not reset and len(grid[y][x]) == count) or grid[y][x][-1] == reset)
      )
      
      embed = discohook.Embed(
      '{}\'s Canvas'.format(name),
        description = '\n'.join([
          'Canvas size: {}x{}'.format(*size),
          '',
          'Pixels filled: {}%'.format('{:.2f}'.format((tile_count / (size[0] * size[1])) * 100).rstrip('0').removesuffix('.'))
        ]),
        color = COLOR_BLURPLE
      )
      if icon:
        embed.set_thumbnail(icon)

      def blocking():
        im = draw_map(grid, configs)
        factor = IMAGE_SIZE // max(size)
        resize = (size[0] * factor, size[1] * factor)
        if size != resize:
          im = im.resize(resize, Image.Resampling.NEAREST)
        buffer = io.BytesIO()
        im.save(buffer, 'PNG')
        return buffer

      buffer = await asyncio.to_thread(blocking)
      embed.set_image(discohook.File('map.png', content = buffer.getvalue()))

  else:
    embed = discohook.Embed(
      'Canvas Not Found',
      description = 'The server ID `{}` is incorrect or the server has never used the bot before.'.format(server_id),
      color = COLOR_RED
    )

  if defer_response:
    await defer_response.edit(embed = embed)
  else:
    await interaction.response.send(embed = embed)