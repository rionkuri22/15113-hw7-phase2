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
    LEVEL_TIME_LIMIT
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
        self.fireboy.resolve_tile_collisions(self.level.tiles)
        self.watergirl.resolve_tile_collisions(self.level.tiles)

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
        fireboy_at_exit   = self.fireboy.has_reached_exit(self.level.exit_doors)
        watergirl_at_exit = self.watergirl.has_reached_exit(self.level.exit_doors)
        if fireboy_at_exit and watergirl_at_exit:
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