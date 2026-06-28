"""
Road rendering helpers.
"""
import pygame
from game.constants import *


class Road:
    """Scrolling road with lane markers."""

    def __init__(self, road_x, road_width, height, lane_count=3):
        self.road_x     = road_x
        self.road_width = road_width
        self.height     = height
        self.lane_count = lane_count
        self.lane_width = road_width // lane_count
        self.scroll_y   = 0.0

        # Pre-build dash positions
        self.dash_h    = 40
        self.dash_gap  = 30
        self.dash_period = self.dash_h + self.dash_gap

    def update(self, scroll_speed):
        self.scroll_y = (self.scroll_y + scroll_speed) % self.dash_period

    def draw(self, surface, offset_x=0):
        rx = self.road_x + offset_x

        # Grass either side
        pygame.draw.rect(surface, GRASS, (offset_x, 0, rx - offset_x, self.height))
        pygame.draw.rect(surface, GRASS, (rx + self.road_width, 0,
                                          surface.get_width() - rx - self.road_width,
                                          self.height))

        # Road surface
        pygame.draw.rect(surface, ASPHALT, (rx, 0, self.road_width, self.height))

        # Kerb lines
        pygame.draw.rect(surface, WHITE, (rx, 0, 4, self.height))
        pygame.draw.rect(surface, WHITE, (rx + self.road_width - 4, 0, 4, self.height))

        # Lane dashes
        for lane in range(1, self.lane_count):
            lx = rx + lane * self.lane_width - 2
            y = -self.dash_period + self.scroll_y
            while y < self.height:
                pygame.draw.rect(surface, ROAD_LINE, (lx, y, 4, self.dash_h))
                y += self.dash_period

    def lane_center_x(self, lane, offset_x=0):
        """Return pixel x-centre of given lane (0-indexed)."""
        return self.road_x + offset_x + lane * self.lane_width + self.lane_width // 2
