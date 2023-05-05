import discohook

@discohook.command('help', 'shows commands list and tutorial')
async def help_command(interaction):
  embed = discohook.Embed(
    title = 'r/Place Help',
    description = 'The only command available is `/canvas`, to interact with the 250x250 global canvas.',
    color = interaction.client.constants.COLOR_BLURPLE
  )
  embed.thumbnail(interaction.client.constants.BOT_AVATAR_URL)
  await interaction.response(embed = embed)