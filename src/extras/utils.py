def get_button_name(interaction):
  for row in interaction.payload['message']['components']:
    for component in row['components']:
      if component['custom_id'] == interaction.data['custom_id']:
        return component['emoji']['name']