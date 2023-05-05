"""
Contains custom buttons to do the following:
- converts emoji argument from str to PartialEmoji
- sets custom id after initialized if given for persistent buttons
- uses ButtonStyle.link when url is given
This contains a decorator too.
- no url argument, prefer using class instead
"""

import discohook

class CustomButton(discohook.Button):
  def __init__(self, label = None, emoji = None, custom_id = None, url = None, style = discohook.ButtonStyle.blurple, disabled = False):
    if emoji:
      if isinstance(emoji, str):
        emoji = discohook.PartialEmoji(emoji, None)
      else:
        emoji = discohook.PartialEmoji(*emoji) # name, id, anim:bool
    if url:
      style = discohook.ButtonStyle.link
    super().__init__(label = label, emoji = emoji, url = url, style = style, disabled = disabled)
    if custom_id:
      self.custom_id = custom_id

def custom_button(label = None, emoji = None, custom_id = None, style = discohook.ButtonStyle.blurple, disabled = False):
  def decorator(coro):
    btn = CustomButton(label = label, emoji = emoji, custom_id = custom_id, style = style, disabled = disabled)
    btn.on_interaction(coro)
    return btn
  return decorator