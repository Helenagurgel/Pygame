"""Entry point for Head Soccer DesSoft."""

import os

# Garante que o diretório de trabalho seja sempre a pasta do projeto,
# independente de onde o Python foi invocado.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.game import Game


if __name__ == "__main__":
    Game().run()
