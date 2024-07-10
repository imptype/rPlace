"""
Contains constants, not secrets but things that might change.
"""

BOT_VERSION = '3.9.2'

# Bot stuff
BOT_AVATAR_URL = 'https://cdn.discordapp.com/avatars/970423357206061056/b99ed1acd81e8d3dfe745cc77e2ff2ac.png?size=1024'
BOT_INVITE_URL = 'https://discord.com/api/oauth2/authorize?scope=bot&client_id=970423357206061056'
BOT_SUPPORT_URL = 'https://discord.gg/BZHPGjKYRz'
BOT_VOTE_URL = 'https://top.gg/bot/970423357206061056/vote'

# Colors
COLOR_BLURPLE = 0x5865F2
COLOR_GREEN = 0x2ECC71
COLOR_ORANGE = 0xE67E22
COLOR_RED = 0xE74C3C
COLOR_BLUE = 0x3498DB

# Other
REFRESH_DEBOUNCE = 60 # for movement, delay refresh by 60 seconds, refresh always on place though
CANVAS_SIZE = (1000, 1000) # default, can be list but keeping as tuple
DEFAULT_SPAWN = '0_0' # (0, 0) at origin, can be changed to ?_? for random
IMAGE_SIZE = 1024 # size of map images in pixels
FETCH_DEBOUNCE = 5 # for force refresh, min seconds before fetching records from db again for same isntacen
PREMIUM_SKU_ID = 0