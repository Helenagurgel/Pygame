"""Tela de instruções — controles, mecânica de chute e power-ups.

Acessível pelo menu principal. Exibe tudo que o jogador precisa saber
antes de entrar em campo.
"""

import pygame

from src.entities.powerup import BigBall, FireBall, Freeze, GiantPlayer, LowGravity, SmallBall
from src.scenes.base_scene import Scene
from src.settings import BLACK, HEIGHT, SKY_BLUE, WIDTH
from src.utils.asset_loader import AssetLoader

_KEYS_P1 = [('A', 'esquerda'), ('D', 'direita'), ('W', 'pular'), ('ESPACO', 'chutar')]
_KEYS_P2 = [('<-', 'esquerda'), ('->', 'direita'), ('^', 'pular'), ('ENTER', 'chutar')]

_KEY_POSITIONS_X = [
    WIDTH // 2 - 360,
    WIDTH // 2 - 120,
    WIDTH // 2 + 120,
    WIDTH // 2 + 360,
]

_POWERUP_ENTRIES = [
    (FireBall,     'A bola fica em chamas — chutes ficam 1.5x mais fortes.'),
    (GiantPlayer,  'O jogador que pegou cresce e domina uma area maior.'),
    (Freeze,       'O adversario fica imobil por alguns segundos.'),
    (LowGravity,   'Gravidade reduzida temporariamente para todos.'),
    (BigBall,      'A bola dobra de tamanho — mais facil de acertar.'),
    (SmallBall,    'A bola diminui pela metade — muito mais dificil de acertar.'),
]


class InstructionsScene(Scene):
    """Tela de instrucoes com controles, mecanica de chute e power-ups.

    Exibe uma visao geral do jogo e retorna ao menu ao pressionar
    ENTER ou ESC.
    """

    def __init__(self, game):
        """Inicializa fontes para titulo, secoes, corpo e teclas.

        Args:
            game: Instancia principal do jogo.
        """
        super().__init__(game)
        self._bg = AssetLoader.load_image("assets/images/ui/Fundo Padrão.png", scale=(WIDTH, HEIGHT))
        self.font_title = AssetLoader.load_font(None, 64)
        self.font_section = AssetLoader.load_font(None, 36)
        self.font_body = AssetLoader.load_font(None, 28)
        self.font_key = AssetLoader.load_font(None, 22)
        self.font_hint = AssetLoader.load_font(None, 26)
        self._powerup_icons = self._build_powerup_icons()

    @staticmethod
    def _build_powerup_icons():
        """Instancia cada classe de power-up para extrair seu icone."""
        icons = []
        for cls, desc in _POWERUP_ENTRIES:
            instance = cls(0, 0)
            icons.append((instance.icon, desc))
        return icons

    def handle_events(self, events):
        """Retorna ao MenuScene ao pressionar ESC ou ENTER.

        Args:
            events: Lista de pygame.Event do frame atual.
        """
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
            ):
                from src.scenes.menu import MenuScene
                self.game.change_scene(MenuScene(self.game))

    def update(self, dt):
        """Mantem a cena atualizada.

        Args:
            dt: Tempo em segundos desde o ultimo frame.
        """

    def draw(self, surface):
        """Renderiza todas as secoes de instrucoes.

        Args:
            surface: pygame.Surface onde a cena sera renderizada.
        """
        surface.blit(self._bg, (0, 0))

        title_surf = self.font_title.render("Como Jogar", True, BLACK)
        surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 48)))

        self._draw_controls(surface)
        self._draw_kick_mechanics(surface)
        self._draw_powerups(surface)

        hint_surf = self.font_hint.render(
            "Pressione ENTER ou ESC para voltar", True, BLACK
        )
        surface.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 30)))

    # ------------------------------------------------------------------ #
    # Secao 1: Controles                                                   #
    # ------------------------------------------------------------------ #

    def _draw_controls(self, surface):
        """Desenha a tabela de controles dos dois jogadores.

        Args:
            surface: Superficie de destino.
        """
        header = self.font_section.render("Controles", True, BLACK)
        surface.blit(header, header.get_rect(center=(WIDTH // 2, 105)))

        p1_label = self.font_body.render("Jogador 1:", True, BLACK)
        surface.blit(p1_label, p1_label.get_rect(midright=(_KEY_POSITIONS_X[0] - 16, 155)))

        p2_label = self.font_body.render("Jogador 2:", True, BLACK)
        surface.blit(p2_label, p2_label.get_rect(midright=(_KEY_POSITIONS_X[0] - 16, 230)))

        for i, (key_text, action) in enumerate(_KEYS_P1):
            cx = _KEY_POSITIONS_X[i]
            self._draw_key(surface, key_text, (cx, 150))
            action_surf = self.font_body.render(action, True, BLACK)
            surface.blit(action_surf, action_surf.get_rect(center=(cx, 183)))

        for i, (key_text, action) in enumerate(_KEYS_P2):
            cx = _KEY_POSITIONS_X[i]
            self._draw_key(surface, key_text, (cx, 225))
            action_surf = self.font_body.render(action, True, BLACK)
            surface.blit(action_surf, action_surf.get_rect(center=(cx, 258)))

    def _draw_key(self, surface, label, center):
        """Desenha um retangulo estilo tecla com o label centralizado.

        Args:
            surface: Superficie de destino.
            label: Texto exibido dentro da tecla.
            center: Tupla (x, y) do centro da tecla.
        """
        text_surf = self.font_key.render(label, True, BLACK)
        pad_x, pad_y = 10, 5
        w = max(40, text_surf.get_width() + pad_x * 2)
        h = text_surf.get_height() + pad_y * 2
        rect = pygame.Rect(0, 0, w, h)
        rect.center = center
        pygame.draw.rect(surface, (225, 225, 225), rect, border_radius=4)
        pygame.draw.rect(surface, BLACK, rect, 2, border_radius=4)
        surface.blit(text_surf, text_surf.get_rect(center=center))

    # ------------------------------------------------------------------ #
    # Secao 2: Mecanica do chute                                           #
    # ------------------------------------------------------------------ #

    def _draw_kick_mechanics(self, surface):
        """Desenha a explicacao da mecanica de chute.

        Args:
            surface: Superficie de destino.
        """
        header = self.font_section.render("Mecanica do Chute", True, BLACK)
        surface.blit(header, header.get_rect(center=(WIDTH // 2, 300)))

        lines = [
            "A forca do chute e fixa, mas a direcao depende da posicao",
            "da bola em relacao ao jogador no momento do chute.",
            "Bola alta (na cabeca) -> chute alto.   Bola rasteira (no pe) -> chute reto.",
        ]
        for i, line in enumerate(lines):
            surf = self.font_body.render(line, True, BLACK)
            surface.blit(surf, surf.get_rect(center=(WIDTH // 2, 340 + i * 32)))

    # ------------------------------------------------------------------ #
    # Secao 3: Power-ups                                                   #
    # ------------------------------------------------------------------ #

    def _draw_powerups(self, surface):
        """Desenha a lista de power-ups com icones no lugar dos nomes.

        Args:
            surface: Superficie de destino.
        """
        header = self.font_section.render("Power-ups", True, BLACK)
        surface.blit(header, header.get_rect(center=(WIDTH // 2, 435)))

        icon_size = 30
        row_spacing = 36
        start_y = 468
        gap = 8

        for i, (icon_surf, desc) in enumerate(self._powerup_icons):
            y = start_y + i * row_spacing
            icon = pygame.transform.smoothscale(icon_surf, (icon_size, icon_size))
            desc_surf = self.font_body.render(f" {desc}", True, BLACK)
            total_w = icon_size + gap + desc_surf.get_width()
            start_x = WIDTH // 2 - total_w // 2
            surface.blit(icon, (start_x, y - icon_size // 2))
            surface.blit(desc_surf, (start_x + icon_size + gap, y - desc_surf.get_height() // 2))
