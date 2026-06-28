"""
Car drawing - pure pygame, no image assets needed.
"""
import pygame
from game.constants import *


def draw_player_car(surface, x, y, color=BLUE, small=False):
    """Draw a stylised player car centred at (x, y)."""
    w = (PLAYER_WIDTH  - 8) if not small else (PLAYER_WIDTH  - 16)
    h = (PLAYER_HEIGHT - 4) if not small else (PLAYER_HEIGHT - 16)
    _draw_car(surface, x, y, w, h, color, is_player=True)


def draw_traffic_car(surface, x, y, car_type="sedan", small=False):
    type_colors = {
        "sedan":  (RED),
        "suv":    (ORANGE),
        "truck":  (PURPLE),
    }
    color = type_colors.get(car_type, RED)
    w = (TRAFFIC_WIDTH  - 8) if not small else (TRAFFIC_WIDTH  - 16)
    h = (TRAFFIC_HEIGHT - 4) if not small else (TRAFFIC_HEIGHT - 16)
    th = h + 10 if car_type == "truck" else h
    _draw_car(surface, x, y, w, th, color, is_player=False)


def _draw_car(surface, cx, cy, w, h, color, is_player):
    """Generic car body with windows and wheels."""
    x = cx - w // 2
    y = cy - h // 2

    # Body
    pygame.draw.rect(surface, color, (x, y, w, h), border_radius=8)

    # Windshield
    win_margin = 5
    win_h = h // 4
    win_y = y + (h // 8 if is_player else (h - win_h - h // 8))
    win_color = (160, 220, 255)
    pygame.draw.rect(surface, win_color,
                     (x + win_margin, win_y, w - win_margin * 2, win_h),
                     border_radius=4)

    # Rear window (opposite end)
    rear_y = (y + h - win_h - h // 8) if is_player else (y + h // 8)
    pygame.draw.rect(surface, (100, 160, 200),
                     (x + win_margin + 4, rear_y, w - win_margin * 2 - 8, win_h - 4),
                     border_radius=3)

    # Wheels
    wheel_w, wheel_h = 8, 16
    wheel_color = (20, 20, 20)
    rim_color   = (120, 120, 120)
    for wx, wy in [
        (x - 4,         y + h // 5),
        (x + w - 4,     y + h // 5),
        (x - 4,         y + h - h // 5 - wheel_h),
        (x + w - 4,     y + h - h // 5 - wheel_h),
    ]:
        pygame.draw.rect(surface, wheel_color, (wx, wy, wheel_w, wheel_h), border_radius=3)
        pygame.draw.rect(surface, rim_color,   (wx + 2, wy + 4, wheel_w - 4, wheel_h - 8))

    # Headlights / taillights
    light_y  = y + 4      if is_player else y + h - 8
    light_c  = YELLOW     if is_player else RED
    for lx in [x + 4, x + w - 10]:
        pygame.draw.rect(surface, light_c, (lx, light_y, 6, 4), border_radius=2)
