"""
Human play mode.
"""
import pygame
import sys
from game.constants import *
from game.session import GameSession


class HumanMode:
    def __init__(self, screen, clock):
        self.screen      = screen
        self.clock       = clock
        self.font_med    = pygame.font.SysFont("consolas", FONT_MEDIUM, bold=True)
        self.font_small  = pygame.font.SysFont("consolas", FONT_SMALL)
        self.font_large  = pygame.font.SysFont("consolas", FONT_LARGE, bold=True)

    def run(self):
        session = GameSession(
            road_x=ROAD_X,
            road_width=ROAD_WIDTH,
            height=WINDOW_HEIGHT,
        )
        countdown = self._do_countdown()
        if not countdown:
            return

        best = 0.0
        while True:
            self.clock.tick(FPS)

            action = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        action = 1
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        action = 2

            session.update(action)

            self.screen.fill(DARK_GRAY)
            session.draw(self.screen)
            self._draw_hud(session)
            pygame.display.flip()

            if not session.alive:
                best = max(best, session.score)
                if not self._game_over_screen(session.score, best):
                    return
                session = GameSession(
                    road_x=ROAD_X,
                    road_width=ROAD_WIDTH,
                    height=WINDOW_HEIGHT,
                )
                if not self._do_countdown():
                    return

    def _do_countdown(self):
        for i in range(3, 0, -1):
            for _ in range(FPS):
                self.clock.tick(FPS)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        return False
                self.screen.fill(DARK_GRAY)
                # Draw empty road
                road_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                road_surf.fill(DARK_GRAY)
                from game.road import Road
                r = Road(ROAD_X, ROAD_WIDTH, WINDOW_HEIGHT)
                r.draw(road_surf)
                self.screen.blit(road_surf, (0, 0))

                num = self.font_large.render(str(i), True, YELLOW)
                go  = self.font_small.render("Get ready!", True, WHITE)
                self.screen.blit(num, (WINDOW_WIDTH // 2 - num.get_width() // 2,
                                       WINDOW_HEIGHT // 2 - 50))
                self.screen.blit(go,  (WINDOW_WIDTH // 2 - go.get_width() // 2,
                                       WINDOW_HEIGHT // 2 + 20))
                pygame.display.flip()
        return True

    def _draw_hud(self, session):
        x, y = ROAD_X + ROAD_WIDTH + 20, 30
        labels = [
            ("TIME",  f"{session.score:.1f}s"),
            ("LEVEL", str(session.difficulty + 1)),
            ("SPEED", f"{session.scroll_speed:.1f}"),
        ]
        title = self.font_med.render("HUMAN", True, CYAN)
        self.screen.blit(title, (x, y)); y += 40
        pygame.draw.line(self.screen, CYAN, (x, y), (x + 120, y), 2); y += 10
        for label, val in labels:
            lsurf = self.font_small.render(label, True, LIGHT_GRAY)
            vsurf = self.font_med.render(val, True, WHITE)
            self.screen.blit(lsurf, (x, y));       y += 22
            self.screen.blit(vsurf, (x + 10, y));  y += 36

        # Controls reminder
        ctrl = self.font_small.render("← → to steer", True, GRAY)
        self.screen.blit(ctrl, (20, WINDOW_HEIGHT - 30))

    def _game_over_screen(self, score, best):
        for _ in range(FPS * 3):
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                        return True

            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            go   = self.font_large.render("GAME OVER", True, RED)
            sc   = self.font_med.render(f"Time: {score:.1f}s", True, WHITE)
            bs   = self.font_med.render(f"Best: {best:.1f}s",  True, YELLOW)
            hint = self.font_small.render("ENTER to restart   ESC for menu", True, LIGHT_GRAY)
            cx = WINDOW_WIDTH // 2
            self.screen.blit(go,   (cx - go.get_width()   // 2, 220))
            self.screen.blit(sc,   (cx - sc.get_width()   // 2, 310))
            self.screen.blit(bs,   (cx - bs.get_width()   // 2, 360))
            self.screen.blit(hint, (cx - hint.get_width() // 2, 430))
            pygame.display.flip()
        return True
