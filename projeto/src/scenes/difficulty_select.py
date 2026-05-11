"""Tela de seleção de dificuldade — etapa final antes da partida no modo 1P.

Exibida após StadiumSelectScene apenas quando o modo de jogo é '1P'.
Permite ao jogador escolher o nível do CPU antes de iniciar a partida.
"""

import pygame

from src.scenes.base_scene import Scene
from src.settings import BLACK, GREEN, HEIGHT, WHITE, WIDTH, YELLOW
from src.utils.asset_loader import AssetLoader

DIFFICULTIES = [
    {
        'key': 'easy',
        'name': 'Fácil',
        'description': 'CPU lenta e imprecisa. Boa para iniciantes.',
    },
    {
        'key': 'medium',
        'name': 'Médio',
        'description': 'CPU reage rápido e persegue a bola.',
    },
    {
        'key': 'hard',
        'name': 'Difícil',
        'description': 'CPU antecipa a bola e raramente erra.',
    },
]

_OPTION_SPACING = 72
_LIST_TOP = HEIGHT // 2 - _OPTION_SPACING


class DifficultySelectScene(Scene):
    """Tela de seleção de dificuldade para o modo 1 jogador.

    Apresenta uma lista vertical de três níveis de dificuldade. Ao
    confirmar, salva a chave em ``game.config['difficulty']`` e inicia
    a GameplayScene com todos os parâmetros acumulados.
    """

    def __init__(self, game):
        """Inicializa fontes e estado de seleção.

        Args:
            game: Instância principal do jogo. Deve conter um atributo
                ``config`` com chaves ``'mode'``, ``'character_p1'``,
                ``'character_p2'`` e ``'stadium'`` já preenchidas.
        """
        super().__init__(game)
        if not hasattr(game, 'config'):
            game.config = {}

        self.selected_index = 0

        self.font_title = AssetLoader.load_font(None, 56)
        self.font_option = AssetLoader.load_font(None, 46)
        self.font_desc = AssetLoader.load_font(None, 30)
        self.font_hint = AssetLoader.load_font(None, 26)

    def handle_events(self, events):
        """Processa navegação vertical e confirmação de dificuldade.

        Args:
            events: Lista de pygame.Event do frame atual.
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                from src.scenes.stadium_select import StadiumSelectScene
                self.game.change_scene(StadiumSelectScene(self.game))
            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(DIFFICULTIES)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(DIFFICULTIES)
            elif event.key == pygame.K_RETURN:
                self._confirm()

    def _confirm(self):
        """Salva a dificuldade e inicia a GameplayScene."""
        from src.scenes.gameplay import GameplayScene

        self.game.config['difficulty'] = DIFFICULTIES[self.selected_index]['key']
        cfg = self.game.config
        self.game.change_scene(
            GameplayScene(
                self.game,
                cfg.get('mode', '1P'),
                cfg.get('character_p1'),
                cfg.get('character_p2'),
                cfg.get('stadium'),
                difficulty=cfg.get('difficulty'),
            )
        )

    def update(self, dt):
        """Mantém a cena atualizada.

        Args:
            dt: Tempo em segundos desde o último frame.
        """

    def draw(self, surface):
        """Desenha o título, a lista de dificuldades e a descrição selecionada.

        Args:
            surface: pygame.Surface onde a cena será renderizada.
        """
        self._draw_background(surface)

        title_surf = self.font_title.render("Escolha a dificuldade", True, WHITE)
        surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 70)))

        for i, diff in enumerate(DIFFICULTIES):
            is_selected = i == self.selected_index
            color = YELLOW if is_selected else WHITE
            option_surf = self.font_option.render(diff['name'], True, color)
            option_rect = option_surf.get_rect(
                center=(WIDTH // 2, _LIST_TOP + i * _OPTION_SPACING)
            )
            surface.blit(option_surf, option_rect)

            if is_selected:
                arrow_surf = self.font_option.render("▶", True, YELLOW)
                arrow_rect = arrow_surf.get_rect(
                    midright=(option_rect.left - 18, option_rect.centery)
                )
                surface.blit(arrow_surf, arrow_rect)

        desc = DIFFICULTIES[self.selected_index]['description']
        desc_surf = self.font_desc.render(desc, True, WHITE)
        desc_y = _LIST_TOP + len(DIFFICULTIES) * _OPTION_SPACING + 20
        surface.blit(desc_surf, desc_surf.get_rect(center=(WIDTH // 2, desc_y)))

        hint_surf = self.font_hint.render(
            "↑ ↓ Navegar   ENTER Confirmar   ESC Voltar", True, WHITE
        )
        surface.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 36)))

    def _draw_background(self, surface):
        """Desenha um gradiente vertical verde-escuro como fundo.

        A cor diferente das telas anteriores indica que esta é a
        etapa final antes de entrar em campo.

        Args:
            surface: Superfície de destino.
        """
        dark = (5, 20, 5)
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(GREEN[0] * (1 - ratio) + dark[0] * ratio)
            g = int(GREEN[1] * (1 - ratio) + dark[1] * ratio)
            b = int(GREEN[2] * (1 - ratio) + dark[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))
