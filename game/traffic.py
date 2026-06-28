"""
Traffic manager: spawning, movement, state grid, collision detection.
"""
import random
import pygame
from game.constants import *


CAR_TYPES = ["sedan", "suv", "truck"]


class TrafficCar:
    def __init__(self, lane, y, car_type, road_x, lane_width):
        self.lane      = lane
        self.y         = float(y)
        self.car_type  = car_type
        self.road_x    = road_x
        self.lane_width = lane_width
        self.width     = TRAFFIC_WIDTH - 8
        self.height    = TRAFFIC_HEIGHT + (10 if car_type == "truck" else 0)

    @property
    def x(self):
        return self.road_x + self.lane * self.lane_width + self.lane_width // 2

    def rect(self):
        return pygame.Rect(
            self.x - self.width // 2,
            int(self.y) - self.height // 2,
            self.width,
            self.height,
        )


class TrafficManager:
    """
    Manages traffic for one road instance.
    Supports seeded RNG for deterministic Human vs AI mode.
    """

    def __init__(self, road_x, lane_width, screen_height, rng=None):
        self.road_x        = road_x
        self.lane_width    = lane_width
        self.screen_height = screen_height
        self.rng           = rng or random.Random()
        self.cars: list[TrafficCar] = []

        self._spawn_timer   = 0.0
        self._spawn_interval = 90   # frames between spawn attempts
        self._min_gap        = TRAFFIC_HEIGHT + 30

    # ------------------------------------------------------------------
    def update(self, scroll_speed, difficulty_level):
        """Move cars and maybe spawn new ones. Returns list of new cars
        that were spawned this frame (for seed-sync in vs mode)."""
        # Move existing cars downward
        to_remove = []
        for car in self.cars:
            car.y += scroll_speed
            if car.y > self.screen_height + 200:
                to_remove.append(car)
        for car in to_remove:
            self.cars.remove(car)

        # Adjust spawn rate with difficulty
        base_interval = max(30, 90 - difficulty_level * 8)
        self._spawn_interval = base_interval

        self._spawn_timer += 1
        spawned = []
        if self._spawn_timer >= self._spawn_interval:
            self._spawn_timer = 0
            new_cars = self._try_spawn(difficulty_level)
            spawned.extend(new_cars)

        return spawned

    def inject_cars(self, car_specs):
        """Inject pre-determined cars (used by AI lane in vs mode)."""
        for spec in car_specs:
            car = TrafficCar(
                lane=spec["lane"],
                y=spec["y"],
                car_type=spec["car_type"],
                road_x=self.road_x,
                lane_width=self.lane_width,
            )
            self.cars.append(car)

    def _try_spawn(self, difficulty_level):
        """Attempt to spawn a pattern. Returns list of car specs."""
        pattern = self._choose_pattern(difficulty_level)
        spawn_y = -TRAFFIC_HEIGHT * 2

        new_cars = []
        for lane, car_type in pattern:
            # Check spacing
            conflict = False
            for existing in self.cars:
                if existing.lane == lane and abs(existing.y - spawn_y) < self._min_gap:
                    conflict = True
                    break
            if conflict:
                continue

            car = TrafficCar(lane, spawn_y, car_type, self.road_x, self.lane_width)
            self.cars.append(car)
            new_cars.append({"lane": lane, "y": spawn_y, "car_type": car_type})

        # Safety: ensure at least one open lane somewhere near spawn
        if not self._safe_lane_exists(spawn_y):
            # Remove the last spawned batch
            for spec in new_cars:
                self.cars = [c for c in self.cars
                             if not (c.lane == spec["lane"] and abs(c.y - spec["y"]) < 5)]
            new_cars = []

        return new_cars

    def _choose_pattern(self, difficulty_level):
        """Return list of (lane, car_type) tuples for one spawn wave."""
        rng = self.rng
        car_type = rng.choice(CAR_TYPES)

        if difficulty_level < 2:
            # Single car
            lane = rng.randint(0, LANE_COUNT - 1)
            return [(lane, car_type)]
        elif difficulty_level < 4:
            # Single or two-car block
            choice = rng.random()
            if choice < 0.5:
                lane = rng.randint(0, LANE_COUNT - 1)
                return [(lane, car_type)]
            else:
                lanes = rng.sample(range(LANE_COUNT), 2)
                return [(l, rng.choice(CAR_TYPES)) for l in lanes]
        else:
            # Any pattern including alternating
            choice = rng.random()
            if choice < 0.3:
                lane = rng.randint(0, LANE_COUNT - 1)
                return [(lane, car_type)]
            elif choice < 0.6:
                lanes = rng.sample(range(LANE_COUNT), 2)
                return [(l, rng.choice(CAR_TYPES)) for l in lanes]
            else:
                # Block two lanes, leave one open
                open_lane = rng.randint(0, LANE_COUNT - 1)
                blocked = [l for l in range(LANE_COUNT) if l != open_lane]
                return [(l, rng.choice(CAR_TYPES)) for l in blocked]

    def _safe_lane_exists(self, near_y):
        """Return True if at least one lane has no car within 200px of near_y."""
        for lane in range(LANE_COUNT):
            blocked = any(
                c.lane == lane and abs(c.y - near_y) < 200
                for c in self.cars
            )
            if not blocked:
                return True
        return False

    def check_collision(self, player_rect) -> bool:
        for car in self.cars:
            if car.rect().colliderect(player_rect):
                return True
        return False

    def get_state_grid(self, player_lane, player_y, scroll_speed):
        """
        Returns (grid, speed_norm) where grid is (STATE_LANES x STATE_ROWS) binary array,
        row 0 = closest ahead.
        """
        grid = [[0] * STATE_LANES for _ in range(STATE_ROWS)]

        for car in self.cars:
            dy = player_y - car.y   # positive = car is above player = ahead
            if dy < 0 or dy > STATE_ROWS * CELL_HEIGHT:
                continue
            row = int(dy // CELL_HEIGHT)
            if 0 <= row < STATE_ROWS and 0 <= car.lane < STATE_LANES:
                grid[row][car.lane] = 1

        flat = [grid[r][l] for r in range(STATE_ROWS) for l in range(STATE_LANES)]
        speed_norm = min(scroll_speed / MAX_SCROLL_SPEED, 1.0)
        return flat, speed_norm
