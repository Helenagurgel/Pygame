"""Tela de seleção de personagem — primeira tela após o menu principal.

Permite que cada jogador escolha o seu personagem antes de prosseguir
para a seleção de estádio. No modo 2 jogadores, P1 escolhe primeiro e
depois P2; no modo 1 jogador, o personagem do CPU é sorteado.
"""

import math
import random

import pygame

from src.scenes.base_scene import Scene
from src.settings import BLACK, GRAY, HEIGHT, SKY_BLUE, WIDTH
from src.utils.asset_loader import AssetLoader

CHARACTERS = [
    {
        'name': 'Veloz',
        'speed_mult': 1.4,
        'jump_mult': 1.0,
        'force_mult': 0.9,
        'sprite_path': 'assets/images/players/veloz.png',
        'description': 'Sprint acelerado, chute fraco',
        'sprites': {},
    },
    {
        'name': 'Saltador',
        'speed_mult': 1.0,
        'jump_mult': 1.3,
        'force_mult': 1.0,
        'sprite_path': 'assets/images/players/saltador.png',
        'description': 'Pulo elevado, velocidade padrão',
        'sprites': {},
    },
    {
        'name': 'Equilibrado',
        'speed_mult': 1.1,
        'jump_mult': 1.1,
        'force_mult': 1.1,
        'sprite_path': 'assets/images/players/equilibrado.png',
        'description': 'Atributos balanceados',
        'sprites': {},
    },
    {
        'name': 'Tanque',
        'speed_mult': 0.9,
        'jump_mult': 0.9,
        'force_mult': 1.5,
        'sprite_path': 'assets/images/players/tanque.png',
        'description': 'Lento mas chute potente',
        'sprites': {},
    },
]

_REVEAL_DURATION = 2.2          # segundos exibindo o personagem sorteado da CPU
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
        self._state = 'select'   # 'select' | 'cpu_reveal'
        self._cpu_char = None
        self._reveal_timer = 0.0

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
        if self._state == 'cpu_reveal':
            return
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
                available = [c for i, c in enumerate(CHARACTERS) if i != self.selected_p1]
                cpu_char = random.choice(available)
                self.game.config['character_p2'] = cpu_char
                self._cpu_char = cpu_char
                self._state = 'cpu_reveal'
                self._reveal_timer = 0.0
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
        if self._state == 'cpu_reveal':
            self._reveal_timer += dt
            if self._reveal_timer >= _REVEAL_DURATION:
                self._go_to_stadium()

    def _draw_cpu_reveal(self, surface):
        """Exibe o personagem sorteado para a CPU por _REVEAL_DURATION segundos."""
        surface.fill(SKY_BLUE)

        title = self.font_title.render("A CPU vai usar...", True, BLACK)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 160)))

        char = self._cpu_char
        char_idx = CHARACTERS.index(char)
        pulse = 1.0 + 0.07 * math.sin(self._reveal_timer * 5.0)
        w = int(_PREVIEW_W * 1.4 * pulse)
        h = int(_PREVIEW_H * 1.4 * pulse)
        self._blit_preview(surface, char_idx, center=(WIDTH // 2, HEIGHT // 2 - 10), w=w, h=h)

        name_surf = self.font_name.render(char['name'], True, BLACK)
        surface.blit(name_surf, name_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120)))

        desc_surf = self.font_desc.render(char['description'], True, BLACK)
        surface.blit(desc_surf, desc_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 158)))

        progress = min(self._reveal_timer / _REVEAL_DURATION, 1.0)
        bar_w = int(WIDTH * 0.4 * progress)
        bar_x = WIDTH // 2 - int(WIDTH * 0.2)
        pygame.draw.rect(surface, GRAY, (bar_x, HEIGHT - 50, int(WIDTH * 0.4), 10), border_radius=5)
        pygame.draw.rect(surface, BLACK, (bar_x, HEIGHT - 50, bar_w, 10), border_radius=5)

    def draw(self, surface):
        """Desenha o carrossel, nome, descrição e instruções de navegação.

        Args:
            surface: pygame.Surface onde a cena será renderizada.
        """
        if self._state == 'cpu_reveal':
            self._draw_cpu_reveal(surface)
            return

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
        surface.blit(desc_surf, desc_surf.get_rect(center=(WIDTH // 2, _CAROUSEL_Y + 148)))

        char = CHARACTERS[idx]
        self._draw_stat_bar(surface, "Velocidade", char['speed_mult'], _CAROUSEL_Y + 178,
                            color=(220, 120, 40))
        self._draw_stat_bar(surface, "Pulo", char['jump_mult'], _CAROUSEL_Y + 206,
                            color=(60, 120, 220))
        self._draw_stat_bar(surface, "Força", char['force_mult'], _CAROUSEL_Y + 234,
                            color=(180, 60, 60))

        hint_surf = self.font_hint.render(
            "← → Navegar   ENTER Confirmar   ESC Voltar", True, BLACK
        )
        surface.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 36)))

    def _draw_stat_bar(self, surface, label, value, y, color=(80, 180, 80)):
        """Draw a labeled stat bar showing the multiplier value numerically."""
        max_val = 1.5
        bar_w = 180
        bar_h = 14
        fill_w = int(bar_w * min(value / max_val, 1.0))
        bar_x = WIDTH // 2 - bar_w // 2

        lbl = self.font_desc.render(label, True, BLACK)
        surface.blit(lbl, lbl.get_rect(right=bar_x - 8, centery=y + bar_h // 2))

        pygame.draw.rect(surface, (180, 180, 180), (bar_x, y, bar_w, bar_h), border_radius=4)
        if fill_w > 0:
            pygame.draw.rect(surface, color, (bar_x, y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, BLACK, (bar_x, y, bar_w, bar_h), 2, border_radius=4)

        val_text = self.font_hint.render(f"{value:.2f}×", True, BLACK)
        surface.blit(val_text, val_text.get_rect(left=bar_x + bar_w + 8, centery=y + bar_h // 2))

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
