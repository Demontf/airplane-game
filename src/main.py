import os
import sys
import pygame
import configparser
from core.game import Game

def main():
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()

    # Load configuration
    config = configparser.ConfigParser()
    config.read('src/config/config.ini')

    # Create game instance
    game = Game(config)
    
    try:
        # Run game
        game.run()
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Clean up
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()