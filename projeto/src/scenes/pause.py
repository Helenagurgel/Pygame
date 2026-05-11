"""Cena de pausa — overlay semi-transparente sobre a gameplay congelada.

Exibida quando o jogador pressiona ESC durante a partida. Mantém uma
referencia a GameplayScene para retomar exatamente onde parou.
"""

import pygame

from src.scenes.base_scene import Scene
from src.settings import HEIGHT, WHITE, WIDTH, YELLOW
from src.utils.asset_loader import AssetLoader

_OPTIONS = ['Continuar', 'Voltar ao Menu']
_OPTION_SPACING = 62


class PauseScene(Scene):
    """Overlay de pausa renderizado sobre um snapshot da gameplay.

    Captura o frame atual no momento da construcao e o exibe congelado
    por baixo de um escurecimento semi-transparente.
    """

    def __init__(self, game, gameplay_scene):
        """Inicializa o snapshot, as fontes e o estado de selecao.

        Args:
            game: Instancia principal do jogo.
            gameplay_scene: GameplayScene ativa, mantida para retomada.
        """
        super().__init__(game)
        self.gameplay = gameplay_scene
        self.snapshot = game.screen.copy()
        self.selected_index = 0

        self.font_title = AssetLoader.load_font(None, 88)
        self.font_option = AssetLoader.load_font(None, 48)

        self._overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 180))

    def handle_events(self, events):
        """Navega entre as opcoes e executa a acao selecionada.

        Args:
            events: Lista de pygame.Event do frame atual.
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                self.game.change_scene(self.gameplay)
            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(_OPTIONS)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(_OPTIONS)
            elif event.key == pygame.K_RETURN:
                self._confirm()

    def _confirm(self):
        """Executa a acao da opcao atualmente selecionada."""
        if self.selected_index == 0:
            self.game.change_scene(self.gameplay)
        else:
            from src.scenes.menu import MenuScene
            self.game.change_scene(MenuScene(self.game))

    def update(self, dt):
        """Sem atualizacoes — o jogo esta pausado.

        Args:
            dt: Tempo em segundos desde o ultimo frame (ignorado).
        """

    def draw(self, surface):
        """Desenha o snapshot congelado, o overlay e o menu de pausa.

        Args:
            surface: pygame.Surface onde a cena sera renderizada.
        """
        surface.blit(self.snapshot, (0, 0))
        surface.blit(self._overlay, (0, 0))

        title_surf = self.font_title.render("PAUSADO", True, WHITE)
        surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90)))

        options_top = HEIGHT // 2 + 10
        for i, label in enumerate(_OPTIONS):
            is_selected = i == self.selected_index
            color = YELLOW if is_selected else WHITE
            option_surf = self.font_option.render(label, True, color)
            option_rect = option_surf.get_rect(
                center=(WIDTH // 2, options_top + i * _OPTION_SPACING)
            )
            surface.blit(option_surf, option_rect)

            if is_selected:
                arrow_surf = self.font_option.render("▶", True, YELLOW)
                surface.blit(
                    arrow_surf,
                    arrow_surf.get_rect(midright=(option_rect.left - 16, option_rect.centery)),
                )
