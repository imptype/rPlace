import discohook
from ..classes import custom_button

# [UPLEFT  ] [UP   ] [UPRIGHT  ] [COLOR: #FF0000]
# [LEFT    ] [PLACE] [RIGHT    ] [CHANGE COLOR  ]
# [DOWNLEFT] [DOWN ] [DOWNRIGHT] [JUMP TO (X, Y)]
# [ STEP SIZE SELECT ]
# [ ZOOM SIZE SELECT ]

@custom_button(emoji = '↖️')
async def upleft_button(interaction):
  pass

@custom_button(emoji = '⬆️')
async def up_button(interaction):
  pass

@custom_button(emoji = '↗️')
async def upright_button(interaction):
  pass

@custom_button(emoji = '↖️')
async def left_button(interaction):
  pass

@custom_button(emoji = '🟦')
async def place_button(interaction):
  pass

@custom_button(emoji = '➡️')
async def right_button(interaction):
  pass

@custom_button(emoji = '↙️')
async def downleft_button(interaction):
  pass

@custom_button(emoji = '⬇️')
async def down_button(interaction):
  pass

@custom_button(emoji = '↘️')
async def downright_button(interaction):
  pass


explore_view = discohook.View() # this holds left, right, up, down, place, step size select,
explore_view.add_button_row(upleft_button, up_button, upright_button)
explore_view.add_button_row(left_button, place_button, right_button)
explore_view.add_button_row(downleft_button, down_button, downright_button)