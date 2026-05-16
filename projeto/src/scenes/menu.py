"""Main menu scene for Head Soccer DesSoft."""

import pygame

from src.scenes.base_scene import Scene, blit_outlined
from src.settings import HEIGHT, WHITE, WIDTH, YELLOW

_BG_PATH = "assets/images/ui/Capa.png"

# Posições dos botões na imagem escalada para 1280×720.
# A imagem tem proporção 16:9 igual ao jogo, então o scale é uniforme.
_BTN_CX = WIDTH // 2   # centro horizontal
_BTN_W = 413           # largura do botão
_BTN_H = 54            # altura do botão
_FIRST_Y = 329         # centro Y do primeiro botão
_SPACING = 62          # espaçamento entre centros


class MenuScene(Scene):
    """Interactive main menu with keyboard and mouse navigation."""

    def __init__(self, game):
        """Create menu state and load the background image."""
        super().__init__(game)
        self.options = [
            ("1 Jogador",   "single_player"),
            ("2 Jogadores", "two_players"),
            ("Instruções",  "instructions"),
            ("Sair",        "exit"),
        ]
        self.selected_index = 0
        self.option_rects = self._build_rects()
        self._bg = self._load_background()
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
        pass

    def draw(self, surface):
        """Draw the background image and highlight the selected button."""
        surface.blit(self._bg, (0, 0))

        rect = self.option_rects[self.selected_index]
        tip_x = rect.left - 10
        cy = rect.centery
        size = 14
        shadow_pts = [
            (tip_x + 2, cy + 2),
            (tip_x - size + 2, cy - size // 2 + 2),
            (tip_x - size + 2, cy + size // 2 + 2),
        ]
        arrow_pts = [
            (tip_x, cy),
            (tip_x - size, cy - size // 2),
            (tip_x - size, cy + size // 2),
        ]
        pygame.draw.polygon(surface, (0, 0, 0), shadow_pts)
        pygame.draw.polygon(surface, YELLOW, arrow_pts)

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
        """Select the option under the cursor, if any."""
        for index, rect in enumerate(self.option_rects):
            if rect.collidepoint(position):
                self.selected_index = index
                return True
        return False

    def _build_rects(self):
        """Build the list of clickable rects aligned with the image buttons."""
        rects = []
        for i in range(len(self.options)):
            rect = pygame.Rect(0, 0, _BTN_W, _BTN_H)
            rect.center = (_BTN_CX, _FIRST_Y + i * _SPACING)
            rects.append(rect)
        return rects

    def _load_background(self):
        """Load and scale the cover image, falling back to a solid colour."""
        try:
            img = pygame.image.load(_BG_PATH).convert()
            return pygame.transform.scale(img, (WIDTH, HEIGHT))
        except (pygame.error, FileNotFoundError, OSError):
            surf = pygame.Surface((WIDTH, HEIGHT))
            surf.fill((30, 80, 180))
            return surf
