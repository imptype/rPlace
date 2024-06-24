import io
import asyncio
import colorsys
import discohook
from collections import defaultdict
from PIL import Image
from ..utils.helpers import get_grid, draw_map, get_user_data, get_guild_data, revert_text
from ..utils.constants import COLOR_BLURPLE, COLOR_ORANGE, COLOR_RED, IMAGE_SIZE, CANVAS_SIZE

color_presets = {
  (255,   0,   0) : 'Red', # primary
  (0,   255,   0) : 'Green',
  (0,     0, 255) : 'Blue',
  (0,   255, 255) : 'Cyan', # secondary
  (255,   0, 255) : 'Magenta',
  (255, 255,   0) : 'Yellow',
  (255, 127,   0) : 'Orange', # tertiary
  (127, 255,   0) : 'Chartreuse',
  (0,   255, 127) : 'Aquamarine',
  (0,   127, 255) : 'Azure',
  (127,   0, 255) : 'Violet',
  (255,   0, 127) : 'Rose'
}
default_color = (0, 0, 0) # black

@discohook.command.slash('preview', description = 'Preview another server\'s canvas!',
  options = [
    discohook.Option.string(
      'server_id', 'The Server ID. Right-click the server to get the ID.',
      required = True,
      min_length = 17,
      max_length = 20
    ),
    discohook.Option.integer(
      'mode', 'The mode to use. Defaults to 1',
      choices = [
        discohook.Choice('1 Default - Shows canvas in regular view', 1),
        discohook.Choice('2 Black and White - Edited pixels are black', 2),
        discohook.Choice('3 Users - Shows all pixels placed by same user', 3)
        #discohook.Choice('3 Heatmap - Most common pixels are red', 2),
        #discohook.Choice('4 Heatmap Age - By age instead', 3),
        #discohook.Choice('5 Users - Shows all pixels placed by same user', 4),
        #discohook.Choice('6 Guilds - By same guild', 5)
      ]
    )
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
async def preview_command(interaction, server_id, mode = 1):
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

      embed = discohook.Embed(
      '{}\'s Canvas'.format(name),
        color = COLOR_BLURPLE
      )
      if icon:
        embed.set_thumbnail(icon)

      global_vars = {}
      def blocking():
        if mode == 1:
          im = draw_map(grid, configs)
        elif mode == 2:
          sconfigs = configs.copy() # flags that every placed pixel should be black
          sconfigs['bw'] = True
          im = draw_map(grid, sconfigs)
          embed.set_footer('Preview Mode: 2 - Black & White')
        elif mode == 3:
          user_pixels = defaultdict(int)
          for y in grid:
            if y < size[1]:
              for x in grid[y]:
                if int(x) < size[0] and ((not reset and len(grid[y][x]) == count) or grid[y][x][-1] == reset):
                  user_pixels[grid[y][x][3]] += 1

          global_vars['user_pixels'] = user_pixels = dict(sorted(user_pixels.items(), key = lambda x: x[1], reverse = True))
          user_colors = defaultdict(lambda: default_color) # black = default
          color_preset_keys = tuple(color_presets)
          for i, v in enumerate(user_pixels):
            user_colors[v] = color_preset_keys[i]
            if i == len(color_presets) - 1:
              break
          sconfigs = configs.copy()
          sconfigs['uc'] = global_vars['user_colors'] = user_colors
          im = draw_map(grid, sconfigs)
          embed.set_footer('Preview Mode: 3 - Users')

        else:
          raise ValueError('mode draw method not found', mode)
        factor = IMAGE_SIZE // max(size)
        resize = (size[0] * factor, size[1] * factor)
        if size != resize:
          im = im.resize(resize, Image.Resampling.NEAREST)
        buffer = io.BytesIO()
        im.save(buffer, 'PNG')
        return buffer

      buffer = await asyncio.to_thread(blocking)
      embed.set_image(discohook.File('map.png', content = buffer.getvalue()))

      get_pixels_filled = lambda count: '{:.2f}'.format((count / (size[0] * size[1])) * 100).rstrip('0').removesuffix('.')

      if mode in (1, 2):
        tile_count = sum(
          1
          for y in grid
          if y < size[1]
          for x in grid[y]
          if int(x) < size[0] and ((not reset and len(grid[y][x]) == count) or grid[y][x][-1] == reset)
        )

        description = 'Pixels filled: {}%'.format(get_pixels_filled(tile_count))
      elif mode == 3:
        user_pixels = global_vars['user_pixels']
        user_colors = global_vars['user_colors']
        description = 'Total unique users: {}'.format(len(user_pixels))

        parts = []
        other_count = 0
        other_places = 0
        for i, (k, v) in enumerate(user_pixels.items()):
          if (c := user_colors[k]) != default_color:
            parts.append('{}. <@{}>'.format(i + 1, revert_text(k)))
            parts.append('➔ {:,}x places or {}%'.format(v, get_pixels_filled(v)))
            parts.append('➔ `#{:02x}{:02x}{:02x}` ({})'.format(c[0], c[1], c[2], color_presets[c]))
          else:
            other_count += 1
            other_places += v
        if other_count:
          parts.append('Other ({}):'.format(other_count))
          parts.append('➔ {:,}x places or {}%'.format(other_places, get_pixels_filled(other_places)))
          c = default_color
          parts.append('➔ `#{:02x}{:02x}{:02x}` ({})'.format(c[0], c[1], c[2], 'Black'))
        description += '\n' + '\n'.join(parts)

      else:
        raise ValueError('mode not supported', mode)

      embed.description = '\n'.join([ # description set after drawing so we can reuse calculations
        'Canvas size: {}x{}'.format(*size),
        '',
        description
      ])

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