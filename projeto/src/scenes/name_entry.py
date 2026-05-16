"""Tela de entrada de nome quando o jogador entra no top 5."""

import pygame

from src.scenes.base_scene import Scene, blit_outlined
from src.settings import HEIGHT, WHITE, WIDTH, YELLOW
from src.utils.asset_loader import AssetLoader
from src.utils.ranking import RankingManager

_MAX_NAME_LEN = 16


class NameEntryScene(Scene):
    """Exibe 'NOVO RECORDE!' e permite digitar o nome antes de salvar."""

    def __init__(self, game, score_p1: int, score_p2: int):
        super().__init__(game)
        self._bg = AssetLoader.load_image("assets/images/ui/Fundo Padrão.png", scale=(WIDTH, HEIGHT))
        self.score_p1 = score_p1
        self.score_p2 = score_p2
        self.name = ""
        self._cursor_blink = 0.0

        self.font_title  = AssetLoader.load_font(None, 80)
        self.font_prompt = AssetLoader.load_font(None, 42)
        self.font_name   = AssetLoader.load_font(None, 60)
        self.font_score  = AssetLoader.load_font(None, 38)
        self.font_hint   = AssetLoader.load_font(None, 28)

        pygame.key.start_text_input()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.name.strip():
                    self._confirm()
                elif event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.name = "Jogador"
                    self._confirm()
            elif event.type == pygame.TEXTINPUT:
                if len(self.name) < _MAX_NAME_LEN:
                    self.name += event.text

    def _confirm(self):
        pygame.key.stop_text_input()
        from src.scenes.ranking import RankingScene
        RankingManager.add_entry(
            self.name.strip() or "Jogador",
            self.score_p1,
            self.score_p2,
        )
        self.game.change_scene(RankingScene(self.game))

    def update(self, dt):
        self._cursor_blink += dt

    def draw(self, surface):
        surface.blit(self._bg, (0, 0))

        blit_outlined(surface, self.font_title, "NOVO RECORDE!", YELLOW, (WIDTH // 2, 130))

        diff = abs(self.score_p1 - self.score_p2)
        score_text = f"Placar: {self.score_p1} x {self.score_p2}  (diferenca de {diff} gols)"
        blit_outlined(surface, self.font_score, score_text, WHITE, (WIDTH // 2, 230))

        blit_outlined(surface, self.font_prompt, "Digite seu nome:", WHITE, (WIDTH // 2, 330))

        # Caixinha de fundo pro campo de texto (antes do texto)
        box_w, box_h = 480, 64
        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((0, 0, 0, 120))
        surface.blit(box, (WIDTH // 2 - box_w // 2, 385))
        pygame.draw.rect(surface, YELLOW, (WIDTH // 2 - box_w // 2, 385, box_w, box_h), 2)

        cursor = "|" if int(self._cursor_blink * 2) % 2 == 0 else " "
        blit_outlined(surface, self.font_name, self.name + cursor, YELLOW, (WIDTH // 2, 417))

        blit_outlined(
            surface, self.font_hint,
            "ENTER confirmar   ESC pular",
            WHITE, (WIDTH // 2, HEIGHT - 44),
        )
