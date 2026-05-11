"""Tela de seleção de personagem — primeira tela após o menu principal.

Permite que cada jogador escolha o seu personagem antes de prosseguir
para a seleção de estádio. No modo 2 jogadores, P1 escolhe primeiro e
depois P2; no modo 1 jogador, o personagem do CPU é sorteado.
"""

import math
import random

import pygame

from src.scenes.base_scene import Scene
from src.settings import BLACK, HEIGHT, SKY_BLUE, WIDTH
from src.utils.asset_loader import AssetLoader

CHARACTERS = [
    {
        'name': 'Veloz',
        'speed_mult': 1.3,
        'jump_mult': 1.0,
        'sprite_path': 'assets/images/players/veloz.png',
        'description': 'Rápido, mas pulo médio',
    },
    {
        'name': 'Saltador',
        'speed_mult': 1.0,
        'jump_mult': 1.4,
        'sprite_path': 'assets/images/players/saltador.png',
        'description': 'Pulo alto, velocidade média',
    },
    {
        'name': 'Equilibrado',
        'speed_mult': 1.1,
        'jump_mult': 1.1,
        'sprite_path': 'assets/images/players/equilibrado.png',
        'description': 'Atributos balanceados',
    },
    {
        'name': 'Tanque',
        'speed_mult': 0.9,
        'jump_mult': 0.9,
        'sprite_path': 'assets/images/players/tanque.png',
        'description': 'Lento, mas poderoso',
    },
]

_PREVIEW_W, _PREVIEW_H = 140, 160
_NEIGHBOR_W, _NEIGHBOR_H = 90, 105
_CENTER_X = WIDTH // 2
_CAROUSEL_Y = HEIGHT // 2 - 10
_NEIGHBOR_OFFSET = 240


class CharacterSelectScene(Scene):
    """Tela de seleção de personagem para um ou dois jogadores.

    Exibe um carrossel horizontal de personagens. No modo 2 jogadores,
    cada jogador faz a sua escolha em sequência antes de avançar para
    a tela de seleção de estádio.
    """

    def __init__(self, game):
        """Inicializa a cena, carregando previews e configurando o estado.

        Args:
            game: Instância principal do jogo. Deve conter (ou receberá)
                o atributo ``config`` do tipo dict com a chave ``'mode'``.
        """
        super().__init__(game)
        if not hasattr(game, 'config'):
            game.config = {}

        self.mode = game.config.get('mode', '2P')
        self.current_player = 1
        self.selected_p1 = 0
        self.selected_p2 = 0

        self._previews = [
            AssetLoader.load_image(char['sprite_path'], scale=(_PREVIEW_W, _PREVIEW_H))
            for char in CHARACTERS
        ]

        self.font_title = AssetLoader.load_font(None, 52)
        self.font_name = AssetLoader.load_font(None, 40)
        self.font_desc = AssetLoader.load_font(None, 28)
        self.font_hint = AssetLoader.load_font(None, 26)

        self._pulse_time = 0.0

    @property
    def _active_index(self):
        """Índice do personagem selecionado pelo jogador atual."""
        return self.selected_p1 if self.current_player == 1 else self.selected_p2

    @_active_index.setter
    def _active_index(self, value):
        if self.current_player == 1:
            self.selected_p1 = value
        else:
            self.selected_p2 = value

    def handle_events(self, events):
        """Processa navegação no carrossel e confirmação de personagem.

        Args:
            events: Lista de pygame.Event do frame atual.
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                from src.scenes.menu import MenuScene
                self.game.change_scene(MenuScene(self.game))
            elif event.key == pygame.K_LEFT:
                self._active_index = (self._active_index - 1) % len(CHARACTERS)
                self._pulse_time = 0.0
            elif event.key == pygame.K_RIGHT:
                self._active_index = (self._active_index + 1) % len(CHARACTERS)
                self._pulse_time = 0.0
            elif event.key == pygame.K_RETURN:
                self._confirm()

    def _confirm(self):
        """Avança para o próximo jogador ou transiciona para a próxima cena."""
        if self.current_player == 1 and self.mode == '2P':
            self.current_player = 2
            self._pulse_time = 0.0
        else:
            self.game.config['character_p1'] = CHARACTERS[self.selected_p1]
            if self.mode == '1P':
                self.game.config['character_p2'] = random.choice(CHARACTERS)
            else:
                self.game.config['character_p2'] = CHARACTERS[self.selected_p2]
            self._go_to_stadium()

    def _go_to_stadium(self):
        """Transiciona para StadiumSelectScene (ou placeholder se não existir)."""
        try:
            from src.scenes.stadium_select import StadiumSelectScene
            self.game.change_scene(StadiumSelectScene(self.game))
        except ImportError:
            self.game.change_scene("stadium_select")

    def update(self, dt):
        """Acumula tempo para a animação de pulso do personagem selecionado.

        Args:
            dt: Tempo em segundos desde o último frame.
        """
        self._pulse_time += dt

    def draw(self, surface):
        """Desenha o carrossel, nome, descrição e instruções de navegação.

        Args:
            surface: pygame.Surface onde a cena será renderizada.
        """
        surface.fill(SKY_BLUE)

        title_text = f"Escolha seu personagem (P{self.current_player})"
        title_surf = self.font_title.render(title_text, True, BLACK)
        surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))

        idx = self._active_index
        n = len(CHARACTERS)
        pulse = 1.0 + 0.05 * math.sin(self._pulse_time * 4.0)

        self._blit_preview(
            surface, (idx - 1) % n,
            center=(_CENTER_X - _NEIGHBOR_OFFSET, _CAROUSEL_Y),
            w=_NEIGHBOR_W, h=_NEIGHBOR_H,
        )
        self._blit_preview(
            surface, (idx + 1) % n,
            center=(_CENTER_X + _NEIGHBOR_OFFSET, _CAROUSEL_Y),
            w=_NEIGHBOR_W, h=_NEIGHBOR_H,
        )
        self._blit_preview(
            surface, idx,
            center=(_CENTER_X, _CAROUSEL_Y),
            w=int(_PREVIEW_W * pulse), h=int(_PREVIEW_H * pulse),
        )

        name_surf = self.font_name.render(CHARACTERS[idx]['name'], True, BLACK)
        surface.blit(name_surf, name_surf.get_rect(center=(WIDTH // 2, _CAROUSEL_Y + 110)))

        desc_surf = self.font_desc.render(CHARACTERS[idx]['description'], True, BLACK)
        surface.blit(desc_surf, desc_surf.get_rect(center=(WIDTH // 2, _CAROUSEL_Y + 150)))

        hint_surf = self.font_hint.render(
            "← → Navegar   ENTER Confirmar   ESC Voltar", True, BLACK
        )
        surface.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 36)))

    def _blit_preview(self, surface, char_index, center, w, h):
        """Blit o preview de um personagem numa posição e tamanho dados.

        Args:
            surface: Superfície de destino.
            char_index: Índice em CHARACTERS.
            center: Tupla (x, y) do centro da imagem na superfície.
            w: Largura final em pixels.
            h: Altura final em pixels.
        """
        scaled = pygame.transform.scale(self._previews[char_index], (w, h))
        surface.blit(scaled, scaled.get_rect(center=center))
