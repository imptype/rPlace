import discohook
from ..utils.constants import COLOR_ORANGE, BOT_INVITE_URL, BOT_SUPPORT_URL, BOT_VOTE_URL, BOT_AVATAR_URL

invite_button = discohook.button.link('Invite', url = BOT_INVITE_URL, emoji = '♻️')
support_button = discohook.button.link('Support', url = BOT_SUPPORT_URL, emoji = '⛑️')
vote_button = discohook.button.link('Vote', url = BOT_VOTE_URL, emoji = '🏆')

@discohook.command.slash('help', description = 'Guide to using the bot!')
async def help_command(interaction):
  embed = discohook.Embed(
    '📜 r/Place Help & Information',
    description = '\n'.join([
      'This bot recreates the [r/Place subreddit](https://reddit.com/r/place) experience on Discord as closely as possible, with a moving cursor and such.',
      '',
      '**Commands [4]**',
      '> The prefix is [Slash Commands](https://support.discord.com/hc/en-us/articles/1500000368501-Slash-Commands-FAQ).',
      '> `/ping` - tests the bot\'s latency in milliseconds.',
      '> `/help` - shows the command list and bot information.',
      '> `/canvas` - interacts with the GLOBAL (server-wide) canvas.',
      '> `/local-canvas` - interacts with your SERVER or DM canvas.',
      '',
      '**IMPORTANT NOTE:** The global canvas is not moderated. If you do not want NSFW or griefing then use `/local-canvas` instead.',
      '',
      '**Bot Credits**',
      'This bot was built using the [discohook library](https://github.com/jnsougata/discohook) and [deta.space](https://deta.space)!',
      'Join the [support server]({}) if you have any questions or suggestions.'.format(BOT_SUPPORT_URL)
    ]),
    color = COLOR_ORANGE
  )
  embed.set_thumbnail(BOT_AVATAR_URL)
  embed.set_footer('Current Version: {}'.format(interaction.client.version))
  view = discohook.View()
  view.add_buttons(invite_button, support_button, vote_button)
  await interaction.response.send(embed = embed, view = view)