# =============================================================================
# level.py
# Defines the hardcoded level grid and all tile/object rendering logic.
# The Level class reads the grid and builds lists of tiles, hazards, gems,
# doors, and player spawn points that the rest of the game uses.
# =============================================================================

import pygame
from settings import (
    TILE_SIZE, COLOR_DARK_GRAY, COLOR_BG,
    COLOR_FIRE_POOL, COLOR_WATER_POOL, COLOR_GREEN_LAKE,
    COLOR_GEM_RED, COLOR_GEM_BLUE,
    COLOR_DOOR_RED, COLOR_DOOR_BLUE,
    COLOR_LEVEL_PINK, COLOR_LEVEL_YELLOW, COLOR_LEVEL_PURPLE, COLOR_LEVEL_BLOCK
)

# =============================================================================
# LEVEL GRID
# Each character maps to a tile or object (see key below).
# The grid is 20 columns wide x 15 rows tall = 800x600 at TILE_SIZE=40.
#
#   # = solid wall / platform
#   . = empty space
#   F = fire pool (kills Fireboy)      W = water pool (kills Watergirl)
#   G = green lake (kills both)
#   R = red gem (Fireboy collects)     B = blue gem (Watergirl collects)
#   1 = Fireboy spawn                  2 = Watergirl spawn
#   X = Fireboy exit door              Y = Watergirl exit door
# =============================================================================
LEVEL_GRID = [
    # col: 0         9        18
    "####################",  # 0  ceiling
    "#.R.....B......XZ..#",  # 1  corridor 1: gems, X=Fireboy door col14, Z=Watergirl door col15
    "#.............######",  # 2  right landing pad (cols14-19 solid so players can reach doors)
    "##############.....#",  # 3  PLATFORM 1: right notch cols14-18 (jump up from right)
    "#..................#",  # 4  corridor 2 row A
    "#.......L..........#",  # 5  corridor 2 row B  (lever col8)
    "#.....##############",  # 6  PLATFORM 2: left notch cols1-5 (jump up from left)
    "#..................#",  # 7  corridor 3 row A
    "#...........B..V...#",  # 8  corridor 3 row B  (blue gem col11, button col15)
    "##############.....#",  # 9  PLATFORM 3: right notch cols14-18
    "#..................#",  # 10 corridor 4 row A
    "#.R.......Y........#",  # 11 corridor 4 row B  (red gem col2, yellow platform col10)
    "#.....##############",  # 12 PLATFORM 4: left notch cols1-5 (players jump up here from bottom)
    "#12...F.....W.....B#",  # 13 spawns col1+2; fire col6; water col12; blue gem col18
    "####################",  # 14 floor
]

# =============================================================================
# Interactive Objects
# =============================================================================

class Lever:
    def __init__(self, x, y):
        # Lever is at the bottom of the tile
        self.rect = pygame.Rect(x, y + TILE_SIZE//2, TILE_SIZE, TILE_SIZE//2)
        self.state = False  # False = off, True = on

    def draw(self, screen):
        color = COLOR_LEVEL_YELLOW
        pygame.draw.rect(screen, color, self.rect)
        # Draw a simple toggle line
        start_x = self.rect.centerx
        start_y = self.rect.bottom
        end_x = self.rect.centerx + (15 if self.state else -15)
        end_y = self.rect.top - 5
        pygame.draw.line(screen, (255, 255, 255), (start_x, start_y), (end_x, end_y), 3)

class Button:
    def __init__(self, x, y):
        # Button is a small rectangular strip on the floor
        self.rect = pygame.Rect(x + 5, y + TILE_SIZE - 8, TILE_SIZE - 10, 8)
        self.is_pressed = False

    def draw(self, screen):
        color = COLOR_LEVEL_PINK
        h = 3 if self.is_pressed else 8
        r = pygame.Rect(self.rect.x, self.rect.bottom - h, self.rect.width, h)
        pygame.draw.rect(screen, color, r)

class MovingPlatform:
    def __init__(self, x, y, color):
        # Platform is 2 tiles wide
        self.rect = pygame.Rect(x, y, TILE_SIZE * 2, 10)
        self.start_y = y
        self.end_y = y - 100 # Moves up 100 pixels
        self.color = color
        self.is_active = False

    def update(self):
        target_y = self.end_y if self.is_active else self.start_y
        if abs(self.rect.y - target_y) > 2:
            if self.rect.y < target_y:
                self.rect.y += 2
            else:
                self.rect.y -= 2
        else:
            self.rect.y = target_y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class PushableBlock:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
        self.velocity_y = 0
        self.is_on_ground = False

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_LEVEL_BLOCK, self.rect)
        pygame.draw.rect(screen, (150, 150, 150), self.rect, 2)

    def update(self, gravity, tiles):
        self.velocity_y += gravity
        self.rect.y += int(self.velocity_y)
        self.is_on_ground = False
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = tile.rect.top
                    self.velocity_y = 0
                    self.is_on_ground = True
                elif self.velocity_y < 0:
                    self.rect.top = tile.rect.bottom
                    self.velocity_y = 0



# =============================================================================
# Tile — a single solid rectangular block the players can stand on/collide with
# =============================================================================
class Tile:
    def __init__(self, x_pixels, y_pixels):
        self.rect = pygame.Rect(x_pixels, y_pixels, TILE_SIZE, TILE_SIZE)

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_DARK_GRAY, self.rect)
        # Thin lighter border so individual tiles are visible
        pygame.draw.rect(screen, (80, 80, 80), self.rect, 1)


# =============================================================================
# HazardZone — a pool (fire / water / green) that can kill players on contact
# =============================================================================
class HazardZone:
    # Maps grid character -> (hazard type string, display color)
    HAZARD_MAP = {
        "F": ("fire",  COLOR_FIRE_POOL),
        "W": ("water", COLOR_WATER_POOL),
        "G": ("green", COLOR_GREEN_LAKE),
    }

    def __init__(self, x_pixels, y_pixels, grid_char):
        self.rect = pygame.Rect(x_pixels, y_pixels, TILE_SIZE, TILE_SIZE)
        self.hazard_type, self.color = self.HAZARD_MAP[grid_char]

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


# =============================================================================
# Gem — collectible item; red gems for Fireboy, blue gems for Watergirl
# =============================================================================
class Gem:
    GEM_RADIUS = 8  # Display size of the gem circle

    def __init__(self, x_pixels, y_pixels, gem_type):
        # gem_type is either "red" (Fireboy) or "blue" (Watergirl)
        self.gem_type = gem_type
        self.color    = COLOR_GEM_RED if gem_type == "red" else COLOR_GEM_BLUE
        # Center the gem within its tile cell
        center_x = x_pixels + TILE_SIZE // 2
        center_y = y_pixels + TILE_SIZE // 2
        self.rect      = pygame.Rect(0, 0, self.GEM_RADIUS * 2, self.GEM_RADIUS * 2)
        self.rect.center = (center_x, center_y)
        self.collected = False  # Flipped to True when a player picks it up

    def draw(self, screen):
        if not self.collected:
            pygame.draw.circle(screen, self.color, self.rect.center, self.GEM_RADIUS)


# =============================================================================
# ExitDoor — the goal tile each player must reach to win
# =============================================================================
class ExitDoor:
    def __init__(self, x_pixels, y_pixels, door_type):
        # door_type is "fireboy" or "watergirl"
        self.door_type  = door_type
        self.color      = COLOR_DOOR_RED if door_type == "fireboy" else COLOR_DOOR_BLUE
        self.rect       = pygame.Rect(x_pixels, y_pixels, TILE_SIZE, TILE_SIZE)
        self.is_open    = False  # Could be used later to animate the door

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        # Draw a small white arch shape to suggest a doorway
        inner = self.rect.inflate(-10, -4)
        pygame.draw.rect(screen, (255, 255, 255), inner, 2)


# =============================================================================
# Level — parses LEVEL_GRID and stores all game objects for the current level
# =============================================================================
class Level:
    def __init__(self):
        self.tiles               = []   # Solid platform/wall tiles
        self.hazard_zones        = []   # Fire, water, green lake zones
        self.gems                = []   # Collectible gems
        self.exit_doors          = []   # Fireboy and Watergirl exit doors
        self.levers              = []
        self.buttons             = []
        self.moving_platforms    = []
        self.blocks              = []
        self.fireboy_spawn       = (0, 0)  # Pixel position for Fireboy start
        self.watergirl_spawn     = (0, 0)  # Pixel position for Watergirl start
        self._parse_grid()

    # -------------------------------------------------------------------------
    # _parse_grid — walks every cell in LEVEL_GRID and creates the right object
    # -------------------------------------------------------------------------
    def _parse_grid(self):
        for row_index, row_string in enumerate(LEVEL_GRID):
            for col_index, cell_char in enumerate(row_string):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE

                if cell_char == "#":
                    self.tiles.append(Tile(x, y))

                elif cell_char in ("F", "W", "G"):
                    self.hazard_zones.append(HazardZone(x, y, cell_char))

                elif cell_char == "R":
                    self.gems.append(Gem(x, y, "red"))

                elif cell_char == "B":
                    self.gems.append(Gem(x, y, "blue"))

                elif cell_char == "X":
                    self.exit_doors.append(ExitDoor(x, y, "fireboy"))

                elif cell_char == "Z":
                    self.exit_doors.append(ExitDoor(x, y, "watergirl"))

                elif cell_char == "L":
                    self.levers.append(Lever(x, y))

                elif cell_char == "V":
                    self.buttons.append(Button(x, y))

                elif cell_char == "Y":
                    self.moving_platforms.append(MovingPlatform(x, y, COLOR_LEVEL_YELLOW))

                elif cell_char == "P":
                    self.moving_platforms.append(MovingPlatform(x, y, COLOR_LEVEL_PURPLE))

                elif cell_char == "S":
                    self.blocks.append(PushableBlock(x, y))

                elif cell_char == "1":
                    self.fireboy_spawn = (x, y)

                elif cell_char == "2":
                    self.watergirl_spawn = (x, y)

    # -------------------------------------------------------------------------
    # draw — renders every level object onto the screen each frame
    # -------------------------------------------------------------------------
    def draw(self, screen):
        # Background fill first
        screen.fill(COLOR_BG)

        for tile in self.tiles:
            tile.draw(screen)

        for hazard in self.hazard_zones:
            hazard.draw(screen)

        for gem in self.gems:
            gem.draw(screen)

        for door in self.exit_doors:
            door.draw(screen)