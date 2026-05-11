"""Main game object and execution loop for Head Soccer DesSoft."""

import pygame

from src.scenes.base_scene import Scene
from src.scenes.menu import MenuScene
from src.settings import BLACK, FPS, HEIGHT, TITLE, WHITE, WIDTH
from src.utils.sound_manager import SoundManager


class PlaceholderScene(Scene):
    """Temporary scene used while the final game scenes are not implemented."""

    def __init__(self, game, name):
        """Create a placeholder screen for a future scene."""
        super().__init__(game)
        self.name = name
        self.title_font = pygame.font.Font(None, 64)
        self.text_font = pygame.font.Font(None, 36)

    def handle_events(self, events):
        """Return to the menu when ESC is pressed."""
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.change_scene(MenuScene(self.game))

    def update(self, dt):
        """Keep the placeholder scene updated."""

    def draw(self, surface):
        """Draw placeholder text for a scene that will be created later."""
        surface.fill(BLACK)

        title = self.title_font.render(self.name, True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        surface.blit(title, title_rect)

        hint = self.text_font.render("Cena placeholder - pressione ESC", True, WHITE)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        surface.blit(hint, hint_rect)


class Game:
    """Coordinates pygame setup, the active scene, and the main loop."""

    def __init__(self):
        """Initialize pygame, create the window, and load the first scene."""
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.sounds = SoundManager()
        self.scene = MenuScene(self)

    def change_scene(self, new_scene_instance):
        """Change the active scene.

        Args:
            new_scene_instance: A Scene instance, or a temporary placeholder
                scene name while the next scenes are still being implemented.
        """
        if new_scene_instance == "exit":
            self.quit()
        elif isinstance(new_scene_instance, str):
            self.scene = PlaceholderScene(self, new_scene_instance)
        else:
            self.scene = new_scene_instance

    def quit(self):
        """Request the main loop to stop."""
        self.running = False

    def run(self):
        """Run the main game loop until the player closes the game."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.quit()

            self.scene.handle_events(events)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
