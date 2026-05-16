"""Tela de ranking — exibe o top 5 de maiores goleadas."""

import pygame

from src.scenes.base_scene import Scene, blit_outlined
from src.settings import HEIGHT, WHITE, WIDTH, YELLOW, GRAY
from src.utils.asset_loader import AssetLoader
from src.utils.ranking import RankingManager

_MEDALS = ["1.", "2.", "3.", "4.", "5."]
_ROW_SPACING = 82


class RankingScene(Scene):
    """Mostra as 5 maiores goleadas salvas, ordenadas por diferenca de gols."""

    def __init__(self, game):
        super().__init__(game)
        self._bg = AssetLoader.load_image("assets/images/ui/Fundo Padrão.png", scale=(WIDTH, HEIGHT))
        self.entries = RankingManager.load()

        self.font_title = AssetLoader.load_font(None, 68)
        self.font_entry = AssetLoader.load_font(None, 42)
        self.font_empty = AssetLoader.load_font(None, 36)
        self.font_hint  = AssetLoader.load_font(None, 28)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                from src.scenes.menu import MenuScene
                self.game.change_scene(MenuScene(self.game))

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.blit(self._bg, (0, 0))

        blit_outlined(surface, self.font_title, "TOP 5 - MAIORES GOLEADAS", YELLOW, (WIDTH // 2, 62))

        if not self.entries:
            blit_outlined(surface, self.font_empty, "Nenhum recorde salvo ainda.", WHITE,
                          (WIDTH // 2, HEIGHT // 2))
        else:
            row_y = 158
            for i, entry in enumerate(self.entries):
                medal   = _MEDALS[i]
                name    = entry["name"]
                sp1     = entry["score_p1"]
                sp2     = entry["score_p2"]
                diff    = entry["diff"]
                color   = YELLOW if i == 0 else WHITE

                # Linha: "1.  NomeAqui   5 x 2   (Δ 3)"
                line = f"{medal}  {name:<16}  {sp1} x {sp2}   (D {diff})"
                blit_outlined(surface, self.font_entry, line, color, (WIDTH // 2, row_y))

                # Separador leve
                if i < len(self.entries) - 1:
                    sep_y = row_y + _ROW_SPACING // 2 + 4
                    pygame.draw.line(surface, GRAY,
                                     (WIDTH // 4, sep_y), (WIDTH * 3 // 4, sep_y), 1)

                row_y += _ROW_SPACING

        blit_outlined(surface, self.font_hint,
                      "Pressione qualquer tecla para voltar ao menu",
                      WHITE, (WIDTH // 2, HEIGHT - 40))
