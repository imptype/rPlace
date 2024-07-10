import discohook
from ..utils.constants import COLOR_ORANGE, BOT_INVITE_URL, BOT_SUPPORT_URL, BOT_VOTE_URL, BOT_AVATAR_URL

invite_button = discohook.button.link('Invite', url = BOT_INVITE_URL, emoji = '♻️')
support_button = discohook.button.link('Support', url = BOT_SUPPORT_URL, emoji = '⛑️')
vote_button = discohook.button.link('Vote', url = BOT_VOTE_URL, emoji = '🏆')

@discohook.command.slash('help', description = 'Guide to using the bot!',
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
async def help_command(interaction):
  embed = discohook.Embed(
    '📜 Pixel Canvas Help & Information',
    description = '\n'.join([
      '**Pixel Canvas** lets you place pixels on a resizable canvas with others in real-time. You can draw pixel art or wage pixel wars! In other words, this bot recreates the [r/Place subreddit](https://reddit.com/r/place) experience on Discord as closely as possible, with a moving cursor and such.',
      '',
      '**Commands [5]**',
      '> The prefix is [Slash Commands](https://support.discord.com/hc/en-us/articles/1500000368501-Slash-Commands-FAQ).',
      '> `/ping` - tests the bot\'s latency in milliseconds.',
      '> `/help` - shows the command list and bot information.',
      '> `/canvas` - interacts with the GLOBAL (server-wide) canvas.',
      '> `/local-canvas` - interacts with your SERVER or DM canvas.',
      '> `/preview` - previews a canvascurl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok && ngrok http 8000 by ID with different modes.',
      '',
      '**IMPORTANT NOTE:** The global canvas is not moderated. If you do not want NSFW or griefing then use `/local-canvas` instead.',
      '',
      '**Bot Credits**',
      'This bot was built using the [discohook library](https://github.com/jnsougata/discohook "The library "discohook" is used to make asynchronous serverless Python Discord bots!"), [deta](https://deta.space "Deta Space hosts all our data, and can be used to host apps too!") & [Vercel](https://vercel.com "Vercel is a fast way to deploy serverless functions, which is the cheapest and most efficient hosting solution!")!',
      'Join the [support server]({}) if you have any questions or suggestions.'.format(BOT_SUPPORT_URL)
    ]),
    color = COLOR_ORANGE
  )
  embed.set_thumbnail(BOT_AVATAR_URL)
  embed.set_footer('Current Version: {}'.format(interaction.client.version))
  view = discohook.View()
  view.add_buttons(invite_button, support_button, vote_button)
  await interaction.response.send(embed = embed, view = view)