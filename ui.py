# =============================================================================
# ui.py
# Handles all on-screen text and overlay screens:
#   - Timer display (top center of screen)
#   - Main menu screen
#   - Game over screen  (shown on death or timeout)
#   - Win screen        (shown when both players reach their exits)
#
# All draw functions receive the screen surface and any data they need.
# Nothing in this file modifies game state — it only reads and displays.
# =============================================================================

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BLACK, COLOR_WHITE,
    COLOR_FIREBOY, COLOR_WATERGIRL,
    COLOR_TIMER_OK, COLOR_TIMER_WARN,
    COLOR_BG
)


# =============================================================================
# UIFonts — loads and stores all fonts used across the UI in one place
# =============================================================================
class UIFonts:
    def __init__(self):
        pygame.font.init()
        self.large  = pygame.font.SysFont("Arial", 64, bold=True)
        self.medium = pygame.font.SysFont("Arial", 36, bold=True)
        self.small  = pygame.font.SysFont("Arial", 24)
        self.timer  = pygame.font.SysFont("Courier New", 32, bold=True)


# =============================================================================
# draw_timer — renders the countdown clock at the top center of the screen.
# Turns red when under 10 seconds to warn the players.
# =============================================================================
def draw_timer(screen, fonts, seconds_remaining):
    # Format as MM:SS  e.g. 01:30
    minutes = int(seconds_remaining) // 60
    seconds = int(seconds_remaining) % 60
    time_string = f"{minutes:02}:{seconds:02}"

    # Warn the player when time is almost up
    color = COLOR_TIMER_WARN if seconds_remaining < 10 else COLOR_TIMER_OK

    timer_surface = fonts.timer.render(time_string, True, color)
    # Center horizontally, near the top
    x = SCREEN_WIDTH  // 2 - timer_surface.get_width()  // 2
    y = 8
    screen.blit(timer_surface, (x, y))


# =============================================================================
# draw_gem_counts — renders each player's gem tally below the timer
# =============================================================================
def draw_gem_counts(screen, fonts, fireboy_gems, watergirl_gems):
    # Fireboy gem count — left side
    fb_text = fonts.small.render(f"🔴 x{fireboy_gems}", True, COLOR_FIREBOY)
    screen.blit(fb_text, (16, 8))

    # Watergirl gem count — right side
    wg_text = fonts.small.render(f"🔵 x{watergirl_gems}", True, COLOR_WATERGIRL)
    screen.blit(wg_text, (SCREEN_WIDTH - wg_text.get_width() - 16, 8))


# =============================================================================
# draw_main_menu — full-screen main menu with title and start prompt
# =============================================================================
def draw_main_menu(screen, fonts):
    screen.fill(COLOR_BG)

    # Title
    title = fonts.large.render("FIREBOY & WATERGIRL", True, COLOR_WHITE)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 160))

    # Subtitle characters
    fb_label = fonts.medium.render("🔥 Fireboy", True, COLOR_FIREBOY)
    wg_label = fonts.medium.render("💧 Watergirl", True, COLOR_WATERGIRL)
    screen.blit(fb_label, (SCREEN_WIDTH // 2 - fb_label.get_width() // 2 - 120, 260))
    screen.blit(wg_label, (SCREEN_WIDTH // 2 - wg_label.get_width() // 2 + 120, 260))

    # Controls reminder
    controls = [
        "Fireboy  → Arrow Keys  ( ← ↑ → )",
        "Watergirl → A / W / D",
        "Avoid the wrong elements!",
    ]
    for i, line in enumerate(controls):
        text = fonts.small.render(line, True, COLOR_WHITE)
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 340 + i * 32))

    # Blinking prompt — visible every other half-second
    if (pygame.time.get_ticks() // 500) % 2 == 0:
        prompt = fonts.medium.render("Press SPACE to Start", True, COLOR_WHITE)
        screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 460))


# =============================================================================
# draw_game_over_screen — shown immediately when a player dies or time runs out
# reason: "fire" | "water" | "green" | "timeout"
# =============================================================================
def draw_game_over_screen(screen, fonts, reason):
    # Semi-transparent dark overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    # Main "GAME OVER" heading
    heading = fonts.large.render("GAME OVER", True, (220, 50, 50))
    screen.blit(heading, (SCREEN_WIDTH // 2 - heading.get_width() // 2, 180))

    # Reason message
    reason_messages = {
        "water":   "Fireboy fell in the water!",
        "fire":    "Watergirl got burned!",
        "green":   "Someone touched the green lake!",
        "timeout": "Time ran out!",
    }
    message = reason_messages.get(reason, "Better luck next time!")
    msg_surface = fonts.medium.render(message, True, COLOR_WHITE)
    screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, 270))

    # Restart prompt
    prompt = fonts.small.render("Press R to Restart  |  Press M for Menu", True, COLOR_WHITE)
    screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 360))


# =============================================================================
# draw_win_screen — shown when both players reach their exit doors
# =============================================================================
def draw_win_screen(screen, fonts, fireboy_gems, watergirl_gems):
    # Semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    # Heading
    heading = fonts.large.render("Cleared Level 1!", True, (255, 215, 0))  # Gold
    screen.blit(heading, (SCREEN_WIDTH // 2 - heading.get_width() // 2, 160))

    # Gem totals
    fb_score = fonts.medium.render(f"Fireboy gems:   {fireboy_gems}", True, COLOR_FIREBOY)
    wg_score = fonts.medium.render(f"Watergirl gems: {watergirl_gems}", True, COLOR_WATERGIRL)
    screen.blit(fb_score, (SCREEN_WIDTH // 2 - fb_score.get_width() // 2, 270))
    screen.blit(wg_score, (SCREEN_WIDTH // 2 - wg_score.get_width() // 2, 320))

    # Prompt
    prompt = fonts.small.render("Press R to Play Again  |  Press M for Menu", True, COLOR_WHITE)
    screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 420))