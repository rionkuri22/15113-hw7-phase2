# =============================================================================
# main.py
# Entry point for Fireboy & Watergirl.
# Run this file to launch the game:  python main.py
# =============================================================================

from game import Game


def main():
    game = Game()
    game.run_game_loop()


if __name__ == "__main__":
    main()