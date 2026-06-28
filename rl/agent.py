"""
Deep Q-Network (DQN) agent.
"""
import random
import math
import os
from collections import deque

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


STATE_DIM  = 15 + 3 + 1   # 5×3 grid + lane one-hot + speed
ACTION_DIM = 3


# -----------------------------------------------------------------------
# Neural Network
# -----------------------------------------------------------------------

if TORCH_AVAILABLE:
    class QNetwork(nn.Module):
        def __init__(self, state_dim=STATE_DIM, action_dim=ACTION_DIM):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(state_dim, 128),
                nn.ReLU(),
                nn.Linear(128, 128),
                nn.ReLU(),
                nn.Linear(128, action_dim),
            )

        def forward(self, x):
            return self.net(x)


# -----------------------------------------------------------------------
# Replay Buffer
# -----------------------------------------------------------------------

class ReplayBuffer:
    def __init__(self, capacity=50_000):
        self.buf = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buf.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buf, batch_size)

    def __len__(self):
        return len(self.buf)


# -----------------------------------------------------------------------
# DQN Agent
# -----------------------------------------------------------------------

class DQNAgent:
    def __init__(self,
                 state_dim=STATE_DIM,
                 action_dim=ACTION_DIM,
                 lr=1e-3,
                 gamma=0.99,
                 eps_start=1.0,
                 eps_end=0.05,
                 eps_decay=5000,
                 batch_size=64,
                 target_update=100,
                 model_path="models/dqn_highway.pth"):

        self.state_dim    = state_dim
        self.action_dim   = action_dim
        self.gamma        = gamma
        self.eps_start    = eps_start
        self.eps_end      = eps_end
        self.eps_decay    = eps_decay
        self.batch_size   = batch_size
        self.target_update = target_update
        self.model_path   = model_path

        self.steps_done   = 0
        self.update_count = 0
        self.episode      = 0
        self.scores       = []
        self.avg_rewards  = []

        self.torch_ok = TORCH_AVAILABLE
        if self.torch_ok:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.policy_net = QNetwork(state_dim, action_dim).to(self.device)
            self.target_net = QNetwork(state_dim, action_dim).to(self.device)
            self.target_net.load_state_dict(self.policy_net.state_dict())
            self.target_net.eval()
            self.optimizer  = optim.Adam(self.policy_net.parameters(), lr=lr)
            self.buffer     = ReplayBuffer()
            self._try_load()
        else:
            # Fallback: rule-based agent when torch unavailable
            pass

    # ------------------------------------------------------------------

    def _epsilon(self):
        return self.eps_end + (self.eps_start - self.eps_end) * \
               math.exp(-self.steps_done / self.eps_decay)

    def select_action(self, state, greedy=False):
        """Select action with ε-greedy policy."""
        if not self.torch_ok:
            return self._rule_based(state)

        eps = 0.0 if greedy else self._epsilon()
        self.steps_done += 1

        if random.random() < eps:
            return random.randint(0, self.action_dim - 1)

        with torch.no_grad():
            t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q = self.policy_net(t)
            return q.argmax().item()

    def get_q_values(self, state):
        if not self.torch_ok:
            return [0.0, 0.0, 0.0]
        with torch.no_grad():
            t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            return self.policy_net(t).squeeze().tolist()

    def _rule_based(self, state):
        """Simple rule-based fallback when PyTorch is not installed."""
        # state: 15 grid cells (5 rows × 3 lanes) + 3 lane-oh + 1 speed
        grid = state[:15]
        lane_oh = state[15:18]
        cur_lane = lane_oh.index(1) if 1 in lane_oh else 1

        # Check immediate row (row 0)
        if grid[cur_lane] == 1:           # blocked directly ahead
            if cur_lane > 0 and grid[cur_lane - 1] == 0:
                return 1   # go left
            elif cur_lane < 2 and grid[cur_lane + 1] == 0:
                return 2   # go right
        return 0

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def store(self, state, action, reward, next_state, done):
        if self.torch_ok:
            self.buffer.push(state, action, reward, next_state, done)

    def train_step(self):
        if not self.torch_ok or len(self.buffer) < self.batch_size:
            return None

        batch    = self.buffer.sample(self.batch_size)
        states   = torch.FloatTensor([b[0] for b in batch]).to(self.device)
        actions  = torch.LongTensor( [b[1] for b in batch]).to(self.device)
        rewards  = torch.FloatTensor([b[2] for b in batch]).to(self.device)
        nstates  = torch.FloatTensor([b[3] for b in batch]).to(self.device)
        dones    = torch.FloatTensor([b[4] for b in batch]).to(self.device)

        # Current Q
        q_vals   = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze()

        # Target Q (Double DQN)
        with torch.no_grad():
            next_actions = self.policy_net(nstates).argmax(1)
            next_q       = self.target_net(nstates).gather(1, next_actions.unsqueeze(1)).squeeze()
            target       = rewards + self.gamma * next_q * (1 - dones)

        loss = nn.SmoothL1Loss()(q_vals, target)
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        self.update_count += 1
        if self.update_count % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return loss.item()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self):
        if not self.torch_ok:
            return
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save({
            "policy":      self.policy_net.state_dict(),
            "target":      self.target_net.state_dict(),
            "optimizer":   self.optimizer.state_dict(),
            "steps_done":  self.steps_done,
            "episode":     self.episode,
            "scores":      self.scores,
        }, self.model_path)

    def _try_load(self):
        if not self.torch_ok or not os.path.exists(self.model_path):
            return
        try:
            ckpt = torch.load(self.model_path, map_location=self.device)
            self.policy_net.load_state_dict(ckpt["policy"])
            self.target_net.load_state_dict(ckpt["target"])
            self.optimizer.load_state_dict(ckpt["optimizer"])
            self.steps_done = ckpt.get("steps_done", 0)
            self.episode    = ckpt.get("episode", 0)
            self.scores     = ckpt.get("scores", [])
            print(f"[DQN] Loaded checkpoint: episode {self.episode}, "
                  f"steps {self.steps_done}")
        except Exception as e:
            print(f"[DQN] Could not load checkpoint: {e}")

    def model_exists(self):
        return os.path.exists(self.model_path)
