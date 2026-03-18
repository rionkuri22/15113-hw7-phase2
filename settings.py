"""
- screen width/height, frames per second, gravity constant
- color constants
- timer duration
- player speed and jump strength values
"""

# =============================================================================
# settings.py
# Central configuration for all game constants and tunable values.
# Adjust values here without touching any game logic files.
# =============================================================================

# --- Screen ---
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60
WINDOW_TITLE  = "Fireboy & Watergirl"

# --- Physics ---
GRAVITY       = 0.6    # Downward acceleration applied every frame
JUMP_STRENGTH = -13    # Negative = upward in Pygame's coordinate system
PLAYER_SPEED  = 4      # Horizontal movement speed (pixels per frame)

# --- Timer ---
LEVEL_TIME_LIMIT = 90  # Seconds allowed to complete the level

# --- Tile ---
TILE_SIZE = 40         # Width and height of each grid tile in pixels

# --- Colors (R, G, B) ---
COLOR_BLACK      = (0,   0,   0)
COLOR_WHITE      = (255, 255, 255)
COLOR_DARK_GRAY  = (50,  50,  50)   # Wall / platform tiles
COLOR_BG         = (30,  30,  45)   # Background fill

COLOR_FIREBOY    = (220, 60,  20)   # Fireboy body
COLOR_WATERGIRL  = (30,  120, 220)  # Watergirl body

COLOR_FIRE_POOL  = (200, 80,  0)    # Fatal fire hazard
COLOR_WATER_POOL = (0,   100, 200)  # Fatal water hazard
COLOR_GREEN_LAKE = (0,   160, 60)   # Fatal green-lake (kills both)

COLOR_GEM_RED    = (255, 50,  50)   # Fireboy collectible gem
COLOR_GEM_BLUE   = (50,  50,  255)  # Watergirl collectible gem

COLOR_DOOR_RED   = (180, 30,  30)   # Fireboy exit door
COLOR_DOOR_BLUE  = (30,  30,  180)  # Watergirl exit door

COLOR_TIMER_OK   = (255, 255, 255)  # Timer text — plenty of time
COLOR_TIMER_WARN = (255, 80,  80)   # Timer text — under 10 seconds