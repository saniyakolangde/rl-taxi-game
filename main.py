"""
RL Highway Driver - Main Entry Point
"""
import pygame
import sys
from game.menu import MenuScreen
from game.constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE

def main():
    pygame.init()
    pygame.font.init()
    
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    
    menu = MenuScreen(screen, clock)
    menu.run()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
