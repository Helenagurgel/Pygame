"""Tela de seleção de estádio — segunda tela de configuração da partida.

Exibida após a seleção de personagens. Permite escolher o estádio que
define o background, a música e os modificadores físicos da partida.
No modo 1 jogador, avança para a seleção de dificuldade; no modo 2
jogadores, inicia a partida diretamente.
"""

import pygame

from src.scenes.base_scene import Scene, blit_outlined
from src.settings import BLACK, BLUE, HEIGHT, WHITE, WIDTH, YELLOW
from src.utils.asset_loader import AssetLoader

STADIUMS = [
    {
        'name': 'Estádio Clássico',
        'background_path': 'assets/images/stadiums/Estádio.png',
        'music_path': 'assets/sounds/music/classic.ogg',
        'gravity_mult': 1.0,
        'friction_mult': 1.0,
        'description': 'Campo padrão de futebol',
    },
    {
        'name': 'Lua',
        'background_path': 'assets/images/stadiums/Lua.png',
        'music_path': 'assets/sounds/music/moon.ogg',
        'gravity_mult': 0.4,
        'friction_mult': 1.0,
        'description': 'Gravidade reduzida — bola flutua mais',
    },
    {
        'name': 'Pista Gelada',
        'background_path': 'assets/images/stadiums/Pista de Gelo.png',
        'music_path': 'assets/sounds/music/ice.ogg',
        'gravity_mult': 1.0,
        'friction_mult': 0.7,
        'description': 'Atrito baixo — escorregadio',
    },
]

_THUMB_W, _THUMB_H = 480, 270


class StadiumSelectScene(Scene):
    """Tela de seleção de estádio com navegação por teclado.

    Mostra um thumbnail grande do estádio selecionado, seu nome,
    descrição e modificadores físicos. Avança para DifficultySelectScene
    (modo 1P) ou GameplayScene (modo 2P) ao confirmar.
    """

    def __init__(self, game):
        """Inicializa a cena, carregando thumbnails e configurando as fontes.

        Args:
            game: Instância principal do jogo. Deve conter um atributo
                ``config`` com chaves ``'mode'``, ``'character_p1'`` e
                ``'character_p2'`` preenchidas pela tela anterior.
        """
        super().__init__(game)
        self._bg = AssetLoader.load_image("assets/images/ui/Fundo Padrão.png", scale=(WIDTH, HEIGHT))
        if not hasattr(game, 'config'):
            game.config = {}

        self.selected_index = 0

        self._thumbnails = [
            AssetLoader.load_image(s['background_path'], scale=(_THUMB_W, _THUMB_H))
            for s in STADIUMS
        ]

        self.font_title = AssetLoader.load_font(None, 52)
        self.font_name = AssetLoader.load_font(None, 44)
        self.font_desc = AssetLoader.load_font(None, 30)
        self.font_stats = AssetLoader.load_font(None, 26)
        self.font_hint = AssetLoader.load_font(None, 26)

    def handle_events(self, events):
        """Processa navegação e confirmação de estádio.

        Args:
            events: Lista de pygame.Event do frame atual.
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                from src.scenes.character_select import CharacterSelectScene
                self.game.change_scene(CharacterSelectScene(self.game))
            elif event.key == pygame.K_LEFT:
                self.selected_index = (self.selected_index - 1) % len(STADIUMS)
            elif event.key == pygame.K_RIGHT:
                self.selected_index = (self.selected_index + 1) % len(STADIUMS)
            elif event.key == pygame.K_RETURN:
                self._confirm()

    def _confirm(self):
        """Salva o estádio em game.config e avança para a próxima cena."""
        self.game.config['stadium'] = STADIUMS[self.selected_index]
        mode = self.game.config.get('mode', '2P')
        if mode == '1P':
            self._go_to_difficulty()
        else:
            self._go_to_gameplay()

    def _go_to_difficulty(self):
        """Transiciona para DifficultySelectScene (ou placeholder)."""
        try:
            from src.scenes.difficulty_select import DifficultySelectScene
            self.game.change_scene(DifficultySelectScene(self.game))
        except ImportError:
            self.game.change_scene("difficulty_select")

    def _go_to_gameplay(self):
        """Instancia GameplayScene com os parâmetros acumulados em game.config."""
        from src.scenes.gameplay import GameplayScene

        cfg = self.game.config
        self.game.change_scene(
            GameplayScene(
                self.game,
                cfg.get('mode', '2P'),
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
        """Desenha o thumbnail, nome, descrição e modificadores do estádio.

        Args:
            surface: pygame.Surface onde a cena será renderizada.
        """
        self._draw_background(surface)

        blit_outlined(surface, self.font_title, "Escolha o Estádio", WHITE, (WIDTH // 2, 55))

        stadium = STADIUMS[self.selected_index]
        thumb = self._thumbnails[self.selected_index]
        thumb_rect = thumb.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        surface.blit(thumb, thumb_rect)

        # Borda ao redor do thumbnail
        pygame.draw.rect(surface, YELLOW, thumb_rect.inflate(6, 6), 3)

        # Setas de navegação laterais
        nav_font = self.font_name
        nav_y = thumb_rect.centery
        nav_left_x = thumb_rect.left - 30
        nav_right_x = thumb_rect.right + 30
        for text, cx in (("◀", nav_left_x), ("▶", nav_right_x)):
            shd = nav_font.render(text, True, (0, 0, 0))
            surface.blit(shd, shd.get_rect(center=(cx + 2, nav_y + 2)))
            arr = nav_font.render(text, True, YELLOW)
            surface.blit(arr, arr.get_rect(center=(cx, nav_y)))

        blit_outlined(surface, self.font_name, stadium['name'], YELLOW,
                      (WIDTH // 2, thumb_rect.bottom + 28))
        blit_outlined(surface, self.font_desc, stadium['description'], WHITE,
                      (WIDTH // 2, thumb_rect.bottom + 66))

        stats_text = (
            f"Gravidade ×{stadium['gravity_mult']:.1f}   "
            f"Atrito ×{stadium['friction_mult']:.1f}"
        )
        blit_outlined(surface, self.font_stats, stats_text, YELLOW,
                      (WIDTH // 2, thumb_rect.bottom + 100))

        blit_outlined(surface, self.font_hint, "← → Navegar   ENTER Confirmar   ESC Voltar",
                      WHITE, (WIDTH // 2, HEIGHT - 36))

    def _draw_background(self, surface):
        surface.blit(self._bg, (0, 0))
