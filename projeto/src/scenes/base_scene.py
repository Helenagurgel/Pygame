"""Base classes for all game scenes."""

from abc import ABC, abstractmethod


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
