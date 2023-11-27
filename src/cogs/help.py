import discohook
from ..utils.constants import COLOR_GREEN

@discohook.command.slash('help', description = 'Guide to using the bot!')
async def help_command(interaction):
  embed = discohook.Embed(
    'r/Place Temp Help',
    description = '\n'.join([
      '<@970423357206061056> is a bot inspired by the subreddit [r/Place](https://reddit.com/r/place) where the site allowed any reddit user to place a pixel on a canvas every 5 minutes, and hovering over the pixel would say who placed it and what color. This bot recreates the experience on Discord as closely as possible, with a moving cursor and such.',
      '',
      'The commands are:',
      '- `/ping` - Ping test the bot.',
      '- `/help` - Learn how to use the bot.',
      '- `/canvas` - Interact with the GLOBAL canvas.',
      '- `/local-canvas` - Interact with the SERVER or DM canvas.',
      '',
      '`🚨` **IMPORTANT NOTE:** The global canvas is not moderated. If you do not want NSFW or Griefing then DO NOT USE `/canvas`, use `/local-canvas` instead. The developer is not responsible if someone overwrites all your precious art work.',
      '',
      'Above all, this bot is just for fun. Please enjoy it and share with friends to help it grow! :)',
      '',
      '🔗 [Invite](https://discord.com/api/oauth2/authorize?client_id=970423357206061056&permissions=0&scope=bot)',
      '🔗 [Support](https://discord.gg/BZHPGjKYRz)'
    ]),
    color = COLOR_GREEN
  )
  embed.set_thumbnail('https://cdn.discordapp.com/avatars/970423357206061056/16c2bb057a54a0ab358d1b36f15d169d.png')
  embed.set_footer('v{}'.format(interaction.client.version))
  await interaction.response.send(embed = embed)