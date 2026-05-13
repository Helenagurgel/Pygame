"""Player entity with movement, jumping, kicking, and sprite animation."""

import math

import pygame

from src.settings import (
    GRAVITY,
    KICK_FORCE,
    KICK_RANGE,
    JUMP_VELOCITY,
    PLAYER_HEIGHT,
    PLAYER_SPEED,
    PLAYER_WIDTH,
    WIDTH,
)
from src.utils.animation import Animation


KICK_DURATION_FRAMES = 12
ANIMATION_FRAME_DURATION_MS = 100
ANIMATION_STATES = ("idle", "run", "jump", "kick", "celebrate")


class Player(pygame.sprite.Sprite):
    """Controllable head soccer player sprite."""

    def __init__(self, x, y, controls, character_data, facing_right=True):
        """Create a player with controls, character stats, and animations.

        Args:
            x: Initial horizontal position for the player's rect.
            y: Initial vertical position for the player's rect.
            controls: Dict with the keys 'left', 'right', 'jump', and 'kick',
                each mapped to a pygame keyboard constant.
            character_data: Dict describing the selected character. It must
                contain 'name', 'speed_mult', 'jump_mult', and 'sprites'. The
                'sprites' value is another dict containing frame lists for
                'idle', 'run', 'jump', 'kick', and 'celebrate'.
            facing_right: If True, the player starts facing right. If False,
                the current frame is mirrored horizontally when drawn.
        """
        super().__init__()
        self.controls = controls
        self.character_data = character_data
        self.name = character_data["name"]
        self.speed_mult = character_data["speed_mult"]
        self.jump_mult = character_data["jump_mult"]

        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = facing_right
        self.is_kicking = False
        self.kick_timer = 0
        self._kick_applied = False
        self.score = 0
        self.state = "idle"
        self.frozen = False
        self.size_mult = 1.0
        self.just_jumped = False

        self.animations = self._create_animations(character_data["sprites"])
        self.current_animation = self.animations[self.state]
        self.image = self._get_oriented_frame()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

    def handle_input(self, keys):
        """Read pressed keys and update horizontal movement/action state.

        Args:
            keys: The object returned by pygame.key.get_pressed(), usually
                passed by the active scene once per frame.

        The method sets horizontal velocity from the configured left/right
        controls, starts a jump only while the player is on the ground, and
        starts a fixed-duration kick when the kick key is pressed.
        """
        self.just_jumped = False

        if self.frozen:
            self.vel_x = 0
            return

        self.vel_x = 0

        if keys[self.controls["left"]]:
            self.vel_x = -PLAYER_SPEED * self.speed_mult
            self.facing_right = False
        elif keys[self.controls["right"]]:
            self.vel_x = PLAYER_SPEED * self.speed_mult
            self.facing_right = True

        if keys[self.controls["jump"]] and self.on_ground:
            self.vel_y = JUMP_VELOCITY * self.jump_mult
            self.on_ground = False
            self.just_jumped = True

        if keys[self.controls["kick"]] and not self.is_kicking:
            self.is_kicking = True
            self.kick_timer = KICK_DURATION_FRAMES
            self._kick_applied = False

        self._update_state_from_motion()

    def update(self, dt, ground_y):
        """Apply physics, keep the player inside the screen, and animate.

        Args:
            dt: Time elapsed since the last frame, in seconds. The player uses
                per-frame velocities from the project's current physics
                constants, so this argument is accepted for the scene contract
                and future time-based tuning.
            ground_y: Y coordinate of the floor. When rect.bottom reaches this
                value, the player lands and vertical velocity is reset.

        Gravity is applied while airborne, position is integrated into the
        rect, horizontal movement is clamped to the screen borders, and the
        current state's Animation chooses the frame. If the player is facing
        left, the frame is mirrored with pygame.transform.flip.
        """
        if self.kick_timer > 0:
            self.kick_timer -= 1
        else:
            self.is_kicking = False

        if not self.on_ground:
            self.vel_y += GRAVITY * self.speed_mult

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH

        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        self._update_state_from_motion()
        self._set_animation(self.state)
        self.current_animation.update()
        self.image = self._get_oriented_frame()

        if self.size_mult != 1.0:
            orig_bottom = self.rect.bottom
            orig_centerx = self.rect.centerx
            new_w = int(PLAYER_WIDTH * self.size_mult)
            new_h = int(PLAYER_HEIGHT * self.size_mult)
            self.image = pygame.transform.scale(self.image, (new_w, new_h))
            self.rect = self.image.get_rect()
            self.rect.bottom = orig_bottom
            self.rect.centerx = orig_centerx
            if self.rect.left < 0:
                self.rect.left = 0
            elif self.rect.right > WIDTH:
                self.rect.right = WIDTH

        self.mask = pygame.mask.from_surface(self.image)

    def try_kick(self, ball):
        """Return a fixed-force kick vector when the ball is in range.

        Args:
            ball: Ball-like object with a rect attribute, or x/y coordinates,
                used to calculate the direction from the player to the ball.

        Returns:
            A tuple (force_x, force_y) when the player is currently kicking and
            the distance to the ball is smaller than KICK_RANGE. The vector has
            fixed magnitude KICK_FORCE; only its direction changes based on the
            relative position. Returns None when no kick should happen.
        """
        if not self.is_kicking or self._kick_applied:
            return None

        ball_x, ball_y = self._get_ball_center(ball)
        player_x, player_y = self.rect.center
        dx = ball_x - player_x
        dy = ball_y - player_y
        distance = math.hypot(dx, dy)

        if distance == 0 or distance >= KICK_RANGE:
            return None

        direction_x = dx / distance
        direction_y = dy / distance

        # Always kick upward: clamp vertical direction to ≤ 0 (never downward)
        # and add a fixed upward bias so foot-level kicks arc into the air.
        kick_dy = min(direction_y, 0) - 0.5
        kick_len = math.hypot(direction_x, kick_dy)
        norm = kick_len if kick_len > 0 else 1.0
        force_x = (direction_x / norm) * KICK_FORCE
        force_y = (kick_dy / norm) * KICK_FORCE

        self._kick_applied = True
        return (force_x, force_y)

    def _create_animations(self, sprites):
        """Build an Animation object for every expected player state."""
        fallback_frame = self._create_placeholder_frame()
        animations = {}

        for state in ANIMATION_STATES:
            frames = sprites.get(state) or [fallback_frame]
            loop = state != "kick"
            animations[state] = Animation(
                frames,
                frame_duration_ms=ANIMATION_FRAME_DURATION_MS,
                loop=loop,
            )

        return animations

    def _create_placeholder_frame(self):
        """Create a visible temporary frame for characters without sprites."""
        frame = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        frame.fill((255, 0, 255))
        return frame

    def _set_animation(self, state):
        """Switch to a new animation state and reset it when needed."""
        next_animation = self.animations[state]
        if next_animation is not self.current_animation:
            self.current_animation = next_animation
            self.current_animation.reset()

    def _get_oriented_frame(self):
        """Return the current frame, mirrored if the player faces left."""
        frame = self.current_animation.get_current_frame()
        if self.facing_right:
            return frame
        return pygame.transform.flip(frame, True, False)

    def _update_state_from_motion(self):
        """Choose the visual state from kick, jump, run, or idle priority."""
        if self.is_kicking:
            self.state = "kick"
        elif not self.on_ground:
            self.state = "jump"
        elif self.vel_x != 0:
            self.state = "run"
        else:
            self.state = "idle"

    def tick_celebrate(self):
        """Advance the celebration animation by one frame without physics.

        Called once per frame while the scene is in the 'celebrating' state so
        the winning player plays its celebrate animation even though the normal
        physics update loop is paused. Sets state, switches the animation track
        if needed, ticks the frame counter, and rebuilds the oriented image.
        """
        self.state = "celebrate"
        self._set_animation("celebrate")
        self.current_animation.update()
        self.image = self._get_oriented_frame()

    def _get_ball_center(self, ball):
        """Extract the ball center from common ball object shapes."""
        if hasattr(ball, "rect"):
            return ball.rect.center
        if hasattr(ball, "x") and hasattr(ball, "y"):
            return (ball.x, ball.y)
        return ball
