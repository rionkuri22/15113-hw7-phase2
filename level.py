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
    COLOR_DOOR_RED, COLOR_DOOR_BLUE
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
    "####################",  # row 0  — ceiling
    "#1.....R......B...2#",  # row 1  — top platform (spawns + gems)
    "###################.",  # row 2  — solid floor under row 1 (right gap)
    "#......#............",  # row 3  — mid-left platform
    "#.FFFF.#....WWWW...#",  # row 4  — fire pool left, water pool right
    "########.......####.",  # row 5  — floor with gap in middle
    "#...........R......#",  # row 6  — open area with gem
    "#.GGG.....GGGG.....#",  # row 7  — green lakes
    "#######.......######",  # row 8  — platform with gap
    "#....B.....R.......#",  # row 9  — gems on lower level
    "#.WWWW.....FFFF....#",  # row 10 — water left, fire right
    "########.......#####",  # row 11 — platform with gap
    "#X.................#",  # row 12 — Fireboy door on left
    "#.................Y#",  # row 13 — Watergirl door on right
    "####################",  # row 14 — floor
]


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

                elif cell_char == "Y":
                    self.exit_doors.append(ExitDoor(x, y, "watergirl"))

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