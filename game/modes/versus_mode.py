"""
Human vs AI split-screen mode.
Identical traffic via shared seed.
"""
import pygame
import sys
import random
from game.constants import *
from game.session import GameSession
from rl.agent import DQNAgent


class VersusMode:
    def __init__(self, screen, clock):
        self.screen     = screen
        self.clock      = clock
        self.font_med   = pygame.font.SysFont("consolas", FONT_MEDIUM, bold=True)
        self.font_small = pygame.font.SysFont("consolas", FONT_SMALL)
        self.font_large = pygame.font.SysFont("consolas", FONT_LARGE, bold=True)
        self.font_tiny  = pygame.font.SysFont("consolas", 14)

        # Layout
        self.half_w   = WINDOW_WIDTH // 2
        self.road_w   = SPLIT_ROAD_WIDTH
        self.road_x   = SPLIT_ROAD_X
        self.lane_w   = self.road_w // LANE_COUNT

    def run(self):
        seed    = random.randint(0, 2**31)
        rng_h   = random.Random(seed)
        rng_ai  = random.Random(seed)

        human_sess = GameSession(
            road_x=self.road_x,
            road_width=self.road_w,
            height=WINDOW_HEIGHT,
            rng=rng_h,
            small_cars=True,
        )
        ai_sess = GameSession(
            road_x=self.road_x + self.half_w,
            road_width=self.road_w,
            height=WINDOW_HEIGHT,
            rng=rng_ai,
            small_cars=True,
        )

        agent = DQNAgent()
        ai_state = ai_sess.reset()

        countdown = self._do_countdown()
        if not countdown:
            return

        while True:
            self.clock.tick(FPS)

            human_action = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        human_action = 1
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        human_action = 2

            # Human step
            spawned = human_sess.update(human_action)

            # AI step - inject same cars as human spawned (deterministic)
            ai_action = agent.select_action(ai_state, greedy=True)

            # Sync: replicate spawned cars from human's traffic manager to AI's
            # but with AI road_x offset
            ai_specs = []
            for spec in spawned:
                ai_specs.append({
                    "lane":     spec["lane"],
                    "y":        spec["y"],
                    "car_type": spec["car_type"],
                })
            ai_sess.update(ai_action, injected_cars=ai_specs if spawned else None)
            # If no injection, let AI traffic manage itself (same RNG seed ensures same sequence)
            if not spawned and ai_specs == []:
                pass   # already updated above

            ai_state = ai_sess.get_state()

            # Draw
            self.screen.fill(DARK_GRAY)

            # Draw divider
            pygame.draw.rect(self.screen, BLACK,
                             (self.half_w - 2, 0, 4, WINDOW_HEIGHT))

            human_sess.draw(self.screen)
            ai_sess.draw(self.screen)

            self._draw_labels(human_sess, ai_sess)
            pygame.display.flip()

            if not human_sess.alive or not ai_sess.alive:
                # Show result
                h_score = human_sess.score
                a_score = ai_sess.score
                # Let the other survive a bit longer if still alive
                if not human_sess.alive and ai_sess.alive:
                    # keep running AI for a moment
                    for _ in range(FPS * 2):
                        self.clock.tick(FPS)
                        ai_action = agent.select_action(ai_state, greedy=True)
                        ai_sess.update(ai_action)
                        ai_state = ai_sess.get_state()
                        self.screen.fill(DARK_GRAY)
                        pygame.draw.rect(self.screen, BLACK,
                                        (self.half_w - 2, 0, 4, WINDOW_HEIGHT))
                        human_sess.draw(self.screen)
                        ai_sess.draw(self.screen)
                        self._draw_labels(human_sess, ai_sess)
                        pygame.display.flip()
                        if not ai_sess.alive:
                            break
                a_score = ai_sess.score

                self._result_screen(h_score, a_score)
                return

    # ------------------------------------------------------------------

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
                pygame.draw.rect(self.screen, BLACK,
                                (self.half_w - 2, 0, 4, WINDOW_HEIGHT))
                num = self.font_large.render(str(i), True, YELLOW)
                self.screen.blit(num,
                                (WINDOW_WIDTH // 2 - num.get_width() // 2,
                                 WINDOW_HEIGHT // 2 - 40))
                pygame.display.flip()
        return True

    def _draw_labels(self, human_sess, ai_sess):
        # Panel headers
        hl = self.font_med.render("HUMAN", True, CYAN)
        al = self.font_med.render("AI", True, GREEN)
        self.screen.blit(hl, (self.half_w // 2 - hl.get_width() // 2, 10))
        self.screen.blit(al, (self.half_w + self.half_w // 2 - al.get_width() // 2, 10))

        # Scores
        hs = self.font_small.render(f"{human_sess.score:.1f}s", True, WHITE)
        as_ = self.font_small.render(f"{ai_sess.score:.1f}s", True, WHITE)
        self.screen.blit(hs,  (self.half_w // 2 - hs.get_width() // 2, 44))
        self.screen.blit(as_, (self.half_w + self.half_w // 2 - as_.get_width() // 2, 44))

        # DEAD label
        if not human_sess.alive:
            d = self.font_med.render("CRASHED!", True, RED)
            self.screen.blit(d, (self.half_w // 2 - d.get_width() // 2,
                                 WINDOW_HEIGHT // 2 - 20))
        if not ai_sess.alive:
            d = self.font_med.render("CRASHED!", True, RED)
            self.screen.blit(d, (self.half_w + self.half_w // 2 - d.get_width() // 2,
                                 WINDOW_HEIGHT // 2 - 20))

        # Controls hint
        hint = self.font_tiny.render("← → Human controls", True, GRAY)
        self.screen.blit(hint, (10, WINDOW_HEIGHT - 24))

    def _result_screen(self, h_score, a_score):
        if h_score > a_score:
            winner, color = "HUMAN WINS!", CYAN
        elif a_score > h_score:
            winner, color = "AI WINS!", GREEN
        else:
            winner, color = "IT'S A TIE!", YELLOW

        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    return

            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            w_surf = self.font_large.render(winner, True, color)
            h_surf = self.font_med.render(f"Human: {h_score:.1f}s", True, CYAN)
            a_surf = self.font_med.render(f"AI:    {a_score:.1f}s", True, GREEN)
            k_surf = self.font_small.render("Press any key to return to menu", True, LIGHT_GRAY)

            cx = WINDOW_WIDTH // 2
            self.screen.blit(w_surf, (cx - w_surf.get_width() // 2, 200))
            self.screen.blit(h_surf, (cx - h_surf.get_width() // 2, 290))
            self.screen.blit(a_surf, (cx - a_surf.get_width() // 2, 340))
            self.screen.blit(k_surf, (cx - k_surf.get_width() // 2, 430))
            pygame.display.flip()
