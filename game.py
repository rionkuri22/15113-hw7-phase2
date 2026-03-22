# =============================================================================
# game.py
# The central Game class that owns the main loop and coordinates all systems:
#   - Screen / clock setup
#   - Game state machine  (MENU → PLAYING → GAME_OVER / WIN)
#   - Per-frame input, physics, collision, and rendering
# =============================================================================

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WINDOW_TITLE,
    LEVEL_TIME_LIMIT, GRAVITY,
    COLOR_LEVEL_YELLOW, COLOR_LEVEL_PURPLE
)
from level   import Level
from players import Fireboy, Watergirl
from ui      import UIFonts, draw_timer, draw_gem_counts, \
                    draw_main_menu, draw_game_over_screen, draw_win_screen


# =============================================================================
# GameState — simple constants used to track which screen is active
# =============================================================================
class GameState:
    MENU      = "menu"
    PLAYING   = "playing"
    GAME_OVER = "game_over"
    WIN       = "win"


# =============================================================================
# Game — owns the window, clock, and all game objects; runs the main loop
# =============================================================================
class Game:
    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock   = pygame.time.Clock()
        self.fonts   = UIFonts()
        self.running = True

        # Start on the main menu
        self.state = GameState.MENU

        # These are initialised properly in initialize_level()
        self.level           = None
        self.fireboy         = None
        self.watergirl       = None
        self.time_remaining  = LEVEL_TIME_LIMIT
        self.game_over_reason = ""   # Passed to the game-over screen

    # -------------------------------------------------------------------------
    # initialize_level — (re)builds the level and spawns both players.
    # Called at the start of a new game and when the player restarts.
    # -------------------------------------------------------------------------
    def initialize_level(self):
        self.level          = Level()
        self.fireboy        = Fireboy(*self.level.fireboy_spawn)
        self.watergirl      = Watergirl(*self.level.watergirl_spawn)
        self.time_remaining = LEVEL_TIME_LIMIT
        self.game_over_reason = ""
        self.last_lever_touch = {}

    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    def run_game_loop(self):
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000.0  # Seconds since last frame

            self.handle_global_events()

            if self.state == GameState.MENU:
                self.update_menu()
                self.render_menu()

            elif self.state == GameState.PLAYING:
                self.update_playing(delta_time)
                self.render_playing()

            elif self.state == GameState.GAME_OVER:
                self.render_game_over()
                self.handle_post_game_input()

            elif self.state == GameState.WIN:
                self.render_win()
                self.handle_post_game_input()

            pygame.display.flip()

        pygame.quit()

    # =========================================================================
    # EVENT HANDLING
    # =========================================================================

    # -------------------------------------------------------------------------
    # handle_global_events — processes quit and universal key events every frame
    # -------------------------------------------------------------------------
    def handle_global_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    # -------------------------------------------------------------------------
    # handle_post_game_input — R = restart, M = back to menu
    # Called every frame while on GAME_OVER or WIN screens
    # -------------------------------------------------------------------------
    def handle_post_game_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            self.initialize_level()
            self.state = GameState.PLAYING
        elif keys[pygame.K_m]:
            self.state = GameState.MENU

    # =========================================================================
    # MENU STATE
    # =========================================================================

    # -------------------------------------------------------------------------
    # update_menu — waits for SPACE to start the game
    # -------------------------------------------------------------------------
    def update_menu(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.initialize_level()
            self.state = GameState.PLAYING

    def render_menu(self):
        draw_main_menu(self.screen, self.fonts)

    # =========================================================================
    # PLAYING STATE — update
    # =========================================================================

    # -------------------------------------------------------------------------
    # update_playing — runs every frame while the game is active:
    #   1. Count down the timer
    #   2. Read player input
    #   3. Apply gravity
    #   4. Resolve tile collisions
    #   5. Check hazard contact
    #   6. Check gem collection
    #   7. Check win condition
    # -------------------------------------------------------------------------
    def update_playing(self, delta_time):
        self.tick_timer(delta_time)
        self.handle_player_input()
        self.apply_gravity_to_players()
        self.handle_interactive_objects()
        self.resolve_player_collisions()
        self.check_player_hazards()
        self.check_gem_collection()
        self.check_win_condition()

    # -------------------------------------------------------------------------
    # tick_timer — decrements the countdown; triggers game over at zero
    # -------------------------------------------------------------------------
    def tick_timer(self, delta_time):
        self.time_remaining -= delta_time
        if self.time_remaining <= 0:
            self.time_remaining   = 0
            self.game_over_reason = "timeout"
            self.state            = GameState.GAME_OVER

    # -------------------------------------------------------------------------
    # handle_player_input — passes current key state to each player
    # -------------------------------------------------------------------------
    def handle_player_input(self):
        keys = pygame.key.get_pressed()
        self.fireboy.handle_input(keys)
        self.watergirl.handle_input(keys)

    # -------------------------------------------------------------------------
    # apply_gravity_to_players — pulls both players down each frame
    # -------------------------------------------------------------------------
    def apply_gravity_to_players(self):
        self.fireboy.apply_gravity()
        self.watergirl.apply_gravity()

    # -------------------------------------------------------------------------
    # resolve_player_collisions — pushes players out of solid tiles
    # -------------------------------------------------------------------------
    def resolve_player_collisions(self):
        # Merge tiles and moving platforms for collision
        collision_tiles = self.level.tiles + self.level.moving_platforms + self.level.blocks
        self.fireboy.resolve_tile_collisions(collision_tiles)
        self.watergirl.resolve_tile_collisions(collision_tiles)

    def handle_interactive_objects(self):
        # Update blocks
        for block in self.level.blocks:
            block.update(GRAVITY, self.level.tiles)
            # Players can push blocks
            if self.fireboy.rect.colliderect(block.rect):
                if self.fireboy.velocity_x > 0:
                    block.rect.left = self.fireboy.rect.right
                elif self.fireboy.velocity_x < 0:
                    block.rect.right = self.fireboy.rect.left
            if self.watergirl.rect.colliderect(block.rect):
                if self.watergirl.velocity_x > 0:
                    block.rect.left = self.watergirl.rect.right
                elif self.watergirl.velocity_x < 0:
                    block.rect.right = self.watergirl.rect.left

        # Update buttons
        for button in self.level.buttons:
            button.is_pressed = self.fireboy.rect.colliderect(button.rect) or \
                               self.watergirl.rect.colliderect(button.rect)
            for block in self.level.blocks:
                if block.rect.colliderect(button.rect):
                    button.is_pressed = True

        # Update levers (simple toggle on contact)
        for i, lever in enumerate(self.level.levers):
            is_touching = self.fireboy.rect.colliderect(lever.rect) or self.watergirl.rect.colliderect(lever.rect)
            if is_touching and not self.last_lever_touch.get(i, False):
                lever.state = not lever.state
            self.last_lever_touch[i] = is_touching

        # Update platforms
        for platform in self.level.moving_platforms:
            if platform.color == COLOR_LEVEL_YELLOW:
                # In our Level 1, we only have one lever
                platform.is_active = any(l.state for l in self.level.levers)
            elif platform.color == COLOR_LEVEL_PURPLE:
                platform.is_active = any(b.is_pressed for b in self.level.buttons)
            platform.update()

    # -------------------------------------------------------------------------
    # check_player_hazards — ends the game if either player touches a fatal zone
    # -------------------------------------------------------------------------
    def check_player_hazards(self):
        # Check Fireboy
        for hazard in self.level.hazard_zones:
            if self.fireboy.rect.colliderect(hazard.rect):
                if hazard.hazard_type in self.fireboy.fatal_hazard_types:
                    self.game_over_reason = hazard.hazard_type
                    self.state            = GameState.GAME_OVER
                    return

        # Check Watergirl
        for hazard in self.level.hazard_zones:
            if self.watergirl.rect.colliderect(hazard.rect):
                if hazard.hazard_type in self.watergirl.fatal_hazard_types:
                    self.game_over_reason = hazard.hazard_type
                    self.state            = GameState.GAME_OVER
                    return

    # -------------------------------------------------------------------------
    # check_gem_collection — lets each player collect their own gem type
    # -------------------------------------------------------------------------
    def check_gem_collection(self):
        self.fireboy.collect_gems(self.level.gems)
        self.watergirl.collect_gems(self.level.gems)

    # -------------------------------------------------------------------------
    # check_win_condition — both players must reach their own exit door to win
    # -------------------------------------------------------------------------
    def check_win_condition(self):
        # Light up doors when correct player is nearby
        fireboy_at_exit = False
        watergirl_at_exit = False
        for door in self.level.exit_doors:
            if door.door_type == "fireboy":
                door.is_lit = self.fireboy.rect.colliderect(door.rect)
                if door.is_lit:
                    fireboy_at_exit = True
            elif door.door_type == "watergirl":
                door.is_lit = self.watergirl.rect.colliderect(door.rect)
                if door.is_lit:
                    watergirl_at_exit = True
        # Both must be at their doors simultaneously
        if fireboy_at_exit and watergirl_at_exit:
            for door in self.level.exit_doors:
                door.is_open = True
            self.state = GameState.WIN

    # =========================================================================
    # PLAYING STATE — render
    # =========================================================================

    # -------------------------------------------------------------------------
    # render_playing — draws the level, players, timer, and gem counts
    # -------------------------------------------------------------------------
    def render_playing(self):
        # Level draws the background + all tiles/hazards/gems/doors
        self.level.draw(self.screen)

        # Draw both players on top
        self.fireboy.draw(self.screen)
        self.watergirl.draw(self.screen)

        # HUD — timer and gem counters
        draw_timer(self.screen, self.fonts, self.time_remaining)
        draw_gem_counts(
            self.screen, self.fonts,
            self.fireboy.gems_collected,
            self.watergirl.gems_collected
        )

    # =========================================================================
    # GAME OVER / WIN — render
    # =========================================================================

    def render_game_over(self):
        # Keep the level visible behind the overlay
        self.render_playing()
        draw_game_over_screen(self.screen, self.fonts, self.game_over_reason)

    def render_win(self):
        self.render_playing()
        draw_win_screen(
            self.screen, self.fonts,
            self.fireboy.gems_collected,
            self.watergirl.gems_collected
        )