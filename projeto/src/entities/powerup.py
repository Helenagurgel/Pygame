"""Power-up entities, active-effect helpers and spawner for Head Soccer DesSoft."""

import math
import random
from abc import ABC, abstractmethod

import pygame

from src.settings import GROUND_Y, WIDTH


_SPAWN_INTERVAL_MS = 10_000
_FLOAT_AMPLITUDE = 8    # pixels of vertical oscillation
_FLOAT_SPEED = 2.0      # radians per second
_ICON_RADIUS = 40
_SPAWN_X_MARGIN = 150
_SPAWN_Y_MIN = int(GROUND_Y * 0.40)
_SPAWN_Y_MAX = int(GROUND_Y * 0.70)


class PowerUp(pygame.sprite.Sprite, ABC):
    """Abstract collectible power-up that floats on the field.

    Sub-classes must define ``duration_ms``, ``name``, ``apply`` and
    ``expire``. While on the field the sprite oscillates vertically with a
    sine wave. Once collected the sprite is killed from the field group;
    effect timing is managed externally by the scene via ``_powerup_effects``.
    """

    duration_ms: int = 5_000
    name: str = "PowerUp"

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self._base_y = float(y)
        self._float_time = 0.0
        self.icon = self._create_icon()
        self.image = self.icon
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt: float) -> None:
        """Animate vertical floating using a sine wave."""
        self._float_time += dt
        offset = math.sin(self._float_time * _FLOAT_SPEED) * _FLOAT_AMPLITUDE
        self.rect.centery = int(self._base_y + offset)

    @abstractmethod
    def apply(self, target) -> None:
        """Apply this power-up's effect to *target*."""

    @abstractmethod
    def expire(self, target) -> None:
        """Remove this power-up's effect from *target*."""

    @abstractmethod
    def _create_icon(self) -> pygame.Surface:
        """Return the icon surface drawn on the field."""


# ---------------------------------------------------------------------------
# Concrete power-ups
# ---------------------------------------------------------------------------

class FireBall(PowerUp):
    """Ignites the ball for 5 s — kicks become 1.5× stronger.

    Collected by the *ball* (not a player). Sets ``ball.kick_mult = 1.5`` and
    ``ball.on_fire = True`` so the scene can emit fire particles and scale kick
    vectors accordingly. On expiry both attributes are restored to their
    defaults.
    """

    duration_ms = 5_000
    name = "FireBall"

    def _create_icon(self) -> pygame.Surface:
        size = _ICON_RADIUS * 2
        try:
            img = pygame.image.load("assets/images/powerups/FireBall.png").convert_alpha()
            return pygame.transform.scale(img, (size, size))
        except (pygame.error, FileNotFoundError, OSError):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (220, 80, 0), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS)
            pygame.draw.circle(surf, (255, 200, 50), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS - 7)
            for i in range(6):
                angle = math.radians(i * 60)
                cx = _ICON_RADIUS + math.cos(angle) * (_ICON_RADIUS - 9)
                cy = _ICON_RADIUS + math.sin(angle) * (_ICON_RADIUS - 9)
                pygame.draw.circle(surf, (255, 60, 0), (int(cx), int(cy)), 4)
            return surf

    def apply(self, target) -> None:
        """Set kick multiplier and fire flag on the ball."""
        target.kick_mult = 1.5
        target.on_fire = True

    def expire(self, target) -> None:
        """Restore the ball to its normal kick force."""
        target.kick_mult = 1.0
        target.on_fire = False


class GiantPlayer(PowerUp):
    """Doubles the collecting player's visual and collision size for 6 s.

    Sets ``player.size_mult = 2.0`` so the sprite and hitbox grow to twice
    their normal dimensions. On expiry ``size_mult`` is restored to ``1.0``
    and the rect resizes back to normal on the next physics frame.
    """

    duration_ms = 5_000
    name = "GiantPlayer"

    def _create_icon(self) -> pygame.Surface:
        size = _ICON_RADIUS * 2
        try:
            img = pygame.image.load("assets/images/powerups/BigPlayer.png").convert_alpha()
            return pygame.transform.scale(img, (size, size))
        except (pygame.error, FileNotFoundError, OSError):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (50, 200, 80), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS)
            cx, cy = _ICON_RADIUS, _ICON_RADIUS
            pygame.draw.polygon(surf, (255, 255, 255), [
                (cx, cy - 14), (cx - 9, cy - 3), (cx + 9, cy - 3),
            ])
            pygame.draw.rect(surf, (255, 255, 255), pygame.Rect(cx - 4, cy - 3, 8, 13))
            return surf

    def apply(self, target) -> None:
        """Double the player's size multiplier."""
        target.size_mult = 2.0

    def expire(self, target) -> None:
        """Restore the player's normal size."""
        target.size_mult = 1.0


class Freeze(PowerUp):
    """Freezes the *opponent* for 2 s — prevents all movement input.

    The scene is responsible for resolving which player is the opponent and
    passing that player as *target*. Sets ``player.frozen = True`` so that
    ``handle_input`` becomes a no-op for the duration. The target can still
    fall under gravity; only voluntary input is blocked.
    """

    duration_ms = 5_000
    name = "Freeze"

    def _create_icon(self) -> pygame.Surface:
        size = _ICON_RADIUS * 2
        try:
            img = pygame.image.load("assets/images/powerups/Freeze.png").convert_alpha()
            return pygame.transform.scale(img, (size, size))
        except (pygame.error, FileNotFoundError, OSError):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (100, 180, 255), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS)
            cx, cy = _ICON_RADIUS, _ICON_RADIUS
            for angle in range(0, 180, 60):
                rad = math.radians(angle)
                x1 = cx + math.cos(rad) * (_ICON_RADIUS - 4)
                y1 = cy + math.sin(rad) * (_ICON_RADIUS - 4)
                x2 = cx - math.cos(rad) * (_ICON_RADIUS - 4)
                y2 = cy - math.sin(rad) * (_ICON_RADIUS - 4)
                pygame.draw.line(surf, (220, 240, 255), (int(x1), int(y1)), (int(x2), int(y2)), 3)
            pygame.draw.circle(surf, (220, 240, 255), (cx, cy), 5)
            return surf

    def apply(self, target) -> None:
        """Freeze the opponent player."""
        target.frozen = True

    def expire(self, target) -> None:
        """Unfreeze the opponent player."""
        target.frozen = False


class LowGravity(PowerUp):
    """Reduces scene gravity for all entities for 4 s.

    The *target* is the ``GameplayScene`` instance. Stores the original
    ``gravity_mult`` value so it can be restored precisely on expiry even
    when the stadium already has a custom gravity modifier.
    """

    duration_ms = 5_000
    name = "LowGravity"

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self._original_gravity: float = 1.0

    def _create_icon(self) -> pygame.Surface:
        size = _ICON_RADIUS * 2
        try:
            img = pygame.image.load("assets/images/powerups/Low_Gravity.png").convert_alpha()
            return pygame.transform.scale(img, (size, size))
        except (pygame.error, FileNotFoundError, OSError):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (180, 120, 255), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS)
            cx, cy = _ICON_RADIUS, _ICON_RADIUS
            for off in (-6, 6):
                pygame.draw.polygon(surf, (255, 255, 255), [
                    (cx + off, cy - 12),
                    (cx + off - 5, cy - 4),
                    (cx + off + 5, cy - 4),
                ])
                pygame.draw.rect(surf, (255, 255, 255), pygame.Rect(cx + off - 2, cy - 4, 5, 11))
            return surf

    def apply(self, target) -> None:
        """Reduce the scene gravity to 30 % of its current value."""
        self._original_gravity = target.gravity_mult
        target.gravity_mult = max(0.1, target.gravity_mult * 0.3)

    def expire(self, target) -> None:
        """Restore the scene's original gravity multiplier."""
        target.gravity_mult = self._original_gravity


class BigBall(PowerUp):
    """Doubles the ball's radius for 6 s — harder to dodge, easier to hit.

    Calls ``ball.set_size_mult(2.0)`` on apply and restores it to ``1.0`` on
    expiry so the ball returns to its original dimensions.
    """

    duration_ms = 6_000
    name = "BigBall"

    def _create_icon(self) -> pygame.Surface:
        size = _ICON_RADIUS * 2
        try:
            img = pygame.image.load("assets/images/powerups/BigBall.png").convert_alpha()
            return pygame.transform.scale(img, (size, size))
        except (pygame.error, FileNotFoundError, OSError):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (230, 100, 20), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS)
            pygame.draw.circle(surf, (255, 255, 255), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS - 6)
            pygame.draw.circle(surf, (40, 40, 40), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS - 6, 2)
            cx, cy = _ICON_RADIUS, _ICON_RADIUS
            for angle, dx, dy in [(90, 0, -1), (270, 0, 1), (0, 1, 0), (180, -1, 0)]:
                tip_x = cx + dx * (_ICON_RADIUS - 1)
                tip_y = cy + dy * (_ICON_RADIUS - 1)
                pygame.draw.polygon(surf, (230, 100, 20), [
                    (tip_x, tip_y),
                    (tip_x - dy * 4 - dx * 5, tip_y - dx * 4 - dy * 5),
                    (tip_x + dy * 4 - dx * 5, tip_y + dx * 4 - dy * 5),
                ])
            return surf

    def apply(self, target) -> None:
        """Double the ball's size."""
        target.set_size_mult(2.0)

    def expire(self, target) -> None:
        """Restore the ball to its normal size."""
        target.set_size_mult(1.0)


class SmallBall(PowerUp):
    """Halves the ball's radius for 6 s — harder to hit, easier to dodge.

    Calls ``ball.set_size_mult(0.5)`` on apply and restores it to ``1.0`` on
    expiry so the ball returns to its original dimensions.
    """

    duration_ms = 6_000
    name = "SmallBall"

    def _create_icon(self) -> pygame.Surface:
        size = _ICON_RADIUS * 2
        try:
            img = pygame.image.load("assets/images/powerups/SmallBall.png").convert_alpha()
            return pygame.transform.scale(img, (size, size))
        except (pygame.error, FileNotFoundError, OSError):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (20, 180, 200), (_ICON_RADIUS, _ICON_RADIUS), _ICON_RADIUS)
            pygame.draw.circle(surf, (255, 255, 255), (_ICON_RADIUS, _ICON_RADIUS), (_ICON_RADIUS - 6) // 2)
            pygame.draw.circle(surf, (40, 40, 40), (_ICON_RADIUS, _ICON_RADIUS), (_ICON_RADIUS - 6) // 2, 2)
            cx, cy = _ICON_RADIUS, _ICON_RADIUS
            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                outer_x = cx + dx * (_ICON_RADIUS - 2)
                outer_y = cy + dy * (_ICON_RADIUS - 2)
                inner_x = cx + dx * ((_ICON_RADIUS - 6) // 2 + 4)
                inner_y = cy + dy * ((_ICON_RADIUS - 6) // 2 + 4)
                pygame.draw.line(surf, (20, 180, 200), (outer_x, outer_y), (inner_x, inner_y), 3)
                pygame.draw.polygon(surf, (20, 180, 200), [
                    (inner_x, inner_y),
                    (inner_x - dy * 3 + dx * 4, inner_y - dx * 3 + dy * 4),
                    (inner_x + dy * 3 + dx * 4, inner_y + dx * 3 + dy * 4),
                ])
            return surf

    def apply(self, target) -> None:
        """Halve the ball's size."""
        target.set_size_mult(0.5)

    def expire(self, target) -> None:
        """Restore the ball to its normal size."""
        target.set_size_mult(1.0)


# ---------------------------------------------------------------------------
# Spawner
# ---------------------------------------------------------------------------

_POWERUP_CLASSES = [FireBall, GiantPlayer, Freeze, LowGravity, BigBall, SmallBall]


class PowerUpSpawner:
    """Spawns a random power-up every 10–15 s in the middle zone of the field.

    Each spawn picks a random X within the horizontal safe margin and a random
    Y between 40 % and 70 % of ``GROUND_Y`` so power-ups always appear in
    reachable air space. At most one of each type should be on the field at
    once; this constraint is enforced by the scene's collision handler.
    """

    def __init__(self, group: pygame.sprite.Group) -> None:
        """Attach the spawner to *group* where new sprites will be added."""
        self._group = group
        self._timer_ms = self._next_interval()

    def update(self, dt: float) -> None:
        """Tick the spawn timer and emit a new power-up when it reaches zero."""
        self._timer_ms -= dt * 1000
        if self._timer_ms <= 0:
            self._spawn()
            self._timer_ms = self._next_interval()

    def reset(self) -> None:
        """Clear all field power-ups and restart the spawn timer."""
        self._group.empty()
        self._timer_ms = self._next_interval()

    def _spawn(self) -> None:
        x = random.randint(_SPAWN_X_MARGIN, WIDTH - _SPAWN_X_MARGIN)
        y = random.randint(_SPAWN_Y_MIN, _SPAWN_Y_MAX)
        cls = random.choice(_POWERUP_CLASSES)
        self._group.add(cls(x, y))

    @staticmethod
    def _next_interval() -> float:
        return _SPAWN_INTERVAL_MS
