"""
Centraliza o carregamento de todos os assets do Head Soccer DesSoft.

Regras:
- Use AssetLoader para qualquer imagem, som, spritesheet ou fonte.
- Assets NUNCA devem ser carregados dentro de loops de jogo; carregue
  uma única vez durante a inicialização da cena ou do jogo.
"""

import pygame


class _SilentSound:
    """Fallback mudo retornado quando um arquivo de som não é encontrado."""

    def play(self, *args, **kwargs) -> None:
        pass

    def set_volume(self, *args, **kwargs) -> None:
        pass

    def stop(self, *args, **kwargs) -> None:
        pass


class AssetLoader:
    """Carregador estático de assets para o jogo.

    Todos os métodos são estáticos e retornam um asset utilizável mesmo
    quando o arquivo não existe, evitando crashes durante o desenvolvimento.
    """

    @staticmethod
    def load_image(
        path: str,
        scale: tuple[int, int] | None = None,
        alpha: bool = True,
    ) -> pygame.Surface:
        """Carrega uma imagem do disco.

        Args:
            path: Caminho para o arquivo de imagem.
            scale: Tupla (largura, altura) para redimensionar. None mantém
                o tamanho original.
            alpha: Se True usa convert_alpha(), caso contrário convert().

        Returns:
            Surface carregada (e redimensionada, se solicitado).
            Surface placeholder 50x50 magenta em caso de erro.
        """
        try:
            surface = pygame.image.load(path)
            surface = surface.convert_alpha() if alpha else surface.convert()
            if scale is not None:
                surface = pygame.transform.scale(surface, scale)
            return surface
        except (pygame.error, FileNotFoundError, OSError):
            print(f"[AssetLoader] imagem não encontrada: {path}")
            placeholder = pygame.Surface((50, 50), pygame.SRCALPHA if alpha else 0)
            placeholder.fill((255, 0, 255))
            return placeholder

    @staticmethod
    def load_sound(path: str) -> pygame.mixer.Sound | _SilentSound:
        """Carrega um efeito sonoro do disco.

        Args:
            path: Caminho para o arquivo de som (.wav, .ogg, etc.).

        Returns:
            pygame.mixer.Sound pronto para uso, ou _SilentSound em caso
            de erro (mesma interface, sem emitir áudio).
        """
        try:
            return pygame.mixer.Sound(path)
        except (pygame.error, FileNotFoundError, OSError):
            print(f"[AssetLoader] som não encontrado: {path}")
            return _SilentSound()

    @staticmethod
    def load_spritesheet(
        path: str,
        frame_width: int,
        frame_height: int,
        num_frames: int,
    ) -> list[pygame.Surface]:
        """Carrega e fatiaa um spritesheet horizontal.

        Args:
            path: Caminho para o arquivo de imagem do spritesheet.
            frame_width: Largura de cada frame em pixels.
            frame_height: Altura de cada frame em pixels.
            num_frames: Quantidade de frames a recortar da esquerda para
                a direita.

        Returns:
            Lista de Surfaces, uma por frame. Em caso de erro, retorna
            lista com num_frames placeholders magenta de (frame_width x
            frame_height).
        """
        def _placeholder_list() -> list[pygame.Surface]:
            p = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            p.fill((255, 0, 255))
            return [p.copy() for _ in range(num_frames)]

        try:
            sheet = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            print(f"[AssetLoader] spritesheet não encontrado: {path}")
            return _placeholder_list()

        frames: list[pygame.Surface] = []
        for i in range(num_frames):
            rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), rect)
            frames.append(frame)
        return frames

    @staticmethod
    def load_font(path: str | None, size: int) -> pygame.font.Font:
        """Carrega uma fonte TTF ou retorna a fonte padrão do sistema.

        Args:
            path: Caminho para o arquivo .ttf/.otf, ou None para usar a
                fonte padrão do sistema.
            size: Tamanho da fonte em pontos.

        Returns:
            pygame.font.Font pronto para uso.
        """
        if path is None:
            return pygame.font.SysFont(None, size)
        try:
            return pygame.font.Font(path, size)
        except (pygame.error, FileNotFoundError, OSError):
            print(f"[AssetLoader] fonte não encontrada: {path} — usando fonte do sistema")
            return pygame.font.SysFont(None, size)
