"""CPU controller for computer-controlled players."""

import math
import random

import pygame

from src.settings import GRAVITY, GROUND_Y, KICK_RANGE, WIDTH


CPU_PROFILES = {
    "easy": {
        "delay_ms": 400,
        "kick_miss_chance": 0.40,
        "jump_chance": 0.25,
        "target_margin": 50,
        "prediction_steps": 0,
        "behavior_change_ms": 900,
        "behaviors": {
            "chase": 0.45,
            "position": 0.15,
            "idle": 0.25,
            "random_walk": 0.15,
        },
    },
    "medium": {
        "delay_ms": 180,
        "kick_miss_chance": 0.15,
        "jump_chance": 0.75,
        "target_margin": 30,
        "prediction_steps": 20,
        "behavior_change_ms": 550,
        "behaviors": {
            "chase": 0.30,
            "intercept": 0.30,
            "position": 0.25,
            "retreat": 0.10,
            "idle": 0.05,
        },
    },
    "hard": {
        "delay_ms": 50,
        "kick_miss_chance": 0.03,
        "jump_chance": 1.0,
        "target_margin": 14,
        "prediction_steps": 60,
        "behavior_change_ms": 300,
        "behaviors": {
            "intercept": 0.30,
            "aim_at_goal": 0.30,
            "position": 0.20,
            "retreat": 0.15,
            "aggressive": 0.05,
        },
    },
}


def _weighted_choice(weights_dict):
    keys = list(weights_dict.keys())
    weights = [weights_dict[k] for k in keys]
    return random.choices(keys, weights=weights, k=1)[0]


class CPUController:
    """Decides simulated key presses for a CPU-controlled player.

    Difficulty levels:
        easy: Slow reaction, high miss rate. Randomly alternates between
            chasing the ball, wandering, and standing idle.
        medium: Moderate reaction. Mixes direct chase, ball interception,
            goal-oriented positioning, and occasional retreats.
        hard: Fast reaction. Predicts ball trajectory, aims kicks at the
            opponent's goal, and tactically retreats to defend.
    """

    def __init__(self, player, ball, difficulty):
        """Create a CPU controller for a player and ball.

        Args:
            player: Player object controlled by this AI.
            ball: Ball object to track and kick.
            difficulty: One of 'easy', 'medium', or 'hard'.
        """
        if difficulty not in CPU_PROFILES:
            raise ValueError("difficulty must be 'easy', 'medium', or 'hard'.")

        self.player = player
        self.ball = ball
        self.difficulty = difficulty
        self.profile = CPU_PROFILES[difficulty]
        self.last_decision_ms = 0
        self.last_behavior_change_ms = 0
        self.current_behavior = "chase"
        self.current_decision = self._empty_decision()
        self._random_walk_dir = 1

    def decide(self, dt):
        """Return a dict that simulates pressed movement/action keys.

        Returns:
            Dict in the format {'left': bool, 'right': bool, 'jump': bool,
            'kick': bool}.
        """
        now = pygame.time.get_ticks()

        if now - self.last_behavior_change_ms >= self.profile["behavior_change_ms"]:
            self.last_behavior_change_ms = now
            self._pick_behavior()

        if now - self.last_decision_ms < self.profile["delay_ms"]:
            return self.current_decision.copy()

        self.last_decision_ms = now
        self.current_decision = self._execute_behavior()
        return self.current_decision.copy()

    # ------------------------------------------------------------------
    # Behavior selection
    # ------------------------------------------------------------------

    def _pick_behavior(self):
        """Choose a behavior based on game state and difficulty weights."""
        ball_x, ball_y = self.ball.rect.center
        player_x, player_y = self.player.rect.center
        dist = math.hypot(ball_x - player_x, ball_y - player_y)

        # Ball is right there — act decisively regardless of difficulty
        if dist < KICK_RANGE * 1.3:
            if self.difficulty == "easy":
                self.current_behavior = random.choice(["chase", "position", "idle"])
            else:
                self.current_behavior = random.choice(["position", "aim_at_goal", "intercept"])
            return

        # Ball threatens own goal — switch to defense
        cpu_attacks_left = self.player.rect.centerx > WIDTH // 2
        own_goal_x = WIDTH if cpu_attacks_left else 0
        ball_near_own_goal = abs(ball_x - own_goal_x) < WIDTH * 0.3
        if ball_near_own_goal and self.difficulty != "easy":
            self.current_behavior = "retreat" if random.random() < 0.5 else "intercept"
            return

        self.current_behavior = _weighted_choice(self.profile["behaviors"])

    def _execute_behavior(self):
        """Dispatch to the correct behavior handler."""
        handlers = {
            "chase": self._behavior_chase,
            "intercept": self._behavior_intercept,
            "position": self._behavior_position,
            "aim_at_goal": self._behavior_aim_at_goal,
            "retreat": self._behavior_retreat,
            "idle": self._behavior_idle,
            "random_walk": self._behavior_random_walk,
            "aggressive": self._behavior_aggressive,
        }
        handler = handlers.get(self.current_behavior, lambda: self._empty_decision())
        return handler()

    # ------------------------------------------------------------------
    # Individual behaviors
    # ------------------------------------------------------------------

    def _behavior_chase(self):
        """Move directly toward the ball's current position."""
        decision = self._empty_decision()
        ball_x, ball_y = self.ball.rect.center
        player_x, player_y = self.player.rect.center
        margin = self.profile["target_margin"]

        if ball_x < player_x - margin:
            decision["left"] = True
        elif ball_x > player_x + margin:
            decision["right"] = True

        ball_is_high = ball_y < player_y - 60
        ball_is_close = abs(ball_x - player_x) < KICK_RANGE * 1.5
        if ball_is_high and ball_is_close:
            decision["jump"] = random.random() < self.profile["jump_chance"]

        if self._ball_in_kick_range():
            decision["kick"] = random.random() >= self.profile["kick_miss_chance"]

        return decision

    def _behavior_intercept(self):
        """Move to the predicted future landing position of the ball."""
        decision = self._empty_decision()
        target_x = self._predict_ball_impact_x()
        player_x, player_y = self.player.rect.center
        ball_x, ball_y = self.ball.rect.center
        margin = self.profile["target_margin"]

        if target_x < player_x - margin:
            decision["left"] = True
        elif target_x > player_x + margin:
            decision["right"] = True

        ball_is_high = ball_y < player_y - 55
        ball_is_close = abs(ball_x - player_x) < KICK_RANGE * 1.6
        if ball_is_high and ball_is_close:
            decision["jump"] = random.random() < self.profile["jump_chance"]

        if self._ball_in_kick_range():
            decision["kick"] = random.random() >= self.profile["kick_miss_chance"]

        return decision

    def _behavior_position(self):
        """Move beside the ball to set up a kick toward the opponent's goal."""
        decision = self._empty_decision()
        ball_x, ball_y = self.ball.rect.center
        player_x, player_y = self.player.rect.center

        # Stand slightly on the same side as own goal so kick goes the right way
        cpu_attacks_left = self.player.rect.centerx > WIDTH // 2
        offset = 40 if cpu_attacks_left else -40
        target_x = max(50, min(WIDTH - 50, ball_x + offset))

        margin = self.profile["target_margin"]
        if target_x < player_x - margin:
            decision["left"] = True
        elif target_x > player_x + margin:
            decision["right"] = True

        ball_is_high = ball_y < player_y - 50
        ball_is_close = abs(ball_x - player_x) < KICK_RANGE * 1.4
        if ball_is_high and ball_is_close:
            decision["jump"] = random.random() < self.profile["jump_chance"]

        if self._ball_in_kick_range():
            decision["kick"] = random.random() >= self.profile["kick_miss_chance"]

        return decision

    def _behavior_aim_at_goal(self):
        """Get behind the ball to kick it directly at the opponent's goal."""
        decision = self._empty_decision()
        ball_x, ball_y = self.ball.rect.center
        player_x, player_y = self.player.rect.center

        cpu_attacks_left = self.player.rect.centerx > WIDTH // 2
        # To kick ball toward left (x=0), stand to the right of it, and vice-versa
        target_x = ball_x + 35 if cpu_attacks_left else ball_x - 35
        target_x = max(50, min(WIDTH - 50, target_x))

        margin = self.profile["target_margin"]
        if target_x < player_x - margin:
            decision["left"] = True
        elif target_x > player_x + margin:
            decision["right"] = True

        ball_is_high = ball_y < player_y - 45
        ball_is_close = abs(ball_x - player_x) < KICK_RANGE * 1.8
        if ball_is_high and ball_is_close:
            decision["jump"] = True

        if self._ball_in_kick_range():
            decision["kick"] = random.random() >= self.profile["kick_miss_chance"]

        return decision

    def _behavior_retreat(self):
        """Pull back toward own half to defend against a dangerous ball."""
        decision = self._empty_decision()
        player_x = self.player.rect.centerx
        ball_x = self.ball.rect.centerx

        cpu_attacks_left = self.player.rect.centerx > WIDTH // 2
        home_x = WIDTH * 0.72 if cpu_attacks_left else WIDTH * 0.28

        margin = self.profile["target_margin"]
        if home_x < player_x - margin:
            decision["left"] = True
        elif home_x > player_x + margin:
            decision["right"] = True

        if self._ball_in_kick_range():
            decision["kick"] = random.random() >= self.profile["kick_miss_chance"]

        return decision

    def _behavior_idle(self):
        """Stand still; kick only if the ball is right at feet."""
        decision = self._empty_decision()
        if self._ball_in_kick_range():
            decision["kick"] = random.random() >= self.profile["kick_miss_chance"]
        return decision

    def _behavior_random_walk(self):
        """Wander randomly — easy-mode confusion behavior."""
        decision = self._empty_decision()

        if random.random() < 0.15:
            self._random_walk_dir *= -1
        player_x = self.player.rect.centerx
        if player_x <= 50:
            self._random_walk_dir = 1
        elif player_x >= WIDTH - 50:
            self._random_walk_dir = -1

        if self._random_walk_dir > 0:
            decision["right"] = True
        else:
            decision["left"] = True

        if self._ball_in_kick_range():
            decision["kick"] = random.random() >= self.profile["kick_miss_chance"]

        return decision

    def _behavior_aggressive(self):
        """Rush the ball with no hesitation — hard-mode burst behavior."""
        decision = self._empty_decision()
        ball_x, ball_y = self.ball.rect.center
        player_x, player_y = self.player.rect.center

        if ball_x < player_x:
            decision["left"] = True
        elif ball_x > player_x:
            decision["right"] = True

        if ball_y < player_y - 40 and self.player.on_ground:
            decision["jump"] = True

        if self._ball_in_kick_range():
            decision["kick"] = True

        return decision

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _predict_ball_impact_x(self):
        """Estimate where the ball will reach near ground level using gravity."""
        x = float(self.ball.rect.centerx)
        y = float(self.ball.rect.centery)
        vel_x = float(self.ball.vel_x)
        vel_y = float(self.ball.vel_y)

        steps = self.profile["prediction_steps"] if self.profile["prediction_steps"] > 0 else 30

        for _ in range(steps):
            vel_y += GRAVITY
            x += vel_x
            y += vel_y

            if x < 0:
                x = 0
                vel_x *= -1
            elif x > WIDTH:
                x = WIDTH
                vel_x *= -1

            if y >= GROUND_Y:
                break

        return max(0, min(WIDTH, x))

    def _ball_in_kick_range(self):
        """Return True when the ball is close enough for the CPU to kick."""
        player_x, player_y = self.player.rect.center
        ball_x, ball_y = self.ball.rect.center
        return math.hypot(ball_x - player_x, ball_y - player_y) < KICK_RANGE

    def _empty_decision(self):
        """Return a neutral decision with no simulated key pressed."""
        return {"left": False, "right": False, "jump": False, "kick": False}
