"""CPU controller for computer-controlled players."""

import math
import random

import pygame

from src.settings import GRAVITY, GROUND_Y, KICK_RANGE, PLAYER_SPEED, WIDTH


CPU_PROFILES = {
    "easy": {
        "delay_ms": 400,
        "kick_miss_chance": 0.35,
        "jump_chance": 0.25,
        "target_margin": 45,
        "prediction_steps": 0,
    },
    "medium": {
        "delay_ms": 200,
        "kick_miss_chance": 0.12,
        "jump_chance": 0.75,
        "target_margin": 28,
        "prediction_steps": 20,
    },
    "hard": {
        "delay_ms": 50,
        "kick_miss_chance": 0.02,
        "jump_chance": 1.0,
        "target_margin": 14,
        "prediction_steps": 60,
    },
}


class CPUController:
    """Decides simulated key presses for a CPU-controlled player.

    Difficulty levels:
        easy: Waits about 400 ms between decisions, follows the ball with loose
            positioning, sometimes misses kicks, and only jumps occasionally.
        medium: Waits about 200 ms, actively chases the ball, jumps when the
            ball is high and close, and usually kicks when in range.
        hard: Waits about 50 ms, tries to stand between the ball and its own
            goal, predicts the ball's future impact point with simple gravity,
            and kicks with very few intentional mistakes.
    """

    def __init__(self, player, ball, difficulty):
        """Create a CPU controller for a player and ball.

        Args:
            player: Player object controlled by this AI. It must expose rect,
                vel_x, vel_y, on_ground, and facing_right attributes.
            ball: Ball object to chase and kick. It must expose rect, vel_x,
                and vel_y attributes.
            difficulty: One of 'easy', 'medium', or 'hard'.

        Raises:
            ValueError: If difficulty is not one of the supported levels.
        """
        if difficulty not in CPU_PROFILES:
            raise ValueError("difficulty must be 'easy', 'medium', or 'hard'.")

        self.player = player
        self.ball = ball
        self.difficulty = difficulty
        self.profile = CPU_PROFILES[difficulty]
        self.last_decision_ms = 0
        self.current_decision = self._empty_decision()

    def decide(self, dt):
        """Return a dict that simulates pressed movement/action keys.

        Args:
            dt: Time elapsed since the previous frame, in seconds. The current
                controller uses pygame's clock for decision delay, but dt is
                accepted so scenes can call all controllers consistently.

        Returns:
            Dict in the format {'left': bool, 'right': bool, 'jump': bool,
            'kick': bool}. A GameplayScene can translate these booleans into
            the CPU player's configured pygame key constants.

        The controller reuses the previous decision until the difficulty's
        reaction delay has elapsed. This makes easy CPUs visibly slower while
        hard CPUs react almost every frame.
        """
        now = pygame.time.get_ticks()
        if now - self.last_decision_ms < self.profile["delay_ms"]:
            return self.current_decision.copy()

        self.last_decision_ms = now
        if self.difficulty == "hard":
            self.current_decision = self._decide_hard()
        else:
            self.current_decision = self._decide_basic()

        return self.current_decision.copy()

    def _decide_basic(self):
        """Decide movement using direct ball position for easy and medium."""
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

    def _decide_hard(self):
        """Decide movement using predicted ball impact and defensive position."""
        decision = self._empty_decision()
        target_x = self._predict_ball_impact_x()
        player_x, player_y = self.player.rect.center

        own_goal_x = WIDTH if self.player.rect.centerx > WIDTH // 2 else 0
        defensive_x = (target_x * 0.7) + (own_goal_x * 0.3)
        margin = self.profile["target_margin"]

        if defensive_x < player_x - margin:
            decision["left"] = True
        elif defensive_x > player_x + margin:
            decision["right"] = True

        ball_x, ball_y = self.ball.rect.center
        ball_is_high = ball_y < player_y - 45
        ball_is_close = abs(ball_x - player_x) < KICK_RANGE * 1.8
        decision["jump"] = ball_is_high and ball_is_close and self.player.on_ground
        decision["kick"] = self._ball_in_kick_range()

        return decision

    def _predict_ball_impact_x(self):
        """Estimate where the ball will be near ground level using gravity."""
        x = float(self.ball.rect.centerx)
        y = float(self.ball.rect.centery)
        vel_x = float(self.ball.vel_x)
        vel_y = float(self.ball.vel_y)

        for _ in range(self.profile["prediction_steps"]):
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
        distance = math.hypot(ball_x - player_x, ball_y - player_y)
        return distance < KICK_RANGE

    def _empty_decision(self):
        """Return a neutral decision with no simulated key pressed."""
        return {
            "left": False,
            "right": False,
            "jump": False,
            "kick": False,
        }
