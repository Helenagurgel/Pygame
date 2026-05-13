"""Ball entity with gravity, bouncing, friction, and visual rotation."""

import pygame

from src.settings import BALL_BOUNCE, BALL_BOUNCE_SOUND_MIN_VEL, BALL_FRICTION, BALL_RADIUS, GRAVITY


KICK_OFFSET = 4
ROTATION_SPEED = 4


class Ball(pygame.sprite.Sprite):
    """Soccer ball sprite controlled by simple arcade physics."""

    def __init__(self, x, y, image):
        """Create a ball centered at the given position.

        Args:
            x: Initial horizontal center position.
            y: Initial vertical center position.
            image: pygame.Surface used as the ball sprite. It is scaled to
                BALL_RADIUS * 2 in both dimensions and stored as the base
                image for future visual rotations.

        The ball starts stopped, creates a rect centered on (x, y), builds a
        mask for pixel-perfect collisions, and initializes its visual rotation
        angle at zero degrees.
        """
        super().__init__()
        diameter = BALL_RADIUS * 2
        self._base_image = pygame.transform.scale(image, (diameter, diameter))
        self.original_image = self._base_image
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

        self.vel_x = 0
        self.vel_y = 0
        self.angle = 0
        self.kick_mult = 1.0
        self.on_fire = False
        self.just_bounced = False
        self.size_mult = 1.0

    def update(self, dt, ground_y, screen_width, gravity_mult=1.0):
        """Update the ball physics and rotated image.

        Args:
            dt: Time elapsed since the last frame, in seconds. The current
                physics constants are frame-based, so dt is accepted for scene
                consistency and future tuning.
            ground_y: Y coordinate of the ground. If the ball goes below this
                line, it is placed back on the ground and bounces.
            screen_width: Width of the playable screen, used for side-wall
                collisions.
            gravity_mult: Multiplier for gravity. Values below 1.0 create
                lighter stadiums, such as a moon stadium with 0.4 gravity.

        Gravity changes vertical velocity every frame, positions are integrated
        into the rect, ground contact inverts vertical velocity with
        BALL_BOUNCE, horizontal movement loses speed through BALL_FRICTION,
        and side walls invert horizontal velocity. The sprite is then rotated
        based on horizontal velocity while preserving rect.center.
        """
        self.vel_y += GRAVITY * gravity_mult

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        self.just_bounced = False
        if self.rect.bottom > ground_y:
            self.rect.bottom = ground_y
            self.just_bounced = abs(self.vel_y) > BALL_BOUNCE_SOUND_MIN_VEL
            self.vel_y *= -BALL_BOUNCE
            self.vel_x *= BALL_FRICTION

        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x *= -BALL_BOUNCE
        elif self.rect.right > screen_width:
            self.rect.right = screen_width
            self.vel_x *= -BALL_BOUNCE

        self._rotate_from_velocity()

    def kick(self, vel_x, vel_y):
        """Set the ball velocity after a player kick.

        Args:
            vel_x: Horizontal kick velocity.
            vel_y: Vertical kick velocity.

        The velocities are assigned directly. A small position offset in the
        kick direction is also applied so the ball does not remain visually or
        physically stuck to the player immediately after contact.
        """
        self.vel_x = vel_x
        self.vel_y = vel_y

        if vel_x > 0:
            self.rect.x += KICK_OFFSET
        elif vel_x < 0:
            self.rect.x -= KICK_OFFSET

        if vel_y > 0:
            self.rect.y += KICK_OFFSET
        elif vel_y < 0:
            self.rect.y -= KICK_OFFSET

    def set_size_mult(self, mult: float) -> None:
        """Resize the ball to *mult* times the default radius, preserving center."""
        center = self.rect.center
        self.size_mult = mult
        new_d = max(4, int(BALL_RADIUS * 2 * mult))
        self.original_image = pygame.transform.scale(self._base_image, (new_d, new_d))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def reset(self, x, y):
        """Stop the ball and move it back to a centered position.

        Args:
            x: New horizontal center position, commonly the middle of the field.
            y: New vertical center position, commonly the kickoff height.

        This method is intended for post-goal resets. It clears velocities,
        restores the visual angle, and rebuilds the image, rect, and mask in a
        consistent stopped state.
        """
        self.vel_x = 0
        self.vel_y = 0
        self.angle = 0
        self.kick_mult = 1.0
        self.on_fire = False
        self.just_bounced = False
        self.size_mult = 1.0
        self.original_image = self._base_image
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

    def _rotate_from_velocity(self):
        """Rotate the visual ball image according to horizontal speed."""
        center = self.rect.center
        self.angle = (self.angle - self.vel_x * ROTATION_SPEED) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)
