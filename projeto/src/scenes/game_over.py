"""Tela de fim de jogo — exibida quando o cronometro da partida chega a zero.

Mostra o placar final, o vencedor (ou empate) e opcoes para jogar
novamente, voltar ao menu ou sair.
"""

import pygame

from src.scenes.base_scene import Scene
from src.settings import BLACK, GRAY, HEIGHT, WHITE, WIDTH, YELLOW
from src.utils.asset_loader import AssetLoader

_OPTIONS = ['Jogar Novamente', 'Voltar ao Menu', 'Sair']
_OPTION_SPACING = 56

_TITLE_FINAL_Y = 90
_TITLE_START_Y = -110


class GameOverScene(Scene):
    """Tela de resultado com animacao de entrada e menu de opcoes.

    Determina o vencedor a partir do placar e anima o titulo "FIM DE JOGO"
    descendo de fora da tela ate sua posicao final.
    """

    def __init__(
        self,
        game,
        score_p1: int,
        score_p2: int,
        char_p1: dict,
        char_p2: dict,
    ):
        """Inicializa o resultado, as fontes e a animacao de entrada.

        Args:
            game: Instancia principal do jogo.
            score_p1: Gols marcados pelo jogador 1.
            score_p2: Gols marcados pelo jogador 2.
            char_p1: Dicionario do personagem do jogador 1 (chave 'name').
            char_p2: Dicionario do personagem do jogador 2 (chave 'name').
        """
        super().__init__(game)
        self._bg = AssetLoader.load_image("assets/images/ui/Fundo Padrão.png", scale=(WIDTH, HEIGHT))
        self.score_p1 = score_p1
        self.score_p2 = score_p2
        self.char_p1 = char_p1
        self.char_p2 = char_p2

        if score_p1 > score_p2:
            self.winner_text = f"Vencedor: {char_p1['name']}"
        elif score_p2 > score_p1:
            self.winner_text = f"Vencedor: {char_p2['name']}"
        else:
            self.winner_text = "EMPATE!"

        self.selected_index = 0
        self.entry_anim_t = 0.0

        self.font_title = AssetLoader.load_font(None, 96)
        self.font_score = AssetLoader.load_font(None, 72)
        self.font_winner = AssetLoader.load_font(None, 48)
        self.font_option = AssetLoader.load_font(None, 40)

    def handle_events(self, events):
        """Navega entre as opcoes e executa a acao selecionada.

        Args:
            events: Lista de pygame.Event do frame atual.
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(_OPTIONS)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(_OPTIONS)
            elif event.key == pygame.K_RETURN:
                self._confirm()

    def _confirm(self):
        """Executa a acao da opcao selecionada."""
        option = _OPTIONS[self.selected_index]
        if option == 'Jogar Novamente':
            self._rematch()
        elif option == 'Voltar ao Menu':
            from src.scenes.menu import MenuScene
            self.game.change_scene(MenuScene(self.game))
        else:
            self.game.quit()

    def _rematch(self):
        """Recria GameplayScene com os mesmos parametros de game.config."""
        from src.scenes.gameplay import GameplayScene

        cfg = getattr(self.game, 'config', {})
        self.game.change_scene(
            GameplayScene(
                self.game,
                cfg.get('mode', '2P'),
                self.char_p1,
                self.char_p2,
                cfg.get('stadium'),
                difficulty=cfg.get('difficulty'),
            )
        )

    def update(self, dt):
        """Avanca a animacao de entrada do titulo.

        Args:
            dt: Tempo em segundos desde o ultimo frame.
        """
        self.entry_anim_t = min(1.0, self.entry_anim_t + dt * 2)

    def draw(self, surface):
        """Desenha o resultado, o placar, o vencedor e as opcoes.

        Args:
            surface: pygame.Surface onde a cena sera renderizada.
        """
        self._draw_background(surface)

        title_y = int(_TITLE_START_Y + (_TITLE_FINAL_Y - _TITLE_START_Y) * self.entry_anim_t)
        title_surf = self.font_title.render("FIM DE JOGO", True, WHITE)
        surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, title_y)))

        score_text = f"{self.score_p1}    -    {self.score_p2}"
        score_surf = self.font_score.render(score_text, True, WHITE)
        surface.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 255)))

        winner_surf = self.font_winner.render(self.winner_text, True, YELLOW)
        surface.blit(winner_surf, winner_surf.get_rect(center=(WIDTH // 2, 345)))

        options_top = 455
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

    def _draw_background(self, surface):
        surface.blit(self._bg, (0, 0))
