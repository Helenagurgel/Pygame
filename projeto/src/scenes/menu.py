"""Main menu scene for Head Soccer DesSoft."""

import pygame

from src.scenes.base_scene import Scene
from src.settings import BLACK, BLUE, HEIGHT, RED, WHITE, WIDTH


class MenuScene(Scene):
    """Interactive main menu with keyboard and mouse navigation."""

    def __init__(self, game):
        """Create menu fonts, options, and initial selection state."""
        super().__init__(game)
        self.title_font = pygame.font.Font(None, 84)
        self.option_font = pygame.font.Font(None, 48)
        self.options = [
            ("1 Jogador", "single_player"),
            ("2 Jogadores", "two_players"),
            ("Instruções", "instructions"),
            ("Sair", "exit"),
        ]
        self.selected_index = 0
        self.option_rects = []
        self.game.sounds.play_music("menu")

    def handle_events(self, events):
        """Process keyboard and mouse input for the menu."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    self._confirm_selection()

            elif event.type == pygame.MOUSEMOTION:
                self._select_option_at(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._select_option_at(event.pos):
                    self._confirm_selection()

    def update(self, dt):
        """Keep the menu state updated.

        The current menu has no animations yet, but the method is kept to
        satisfy the common scene interface.
        """

    def draw(self, surface):
        """Draw the menu background, title, and selectable options."""
        self._draw_background(surface)

        title = self.title_font.render("HEAD SOCCER DESSOFT", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        surface.blit(title, title_rect)

        self.option_rects = []
        first_option_y = HEIGHT // 2 - 40
        spacing = 64

        for index, (label, _) in enumerate(self.options):
            is_selected = index == self.selected_index
            color = RED if is_selected else WHITE
            option_text = self.option_font.render(label, True, color)
            option_rect = option_text.get_rect(
                center=(WIDTH // 2, first_option_y + index * spacing)
            )
            self.option_rects.append(option_rect)

            if is_selected:
                arrow = self.option_font.render(">", True, RED)
                arrow_rect = arrow.get_rect(
                    midright=(option_rect.left - 24, option_rect.centery)
                )
                surface.blit(arrow, arrow_rect)

            surface.blit(option_text, option_rect)

    def _confirm_selection(self):
        """Run the action associated with the selected menu option."""
        _, action = self.options[self.selected_index]
        if action in ("single_player", "two_players"):
            from src.scenes.character_select import CharacterSelectScene
            if not hasattr(self.game, "config"):
                self.game.config = {}
            self.game.config["mode"] = "1P" if action == "single_player" else "2P"
            self.game.change_scene(CharacterSelectScene(self.game))
        elif action == "instructions":
            from src.scenes.instructions import InstructionsScene
            self.game.change_scene(InstructionsScene(self.game))
        else:
            self.game.change_scene(action)

    def _select_option_at(self, position):
        """Select the option under the cursor, if there is one."""
        for index, rect in enumerate(self.option_rects):
            if rect.collidepoint(position):
                self.selected_index = index
                return True

        return False

    def _draw_background(self, surface):
        """Draw a simple vertical gradient background."""
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            red = int(BLUE[0] * (1 - ratio) + BLACK[0] * ratio)
            green = int(BLUE[1] * (1 - ratio) + BLACK[1] * ratio)
            blue = int(BLUE[2] * (1 - ratio) + BLACK[2] * ratio)
            pygame.draw.line(surface, (red, green, blue), (0, y), (WIDTH, y))
