"""
Game Constants
"""

# Window
TITLE = "RL Highway Driver"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
FPS = 60

# Colors
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
GRAY        = (80, 80, 80)
DARK_GRAY   = (40, 40, 40)
LIGHT_GRAY  = (160, 160, 160)
YELLOW      = (255, 220, 0)
RED         = (220, 50, 50)
GREEN       = (50, 200, 80)
BLUE        = (60, 120, 220)
ORANGE      = (230, 140, 40)
CYAN        = (60, 200, 220)
PURPLE      = (160, 80, 220)
DARK_GREEN  = (20, 120, 40)
ASPHALT     = (50, 52, 55)
ROAD_LINE   = (200, 200, 0)
GRASS       = (34, 85, 34)

# Single-screen road layout
ROAD_X      = 150
ROAD_WIDTH  = 600
LANE_COUNT  = 3
LANE_WIDTH  = ROAD_WIDTH // LANE_COUNT

# Split-screen road layout
SPLIT_ROAD_X     = 30
SPLIT_ROAD_WIDTH = 380
SPLIT_LANE_WIDTH = SPLIT_ROAD_WIDTH // LANE_COUNT

# Player
PLAYER_WIDTH  = 44
PLAYER_HEIGHT = 80
PLAYER_Y_FRAC = 0.80   # fraction from top of screen

# Traffic
TRAFFIC_WIDTH  = 44
TRAFFIC_HEIGHT = 80

# RL
STATE_ROWS  = 5
STATE_LANES = 3
CELL_HEIGHT = 100   # pixels per grid row

# Speeds
BASE_SCROLL_SPEED = 4.0
MAX_SCROLL_SPEED  = 14.0

# Difficulty ramp: speed increases every N seconds
DIFFICULTY_INTERVAL = 15   # seconds
SPEED_INCREMENT      = 0.6

# Fonts (loaded lazily in each module)
FONT_SMALL  = 18
FONT_MEDIUM = 26
FONT_LARGE  = 48
FONT_TITLE  = 72
