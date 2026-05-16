"""Base classes for all game scenes."""

from abc import ABC, abstractmethod


def blit_outlined(surface, font, text, color, center, outline=(0, 0, 0), px=2):
    """Render text centered at `center` with a solid pixel outline for readability over any background."""
    txt = font.render(text, True, color)
    shd = font.render(text, True, outline)
    cx, cy = center
    for dx, dy in ((-px, 0), (px, 0), (0, -px), (0, px),
                   (-px, -px), (px, -px), (-px, px), (px, px)):
        surface.blit(shd, shd.get_rect(center=(cx + dx, cy + dy)))
    rect = txt.get_rect(center=center)
    surface.blit(txt, rect)
    return rect


class Scene(ABC):
    """Abstract interface shared by every scene in the game."""

    def __init__(self, game):
        """Store the main game object so scenes can request transitions."""
        self.game = game

    @abstractmethod
    def handle_events(self, events):
        """Handle pygame events received during the current frame."""
        raise NotImplementedError

    @abstractmethod
    def update(self, dt):
        """Update the scene state.

        Args:
            dt: Time elapsed since the previous frame, in seconds.
        """
        raise NotImplementedError

    @abstractmethod
    def draw(self, surface):
        """Draw the scene onto the provided surface."""
        raise NotImplementedError
