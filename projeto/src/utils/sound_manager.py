"""Audio manager for Head Soccer DesSoft.

Expected file layout inside assets/sounds/:

  sfx/
    kick.wav      — ball-kick impact sound
    goal.wav      — goal-scored celebration jingle
    whistle.wav   — referee whistle that plays together with goal
    jump.wav      — player leaves the ground
    bounce.wav    — ball bounces on the ground (significant impact only)
    powerup.wav   — any power-up is collected
    crowd.wav     — crowd cheer (trigger manually via play_sfx("crowd"))

  music/
    menu.wav          — main-menu background music loop
    gameplay.wav      — default in-match music loop
    stadium_<name>.wav — optional per-stadium track; <name> must match the
                         'music_name' value in the stadium data dict passed to
                         GameplayScene (e.g. music_name='beach' → stadium_beach.wav)

All SFX are loaded once at start-up through AssetLoader.load_sound(), which
silently returns a no-op object when a file is missing. Background music uses
pygame.mixer.music streaming; missing tracks are skipped with a console warning
so the game never crashes because of absent audio files.
"""

import os

import pygame

from src.utils.asset_loader import AssetLoader


_SFX_DIR = os.path.join("assets", "sounds", "sfx")
_MUSIC_DIR = os.path.join("assets", "sounds", "music")

_SFX_FILES: dict[str, str] = {
    "kick":    "kick.wav",
    "goal":    "goal.wav",
    "whistle": "whistle.wav",
    "jump":    "jump.wav",
    "bounce":  "bounce.wav",
    "powerup": "powerup.wav",
    "crowd":   "crowd.wav",
}

_MUSIC_FILES: dict[str, str] = {
    "menu":     "menu.wav",
    "gameplay": "gameplay.wav",
}

# Chave: name.lower() do personagem (conforme definido em character_select.py)
_GOAL_CELEBRATION_FILES: dict[str, str] = {
    "veloz":       "goal_veloz.mp3",
    "saltador":    "goal_pulador.mp3",
    "equilibrado": "gol_equilibrado.mp3",
    "tanque":      "gol_tanque.mp3",
}


class SoundManager:
    """Loads and plays all game audio.

    Attach one instance to the Game object as ``game.sounds`` so every scene
    can trigger audio via ``self.game.sounds.play_sfx("kick")`` without
    importing this module directly.

    SFX are eagerly loaded in ``__init__`` and played as one-shot channels.
    Background music is streamed by pygame.mixer.music; only one track plays
    at a time and switching tracks stops the previous one automatically.
    """

    def __init__(self) -> None:
        """Load all SFX files and build the music path registry."""
        self._sfx: dict = {}
        self._music_paths: dict[str, str] = {}
        self._sfx_volume: float = 0.7
        self._music_volume: float = 0.5
        self._current_music: str | None = None

        self._load_sfx()
        self._load_music_paths()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play_sfx(self, name: str) -> None:
        """Play a sound effect by name.

        Args:
            name: One of 'kick', 'goal', 'whistle', 'jump', 'bounce',
                'powerup', or 'crowd'. Unknown names are silently ignored.
        """
        sound = self._sfx.get(name)
        if sound is not None:
            sound.play()

    def play_music(self, name: str, loop: bool = True) -> None:
        """Start background music by track name.

        Args:
            name: Track key such as 'menu', 'gameplay', or a stadium-specific
                name previously registered via register_stadium_music(). If
                the track is already playing it is not restarted.
            loop: When True the track repeats indefinitely. When False it
                plays once and stops.

        Missing or unregistered track names are silently ignored — the game
        continues running without music rather than raising an exception.
        """
        if name == self._current_music:
            return

        path = self._music_paths.get(name)
        if path is None or not os.path.isfile(path):
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self._current_music = name
        except pygame.error as exc:
            print(f"[SoundManager] falha ao tocar música '{name}': {exc}")

    def stop_music(self) -> None:
        """Stop any currently playing background music."""
        pygame.mixer.music.stop()
        self._current_music = None

    def set_volume(self, sfx_volume: float, music_volume: float) -> None:
        """Adjust SFX and music volume globally.

        Args:
            sfx_volume: Float in [0.0, 1.0] applied to every loaded SFX.
            music_volume: Float in [0.0, 1.0] applied to the music stream.

        Clamps both values to the valid range so callers can pass raw slider
        values without additional validation.
        """
        self._sfx_volume = max(0.0, min(1.0, sfx_volume))
        self._music_volume = max(0.0, min(1.0, music_volume))

        for sound in self._sfx.values():
            sound.set_volume(self._sfx_volume)

        pygame.mixer.music.set_volume(self._music_volume)

    def play_goal_celebration(self, character_name: str) -> None:
        """Para a música atual e toca o som de gol do personagem via streaming.

        Args:
            character_name: Valor de ``character['name']`` (ex.: 'Veloz').
                Se não existir mapeamento ou arquivo, cai no sfx genérico 'goal'.
        """
        filename = _GOAL_CELEBRATION_FILES.get(character_name.lower())
        if filename:
            path = os.path.join(_SFX_DIR, filename)
            if os.path.isfile(path):
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(self._music_volume)
                    pygame.mixer.music.play(0)
                    self._current_music = "__celebration__"
                    return
                except pygame.error as exc:
                    print(f"[SoundManager] falha ao tocar celebração '{character_name}': {exc}")

        # Fallback: sfx genérico
        self.play_sfx("goal")

    def register_stadium_music(self, name: str, path: str) -> None:
        """Register an additional music file under a given track name.

        Args:
            name: Arbitrary key to use with play_music(), e.g. 'beach'.
            path: Filesystem path to the .ogg/.mp3/.wav music file.

        Useful when stadium data is loaded dynamically and track names are
        not known at SoundManager construction time.
        """
        self._music_paths[name] = path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_sfx(self) -> None:
        """Load every SFX entry via AssetLoader (silent fallback on error)."""
        for name, filename in _SFX_FILES.items():
            path = os.path.join(_SFX_DIR, filename)
            sound = AssetLoader.load_sound(path)
            sound.set_volume(self._sfx_volume)
            self._sfx[name] = sound

    def _load_music_paths(self) -> None:
        """Populate the music path registry from the known track table."""
        for name, filename in _MUSIC_FILES.items():
            self._music_paths[name] = os.path.join(_MUSIC_DIR, filename)
