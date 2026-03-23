# =============================================================================
# players.py
# Defines the base Player class and the Fireboy / Watergirl subclasses.
#
# Responsibilities:
#   - Store position, velocity, and alive/grounded state
#   - Handle horizontal movement and jumping
#   - Apply gravity each frame
#   - Resolve collisions with solid tiles
#   - Detect contact with hazard zones and gems
#   - Draw the player as a colored rectangle (functionality-first)
# =============================================================================

import pygame
from settings import (
    PLAYER_SPEED, JUMP_STRENGTH, GRAVITY, AIR_SPEED_MULTIPLIER,
    TILE_SIZE, COLOR_FIREBOY, COLOR_WATERGIRL,
    COLOR_WHITE
)


# =============================================================================
# Player — base class shared by Fireboy and Watergirl
# =============================================================================
class Player:
    WIDTH  = 28   # Player hitbox width  (slightly smaller than a tile)
    HEIGHT = 36   # Player hitbox height

    def __init__(self, x, y, color, fatal_hazard_types):
        # Position and size
        self.rect  = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.color = color

        # Velocity components (pixels per frame)
        self.velocity_x = 0
        self.velocity_y = 0

        # State flags
        self.is_on_ground = False   # True when standing on a solid tile
        self.is_alive     = True    # Flipped to False on hazard contact

        # Which hazard types instantly kill this player
        # e.g. Fireboy is killed by "water" and "green"
        self.fatal_hazard_types = fatal_hazard_types

        # Gems collected this run
        self.gems_collected = 0

    # -------------------------------------------------------------------------
    # move_left / move_right — set horizontal velocity for this frame
    # -------------------------------------------------------------------------
    def move_left(self):
        speed = PLAYER_SPEED * (AIR_SPEED_MULTIPLIER if not self.is_on_ground else 1.0)
        self.velocity_x = -speed

    def move_right(self):
        speed = PLAYER_SPEED * (AIR_SPEED_MULTIPLIER if not self.is_on_ground else 1.0)
        self.velocity_x = speed

    def stop_horizontal_movement(self):
        self.velocity_x = 0

    # -------------------------------------------------------------------------
    # jump — only allowed when the player is standing on solid ground
    # -------------------------------------------------------------------------
    def jump(self):
        if self.is_on_ground:
            self.velocity_y   = JUMP_STRENGTH
            self.is_on_ground = False

    # -------------------------------------------------------------------------
    # apply_gravity — pulls the player downward every frame
    # -------------------------------------------------------------------------
    def apply_gravity(self):
        self.velocity_y += GRAVITY

    # -------------------------------------------------------------------------
    # resolve_tile_collisions — move the player then push them out of any solid
    # tile they overlap with.  Horizontal and vertical axes are handled
    # separately so corner cases don't cause the player to stick to walls.
    # -------------------------------------------------------------------------
    def resolve_tile_collisions(self, tiles):
        # --- Horizontal pass ---
        self.rect.x += self.velocity_x
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.velocity_x > 0:           # Moving right — hit left face of tile
                    self.rect.right = tile.rect.left
                elif self.velocity_x < 0:         # Moving left  — hit right face of tile
                    self.rect.left  = tile.rect.right

        # --- Vertical pass ---
        self.rect.y      += int(self.velocity_y)
        self.is_on_ground = False                 # Reset; re-confirmed below if landing

        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.velocity_y > 0:           # Falling down — land on top of tile
                    self.rect.bottom  = tile.rect.top
                    self.velocity_y   = 0
                    self.is_on_ground = True
                elif self.velocity_y < 0:         # Moving up — hit underside of tile
                    self.rect.top   = tile.rect.bottom
                    self.velocity_y = 0

    # -------------------------------------------------------------------------
    # check_hazard_contact — returns True if the player is touching a hazard
    # that is fatal to them, and marks the player as no longer alive
    # -------------------------------------------------------------------------
    def check_hazard_contact(self, hazard_zones):
        for hazard in hazard_zones:
            if self.rect.colliderect(hazard.rect):
                if hazard.hazard_type in self.fatal_hazard_types:
                    self.is_alive = False
                    return True
        return False

    # -------------------------------------------------------------------------
    # check_gem_collection — collects any gem of the correct type on contact
    # -------------------------------------------------------------------------
    def check_gem_collection(self, gems, collectible_gem_type):
        for gem in gems:
            if not gem.collected and gem.gem_type == collectible_gem_type:
                if self.rect.colliderect(gem.rect):
                    gem.collected        = True
                    self.gems_collected += 1

    # -------------------------------------------------------------------------
    # check_reached_exit — returns True if player is overlapping their door
    # -------------------------------------------------------------------------
    def check_reached_exit(self, exit_doors, own_door_type):
        for door in exit_doors:
            if door.door_type == own_door_type:
                if self.rect.colliderect(door.rect):
                    return True
        return False

    # -------------------------------------------------------------------------
    # draw — renders the player as a solid rectangle with a face marker
    # -------------------------------------------------------------------------
    def draw(self, screen):
        # Body
        pygame.draw.rect(screen, self.color, self.rect)
        # Small white dot so you can tell which way the player is facing
        eye_x = self.rect.centerx
        eye_y = self.rect.top + 8
        pygame.draw.circle(screen, COLOR_WHITE, (eye_x, eye_y), 4)


# =============================================================================
# Fireboy — controlled with Arrow keys; dies in water and green lake
# =============================================================================
class Fireboy(Player):
    def __init__(self, x, y):
        super().__init__(
            x, y,
            color              = COLOR_FIREBOY,
            fatal_hazard_types = {"water", "green"}  # Fire is safe for Fireboy
        )

    # -------------------------------------------------------------------------
    # handle_input — reads arrow key state and updates movement / jump
    # -------------------------------------------------------------------------
    def handle_input(self, keys_pressed):
        self.stop_horizontal_movement()

        if keys_pressed[pygame.K_LEFT]:
            self.move_left()
        if keys_pressed[pygame.K_RIGHT]:
            self.move_right()
        if keys_pressed[pygame.K_UP]:
            self.jump()

    # -------------------------------------------------------------------------
    # collect_gems — Fireboy only picks up red gems
    # -------------------------------------------------------------------------
    def collect_gems(self, gems):
        self.check_gem_collection(gems, collectible_gem_type="red")

    # -------------------------------------------------------------------------
    # has_reached_exit — checks if Fireboy is at his red door
    # -------------------------------------------------------------------------
    def has_reached_exit(self, exit_doors):
        return self.check_reached_exit(exit_doors, own_door_type="fireboy")


# =============================================================================
# Watergirl — controlled with A/W/D keys; dies in fire and green lake
# =============================================================================
class Watergirl(Player):
    def __init__(self, x, y):
        super().__init__(
            x, y,
            color              = COLOR_WATERGIRL,
            fatal_hazard_types = {"fire", "green"}   # Water is safe for Watergirl
        )

    # -------------------------------------------------------------------------
    # handle_input — reads A / W / D key state and updates movement / jump
    # -------------------------------------------------------------------------
    def handle_input(self, keys_pressed):
        self.stop_horizontal_movement()

        if keys_pressed[pygame.K_a]:
            self.move_left()
        if keys_pressed[pygame.K_d]:
            self.move_right()
        if keys_pressed[pygame.K_w]:
            self.jump()

    # -------------------------------------------------------------------------
    # collect_gems — Watergirl only picks up blue gems
    # -------------------------------------------------------------------------
    def collect_gems(self, gems):
        self.check_gem_collection(gems, collectible_gem_type="blue")

    # -------------------------------------------------------------------------
    # has_reached_exit — checks if Watergirl is at her blue door
    # -------------------------------------------------------------------------
    def has_reached_exit(self, exit_doors):
        return self.check_reached_exit(exit_doors, own_door_type="watergirl")