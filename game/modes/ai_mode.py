"""
AI Mode: watch the trained agent OR train it live.
"""
import pygame
import sys
from game.constants import *
from game.session import GameSession
from rl.agent import DQNAgent

SAVE_EVERY = 25   # episodes


class AIMode:
    def __init__(self, screen, clock):
        self.screen     = screen
        self.clock      = clock
        self.font_med   = pygame.font.SysFont("consolas", FONT_MEDIUM, bold=True)
        self.font_small = pygame.font.SysFont("consolas", FONT_SMALL)
        self.font_tiny  = pygame.font.SysFont("consolas", 14)

    def run(self):
        # Sub-menu: watch or train
        mode = self._sub_menu()
        if mode is None:
            return

        agent   = DQNAgent()
        session = GameSession(road_x=ROAD_X, road_width=ROAD_WIDTH,
                              height=WINDOW_HEIGHT)
        state   = session.reset()

        greedy   = (mode == "watch")
        training = (mode == "train")

        episode_reward = 0.0
        episode        = agent.episode
        best_score     = max(agent.scores) if agent.scores else 0.0
        recent_scores  = list(agent.scores[-20:]) if agent.scores else []
        loss_val       = 0.0

        # Graph data
        graph_scores = list(agent.scores[-80:]) if agent.scores else []

        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_s and training:
                        agent.save()

            action  = agent.select_action(state, greedy=greedy)
            session.update(action)
            reward  = session.last_reward
            done    = not session.alive
            nstate  = session.get_state()

            if training:
                agent.store(state, action, reward, nstate, done)
                loss_val = agent.train_step() or loss_val

            state           = nstate
            episode_reward += reward

            if done:
                episode += 1
                agent.episode = episode
                score = session.score
                recent_scores.append(score)
                graph_scores.append(score)
                if len(recent_scores) > 20:
                    recent_scores.pop(0)
                if len(graph_scores) > 80:
                    graph_scores.pop(0)
                best_score = max(best_score, score)
                agent.scores.append(score)

                if training and episode % SAVE_EVERY == 0:
                    agent.save()

                episode_reward = 0.0
                state = session.reset()

            # Draw
            self.screen.fill(DARK_GRAY)
            session.draw(self.screen)
            self._draw_hud(session, agent, episode, episode_reward,
                           best_score, recent_scores, greedy, loss_val)
            self._draw_graph(graph_scores)
            if not greedy:
                self._draw_vision_overlay(session, agent, state)
            pygame.display.flip()

        if training:
            agent.save()

    # ------------------------------------------------------------------

    def _sub_menu(self):
        options = []
        agent   = DQNAgent.__new__(DQNAgent)
        agent.model_path = "models/dqn_highway.pth"

        import os
        has_model = os.path.exists(agent.model_path)
        opts = [
            ("T", "Train from scratch" if not has_model else "Continue Training"),
            ("W", "Watch AI" if has_model else "Watch AI (no model yet — will use rules)"),
        ]
        font_m = pygame.font.SysFont("consolas", FONT_MEDIUM, bold=True)
        font_s = pygame.font.SysFont("consolas", FONT_SMALL)
        font_l = pygame.font.SysFont("consolas", FONT_LARGE, bold=True)

        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_t:
                        return "train"
                    if event.key == pygame.K_w:
                        return "watch"

            self.screen.fill(DARK_GRAY)
            title = font_l.render("AI MODE", True, CYAN)
            self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 180))

            for i, (key, label) in enumerate(opts):
                surf = font_m.render(f"[{key}]  {label}", True, WHITE)
                self.screen.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2,
                                        280 + i * 70))

            hint = font_s.render("ESC  Back to menu", True, GRAY)
            self.screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2,
                                    WINDOW_HEIGHT - 50))
            pygame.display.flip()

    # ------------------------------------------------------------------

    def _draw_hud(self, session, agent, episode, ep_reward,
                  best, recent, greedy, loss):
        from rl.agent import TORCH_AVAILABLE
        x, y = ROAD_X + ROAD_WIDTH + 20, 20
        mode_str = "EVAL" if greedy else "TRAIN"
        title = self.font_med.render(f"AI [{mode_str}]", True, CYAN)
        self.screen.blit(title, (x, y)); y += 38
        pygame.draw.line(self.screen, CYAN, (x, y), (x + 140, y), 2); y += 10

        avg = sum(recent) / len(recent) if recent else 0.0
        eps_val = agent._epsilon() if not greedy and hasattr(agent, "_epsilon") else 0.0

        rows = [
            ("Episode",  str(episode)),
            ("Time",     f"{session.score:.1f}s"),
            ("Reward",   f"{ep_reward:.1f}"),
            ("Best",     f"{best:.1f}s"),
            ("Avg(20)",  f"{avg:.1f}s"),
        ]
        if not greedy:
            rows.append(("ε",  f"{eps_val:.3f}"))
            if loss:
                rows.append(("Loss", f"{loss:.4f}"))

        for label, val in rows:
            ls = self.font_tiny.render(label, True, LIGHT_GRAY)
            vs = self.font_small.render(val,   True, WHITE)
            self.screen.blit(ls, (x, y));       y += 18
            self.screen.blit(vs, (x + 10, y));  y += 28

        if not greedy:
            hint = self.font_tiny.render("S = save model", True, GRAY)
            self.screen.blit(hint, (x, WINDOW_HEIGHT - 50))

        if not TORCH_AVAILABLE:
            warn = self.font_tiny.render("PyTorch not found!", True, RED)
            self.screen.blit(warn, (x, WINDOW_HEIGHT - 70))
            warn2 = self.font_tiny.render("Using rule-based AI", True, ORANGE)
            self.screen.blit(warn2, (x, WINDOW_HEIGHT - 50))

    def _draw_graph(self, scores):
        if len(scores) < 2:
            return
        gx, gy = 10, WINDOW_HEIGHT - 140
        gw, gh = ROAD_X - 20, 120
        pygame.draw.rect(self.screen, (30, 30, 30), (gx, gy, gw, gh))
        pygame.draw.rect(self.screen, GRAY, (gx, gy, gw, gh), 1)

        label = self.font_tiny.render("Score history", True, GRAY)
        self.screen.blit(label, (gx + 4, gy + 2))

        mx = max(scores) if scores else 1
        pts = []
        for i, s in enumerate(scores):
            px = gx + int(i / max(len(scores) - 1, 1) * gw)
            py = gy + gh - int(s / max(mx, 1) * (gh - 18)) - 4
            pts.append((px, py))
        if len(pts) > 1:
            pygame.draw.lines(self.screen, GREEN, False, pts, 2)

    def _draw_vision_overlay(self, session, agent, state):
        """Overlay the 5×3 occupancy grid the agent sees."""
        grid_data = state[:15]   # 5 rows × 3 lanes
        ox = ROAD_X + 10
        cell_w = LANE_WIDTH - 6
        cell_h = 24

        label = self.font_tiny.render("AI VISION", True, YELLOW)
        self.screen.blit(label, (ox, session.player_y - STATE_ROWS * cell_h - 24))

        for row in range(STATE_ROWS):
            for lane in range(3):
                val = grid_data[row * 3 + lane]
                cx  = ROAD_X + lane * LANE_WIDTH + 8
                cy  = session.player_y - (STATE_ROWS - row) * cell_h - 10
                color = (200, 60, 60, 160) if val else (60, 60, 60, 80)
                s = pygame.Surface((cell_w, cell_h - 2), pygame.SRCALPHA)
                s.fill(color)
                self.screen.blit(s, (cx, cy))
                if lane == session.player_lane and row == 0:
                    pygame.draw.rect(self.screen, YELLOW, (cx, cy, cell_w, cell_h - 2), 1)

        # Q-values
        qv = agent.get_q_values(state)
        actions = ["STAY", "LEFT", "RIGHT"]
        qx = ROAD_X + ROAD_WIDTH + 20
        qy = WINDOW_HEIGHT - 110
        ql = self.font_tiny.render("Q-values:", True, YELLOW)
        self.screen.blit(ql, (qx, qy)); qy += 18
        for a, q in zip(actions, qv):
            color = GREEN if q == max(qv) else LIGHT_GRAY
            qs = self.font_tiny.render(f"  {a}: {q:.2f}", True, color)
            self.screen.blit(qs, (qx, qy)); qy += 16
