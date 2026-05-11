"""Reusable sprite animation helper.

Example:
    animation = Animation(idle_frames, frame_duration_ms=120)
    animation.update()
    surface.blit(animation.get_current_frame(), player_rect)
"""

import pygame


class Animation:
    """Controls frame timing for a list of pygame Surfaces."""

    def __init__(self, frames, frame_duration_ms=100, loop=True):
        """Create an animation from a sequence of frames.

        Args:
            frames: List of pygame.Surface objects shown in order.
            frame_duration_ms: Time, in milliseconds, each frame stays visible.
            loop: If True, restart at frame 0 after the last frame. If False,
                stop at the final frame and mark the animation as finished.
        """
        if not frames:
            raise ValueError("Animation requires at least one frame.")

        self.frames = frames
        self.frame_duration_ms = frame_duration_ms
        self.loop = loop
        self.current_frame = 0
        self.last_update_ms = pygame.time.get_ticks()
        self.finished = False

    def update(self):
        """Advance the animation frame when enough time has passed."""
        if self.finished:
            return

        now = pygame.time.get_ticks()
        if now - self.last_update_ms < self.frame_duration_ms:
            return

        self.last_update_ms = now
        self.current_frame += 1

        if self.current_frame >= len(self.frames):
            if self.loop:
                self.current_frame = 0
            else:
                self.current_frame = len(self.frames) - 1
                self.finished = True

    def get_current_frame(self):
        """Return the pygame.Surface for the current animation frame."""
        return self.frames[self.current_frame]

    def reset(self):
        """Restart the animation from the first frame."""
        self.current_frame = 0
        self.last_update_ms = pygame.time.get_ticks()
        self.finished = False
