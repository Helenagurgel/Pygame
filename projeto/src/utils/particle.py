"""Small particle effects used by gameplay scenes."""

import random

import pygame


class Particle(pygame.sprite.Sprite):
    """A fading and shrinking particle sprite."""

    def __init__(self, x, y, vel_x, vel_y, color, size, lifetime):
        """Create a particle at a position with velocity and lifetime.

        Args:
            x: Initial horizontal center position.
            y: Initial vertical center position.
            vel_x: Horizontal velocity applied on each update.
            vel_y: Vertical velocity applied on each update.
            color: RGB tuple used to draw the particle.
            size: Initial particle radius in pixels.
            lifetime: Duration in milliseconds before the particle disappears.

        The particle stores its initial size and lifetime so it can shrink and
        fade proportionally as it ages. When lifetime reaches zero, the sprite
        removes itself from all groups with kill().
        """
        super().__init__()
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.initial_size = size
        self.size = size
        self.initial_lifetime = lifetime
        self.lifetime = lifetime
        self.image = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self._redraw()

    def update(self, dt):
        """Move, fade, shrink, and remove the particle when expired.

        Args:
            dt: Time elapsed since the previous frame, in seconds.

        Lifetime is measured in milliseconds, while movement uses dt so the
        effect remains reasonably consistent across different frame rates.
        """
        self.lifetime -= dt * 1000

        if self.lifetime <= 0:
            self.kill()
            return

        self.x += self.vel_x * dt
        self.y += self.vel_y * dt

        life_ratio = self.lifetime / self.initial_lifetime
        self.size = max(1, int(self.initial_size * life_ratio))
        self._redraw(alpha=int(255 * life_ratio))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def _redraw(self, alpha=255):
        """Rebuild the particle surface using the current size and alpha."""
        diameter = self.size * 2
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(
            self.image,
            (*self.color, alpha),
            (self.size, self.size),
            self.size,
        )


class ParticleSystem:
    """Manages groups of particles and common gameplay emissions."""

    def __init__(self):
        """Create an empty particle group."""
        self.particles = pygame.sprite.Group()

    def emit_dust(self, x, y, count=5):
        """Emit brown dust particles around a running or landing player.

        Args:
            x: Horizontal origin of the dust cloud.
            y: Vertical origin of the dust cloud.
            count: Number of particles to create.
        """
        for _ in range(count):
            color = random.choice(
                [
                    (120, 83, 45),
                    (145, 102, 58),
                    (170, 130, 80),
                    (190, 160, 110),
                ]
            )
            particle = Particle(
                x + random.randint(-8, 8),
                y + random.randint(-4, 4),
                random.uniform(-50, 50),
                random.uniform(-35, -10),
                color,
                random.randint(3, 7),
                random.randint(250, 500),
            )
            self.particles.add(particle)

    def emit_sparkle(self, x, y, count=8):
        """Emit bright sparkle particles around the ball or a goal.

        Args:
            x: Horizontal origin of the sparkle burst.
            y: Vertical origin of the sparkle burst.
            count: Number of particles to create.
        """
        for _ in range(count):
            color = random.choice(
                [
                    (255, 255, 180),
                    (255, 230, 80),
                    (180, 240, 255),
                    (255, 255, 255),
                ]
            )
            particle = Particle(
                x + random.randint(-6, 6),
                y + random.randint(-6, 6),
                random.uniform(-90, 90),
                random.uniform(-100, 40),
                color,
                random.randint(2, 5),
                random.randint(300, 650),
            )
            self.particles.add(particle)

    def emit_trail(self, x, y, vel_x, vel_y, count=2, color=(200, 200, 230)):
        """Emit short-lived particles that trail behind a fast-moving ball.

        Args:
            x: Horizontal center of the emission point (ball center).
            y: Vertical center of the emission point (ball center).
            vel_x: Current horizontal ball velocity, used to offset the spawn
                point opposite to the direction of motion so the trail appears
                behind the ball rather than inside it.
            vel_y: Current vertical ball velocity, same purpose as vel_x.
            count: Number of trail particles to create each call.
            color: RGB tuple for the trail color. Pass orange (255, 140, 0)
                when the ball is on fire, grey-white otherwise.
        """
        for _ in range(count):
            particle = Particle(
                x + random.uniform(-3, 3) - vel_x * 0.3,
                y + random.uniform(-3, 3) - vel_y * 0.3,
                vel_x * random.uniform(-0.15, 0.05) + random.uniform(-12, 12),
                vel_y * random.uniform(-0.15, 0.05) + random.uniform(-12, 12),
                color,
                random.randint(2, 5),
                random.randint(80, 180),
            )
            self.particles.add(particle)

    def update(self, dt):
        """Update every active particle.

        Args:
            dt: Time elapsed since the previous frame, in seconds.
        """
        self.particles.update(dt)

    def draw(self, surface):
        """Draw all active particles on the target surface.

        Args:
            surface: pygame.Surface where the particles should be rendered.
        """
        self.particles.draw(surface)
