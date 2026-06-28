"""
Core game session - one road, one player, one traffic manager.
Used by all three modes.
"""
import pygame
import random
from game.constants import *
from game.road import Road
from game.traffic import TrafficManager
from game.cars import draw_player_car, draw_traffic_car


class GameSession:
    """
    A self-contained game session.

    Parameters
    ----------
    road_x      : left edge of road in pixels (within the surface)
    road_width  : total road width
    height      : surface height
    rng         : optional seeded random.Random (for deterministic mode)
    offset_x    : horizontal draw offset (for split-screen subsurface)
    """

    def __init__(self, road_x, road_width, height,
                 rng=None, offset_x=0, small_cars=False):
        self.road_x      = road_x
        self.road_width  = road_width
        self.height      = height
        self.offset_x    = offset_x
        self.small_cars  = small_cars

        self.lane_width  = road_width // LANE_COUNT
        self.road        = Road(road_x, road_width, height, LANE_COUNT)
        self.traffic     = TrafficManager(road_x, self.lane_width, height, rng)

        # Player state
        self.player_lane   = 1          # 0=left, 1=mid, 2=right
        self.player_y      = int(height * PLAYER_Y_FRAC)
        self.player_x      = self._lane_cx(1)

        # Game state
        self.scroll_speed    = BASE_SCROLL_SPEED
        self.alive           = True
        self.frames          = 0
        self.score           = 0.0
        self.difficulty      = 0
        self.last_lane       = 1
        self.collision_flash = 0    # frames of red flash on death

        # Reward accumulator (for RL)
        self.last_reward = 0.0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def _lane_cx(self, lane):
        return self.road_x + lane * self.lane_width + self.lane_width // 2

    @property
    def player_rect(self):
        pw = PLAYER_WIDTH - 8
        ph = PLAYER_HEIGHT - 4
        if self.small_cars:
            pw -= 8; ph -= 12
        return pygame.Rect(
            self.player_x - pw // 2,
            self.player_y - ph // 2,
            pw, ph,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, action=0, injected_cars=None):
        """
        action: 0=stay, 1=left, 2=right
        injected_cars: list of car specs to add (vs mode sync)
        Returns list of spawned car specs (for vs mode sync).
        """
        if not self.alive:
            return []

        # Difficulty ramp
        self.frames += 1
        elapsed_sec = self.frames / FPS
        self.difficulty = int(elapsed_sec / DIFFICULTY_INTERVAL)
        self.scroll_speed = min(
            BASE_SCROLL_SPEED + self.difficulty * SPEED_INCREMENT,
            MAX_SCROLL_SPEED,
        )

        # Road scroll
        self.road.update(self.scroll_speed)

        # Player action
        prev_lane = self.player_lane
        if action == 1 and self.player_lane > 0:
            self.player_lane -= 1
        elif action == 2 and self.player_lane < LANE_COUNT - 1:
            self.player_lane += 1
        self.player_x = self._lane_cx(self.player_lane)

        # Traffic
        if injected_cars is not None:
            self.traffic.inject_cars(injected_cars)
            spawned = []
        else:
            spawned = self.traffic.update(self.scroll_speed, self.difficulty)

        # Collision
        reward = 0.0
        if self.traffic.check_collision(self.player_rect):
            self.alive          = False
            self.collision_flash = 20
            reward              = -100.0
            self.last_reward    = reward
            return spawned

        # Reward
        reward += 1.0          # survived
        reward += 0.1          # forward progress
        if self.player_lane != prev_lane:
            # Bonus if there was a car in old lane within 3 rows
            grid, _ = self.traffic.get_state_grid(
                prev_lane, self.player_y, self.scroll_speed)
            for r in range(min(3, STATE_ROWS)):
                if grid[r * STATE_LANES + prev_lane]:
                    reward += 0.5
                    break
            # Penalty for excessive switching (only if no threat)
            else:
                reward -= 0.05

        self.score        = self.frames / FPS
        self.last_reward  = reward
        return spawned

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface):
        self.road.draw(surface, self.offset_x)

        # Traffic cars
        for car in self.traffic.cars:
            draw_traffic_car(
                surface,
                car.x + self.offset_x,
                int(car.y),
                car.car_type,
                small=self.small_cars,
            )

        # Player car
        if self.alive or self.collision_flash > 0:
            color = RED if self.collision_flash > 0 else BLUE
            draw_player_car(
                surface,
                self.player_x + self.offset_x,
                self.player_y,
                color=color,
                small=self.small_cars,
            )
            if self.collision_flash > 0:
                self.collision_flash -= 1

    # ------------------------------------------------------------------
    # RL helpers
    # ------------------------------------------------------------------

    def get_state(self):
        """Return flat state vector for RL agent."""
        grid, speed_norm = self.traffic.get_state_grid(
            self.player_lane, self.player_y, self.scroll_speed)
        # One-hot lane
        lane_oh = [0, 0, 0]
        lane_oh[self.player_lane] = 1
        return grid + lane_oh + [speed_norm]

    def reset(self):
        """Reset session in-place for RL training."""
        self.player_lane   = 1
        self.player_x      = self._lane_cx(1)
        self.scroll_speed  = BASE_SCROLL_SPEED
        self.alive         = True
        self.frames        = 0
        self.score         = 0.0
        self.difficulty    = 0
        self.last_reward   = 0.0
        self.collision_flash = 0
        self.traffic.cars  = []
        self.traffic._spawn_timer = 0
        self.road.scroll_y = 0.0
        return self.get_state()
