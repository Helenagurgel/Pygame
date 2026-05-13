"""
Centraliza todas as constantes globais do Head Soccer DesSoft.

Regra: NENHUM número mágico ou string literal de configuração deve aparecer
em outros módulos — importe sempre daqui.
"""

import pygame
from enum import Enum

# === Tela ===
WIDTH = 1280
HEIGHT = 720
FPS = 60
TITLE = "Head Soccer DesSoft"

# === Cores RGB ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 220)
YELLOW = (255, 220, 0)
GRAY = (160, 160, 160)
GRASS_GREEN = (34, 139, 34)   # cor do campo
SKY_BLUE = (135, 206, 235)    # cor de fundo

# === Física ===
GRAVITY = 0.6
BALL_BOUNCE = 0.7       # coeficiente de restituição
BALL_FRICTION = 0.99    # atrito do ar/chão aplicado à velocidade da bola
KICK_FORCE = 22         # módulo fixo do vetor de chute
JUMP_VELOCITY = -14     # velocidade vertical inicial do salto (negativo = para cima)
KICK_BIAS_NEAR = 5.0    # viés vertical máximo (bola muito perto)
KICK_BIAS_FAR = 0.3     # viés vertical mínimo (bola na borda do alcance)
KICK_BIAS_BODY = 2.5    # viés extra quando bola está próxima dos pés do jogador

# === Jogador ===
PLAYER_SPEED = 6
PLAYER_WIDTH = 90
PLAYER_HEIGHT = 110
GROUND_Y = HEIGHT - 80  # coordenada Y da linha do chão

# === Bola ===
BALL_RADIUS = 20
KICK_RANGE = 70         # distância máxima (px) entre jogador e bola para chutar

# === Partida ===
MATCH_DURATION = 60          # duração em segundos
GOAL_WIDTH = 30
GOAL_HEIGHT = 200
CELEBRATION_DURATION = 2.0   # segundos de celebração após um gol
KICKOFF_DURATION = 0.75      # segundos de contagem regressiva antes do jogo reiniciar
BALL_PUSH_FORCE = 4          # empurrão suave aplicado à bola no contato sem chute
BALL_BOUNCE_SOUND_MIN_VEL = 2  # |vel_y| mínima para disparar o som de quique

# === Estados do jogo ===
class GameState(Enum):
    MENU = "menu"
    INSTRUCTIONS = "instructions"
    CHAR_SELECT = "char_select"
    STADIUM_SELECT = "stadium_select"
    DIFFICULTY_SELECT = "difficulty_select"
    PLAYING = "playing"
    PAUSED = "paused"
    GOAL_CELEBRATION = "goal_celebration"
    GAME_OVER = "game_over"

# === Teclas — Jogador 1 (WASD + Espaço) ===
P1_LEFT = pygame.K_a
P1_RIGHT = pygame.K_d
P1_JUMP = pygame.K_w
P1_KICK = pygame.K_SPACE

# === Teclas — Jogador 2 (Setas + Enter) ===
P2_LEFT = pygame.K_LEFT
P2_RIGHT = pygame.K_RIGHT
P2_JUMP = pygame.K_UP
P2_KICK = pygame.K_RETURN
