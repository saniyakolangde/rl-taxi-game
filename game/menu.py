"""
Main menu screen.
"""
import pygame
import sys
from game.constants import *
from game.modes.human_mode   import HumanMode
from game.modes.ai_mode      import AIMode
from game.modes.versus_mode  import VersusMode


class MenuScreen:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock
        self.font_title  = pygame.font.SysFont("consolas", FONT_TITLE,  bold=True)
        self.font_large  = pygame.font.SysFont("consolas", FONT_LARGE,  bold=True)
        self.font_medium = pygame.font.SysFont("consolas", FONT_MEDIUM)
        self.font_small  = pygame.font.SysFont("consolas", FONT_SMALL)
        self.selected = 0
        self.options  = ["1. Human", "2. AI (Watch / Train)", "3. Human vs AI"]
        self.scroll_y = 0.0
        self.bg_cars  = self._init_bg_cars()

    # ------------------------------------------------------------------

    def _init_bg_cars(self):
        import random
        cars = []
        for _ in range(8):
            cars.append({
                "x": random.randint(100, WINDOW_WIDTH - 100),
                "y": random.randint(0, WINDOW_HEIGHT),
                "speed": random.uniform(1.5, 3.5),
                "color": random.choice([RED, ORANGE, PURPLE, GREEN]),
            })
        return cars

    def _update_bg(self):
        self.scroll_y += 2
        for car in self.bg_cars:
            car["y"] += car["speed"]
            if car["y"] > WINDOW_HEIGHT + 100:
                car["y"] = -100

    def _draw_bg(self):
        self.screen.fill(ASPHALT)
        # Fake road stripes
        dash_h, dash_gap = 40, 30
        period = dash_h + dash_gap
        off = self.scroll_y % period
        for lx in [300, 600]:
            y = -period + off
            while y < WINDOW_HEIGHT:
                pygame.draw.rect(self.screen, ROAD_LINE, (lx - 2, y, 4, dash_h))
                y += period
        # Bg cars
        from game.cars import draw_traffic_car
        for car in self.bg_cars:
            draw_traffic_car(self.screen, car["x"], int(car["y"]), "sedan")

    # ------------------------------------------------------------------

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.selected = (self.selected - 1) % len(self.options)
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected = (self.selected + 1) % len(self.options)
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE,
                                     pygame.K_1, pygame.K_2, pygame.K_3):
                        if event.key == pygame.K_1:
                            self.selected = 0
                        elif event.key == pygame.K_2:
                            self.selected = 1
                        elif event.key == pygame.K_3:
                            self.selected = 2
                        self._launch(self.selected)

            self._update_bg()
            self._draw_bg()
            self._draw_ui()
            pygame.display.flip()

    def _draw_ui(self):
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT

        # Semi-transparent overlay
        overlay = pygame.Surface((500, 400), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (W // 2 - 250, H // 2 - 220))

        # Title
        title_surf = self.font_title.render("RL HIGHWAY", True, YELLOW)
        self.screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, H // 2 - 200))

        sub = self.font_small.render("Reinforcement Learning Demo", True, LIGHT_GRAY)
        self.screen.blit(sub, (W // 2 - sub.get_width() // 2, H // 2 - 130))

        # Divider
        pygame.draw.line(self.screen, YELLOW,
                         (W // 2 - 200, H // 2 - 110),
                         (W // 2 + 200, H // 2 - 110), 2)

        # Options
        for i, option in enumerate(self.options):
            color  = YELLOW if i == self.selected else WHITE
            prefix = "▶  " if i == self.selected else "   "
            surf   = self.font_large.render(prefix + option, True, color)
            self.screen.blit(surf, (W // 2 - surf.get_width() // 2,
                                    H // 2 - 70 + i * 70))

        # Footer
        footer = self.font_small.render("↑↓ Navigate   ENTER Select   ESC Quit",
                                        True, LIGHT_GRAY)
        self.screen.blit(footer, (W // 2 - footer.get_width() // 2, H - 40))

    def _launch(self, idx):
        if idx == 0:
            mode = HumanMode(self.screen, self.clock)
        elif idx == 1:
            mode = AIMode(self.screen, self.clock)
        else:
            mode = VersusMode(self.screen, self.clock)
        mode.run()
