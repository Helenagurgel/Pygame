"""Core gameplay scene for Head Soccer DesSoft."""

import pygame

from src.entities.ball import Ball
from src.entities.player import Player
from src.scenes.base_scene import Scene
from src.settings import (
    BALL_RADIUS,
    BLACK,
    BLUE,
    GOAL_HEIGHT,
    GOAL_WIDTH,
    GRASS_GREEN,
    GRAY,
    GROUND_Y,
    HEIGHT,
    MATCH_DURATION,
    P1_JUMP,
    P1_KICK,
    P1_LEFT,
    P1_RIGHT,
    P2_JUMP,
    P2_KICK,
    P2_LEFT,
    P2_RIGHT,
    PLAYER_HEIGHT,
    PLAYER_WIDTH,
    WHITE,
    WIDTH,
    YELLOW,
)
from src.utils.particle import ParticleSystem


CELEBRATION_DURATION = 2.0
KICKOFF_DURATION = 0.75
BALL_PUSH_FORCE = 4


class _PressedKeys:
    """Small key-state adapter used by the CPU player."""

    def __init__(self, pressed_keys):
        """Store a set with pygame key constants considered pressed."""
        self.pressed_keys = pressed_keys

    def __getitem__(self, key):
        """Return True when the requested key is active."""
        return key in self.pressed_keys


class GameOverScene(Scene):
    """Temporary game-over scene used until the final scene exists."""

    def __init__(self, game, score_p1, score_p2):
        """Create a result screen with the final scores."""
        super().__init__(game)
        self.score_p1 = score_p1
        self.score_p2 = score_p2
        self.title_font = pygame.font.Font(None, 72)
        self.text_font = pygame.font.Font(None, 42)

    def handle_events(self, events):
        """Return to the menu placeholder when ENTER is pressed."""
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.game.change_scene("menu")

    def update(self, dt):
        """Keep the result screen state updated."""

    def draw(self, surface):
        """Draw the final score."""
        surface.fill(BLACK)
        title = self.title_font.render("FIM DE JOGO", True, WHITE)
        score = self.text_font.render(
            f"{self.score_p1} x {self.score_p2}",
            True,
            YELLOW,
        )
        surface.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
        surface.blit(score, score.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))


class PauseScene(Scene):
    """Temporary pause scene used until the final pause scene exists."""

    def __init__(self, game, previous_scene):
        """Create a pause screen that can resume the previous gameplay scene."""
        super().__init__(game)
        self.previous_scene = previous_scene
        self.title_font = pygame.font.Font(None, 72)
        self.text_font = pygame.font.Font(None, 36)

    def handle_events(self, events):
        """Resume gameplay with ESC or ENTER."""
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
            ):
                self.game.change_scene(self.previous_scene)

    def update(self, dt):
        """Keep the pause scene state updated."""

    def draw(self, surface):
        """Draw the pause overlay."""
        self.previous_scene.draw(surface)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        title = self.title_font.render("PAUSADO", True, WHITE)
        hint = self.text_font.render("ESC ou ENTER para continuar", True, YELLOW)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35)))
        surface.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 35)))


class GameplayScene(Scene):
    """Main match scene with players, ball, score, timer, and goals."""

    def __init__(self, game, mode, character_p1, character_p2, stadium, difficulty=None):
        """Create the full gameplay scene.

        Args:
            game: Main Game object used for scene transitions.
            mode: Match mode, either '1P' for player versus CPU or '2P' for two
                local players.
            character_p1: Character data dict used to create player 1.
            character_p2: Character data dict used to create player 2.
            stadium: Stadium data. It may be a dict containing background,
                background_path and gravity_mult, a pygame.Surface, or None.
            difficulty: Optional CPU difficulty descriptor for future tuning.

        The scene creates two players, a centered ball, sprite groups,
        particles, invisible goal rectangles, HUD fonts, and internal match
        state for kickoff, playing, and goal celebration.
        """
        super().__init__(game)
        if mode not in {"1P", "2P"}:
            raise ValueError("mode must be '1P' or '2P'.")

        self.mode = mode
        self.difficulty = difficulty
        self.stadium = stadium
        self.gravity_mult = self._get_gravity_mult(stadium)
        self.background = self._load_background(stadium)
        self.goal_sound = None

        # feito com IA: controles dos jogadores e CPU reaproveitam Player.handle_input.
        self.p1_controls = {
            "left": P1_LEFT,
            "right": P1_RIGHT,
            "jump": P1_JUMP,
            "kick": P1_KICK,
        }
        self.p2_controls = {
            "left": P2_LEFT,
            "right": P2_RIGHT,
            "jump": P2_JUMP,
            "kick": P2_KICK,
        }

        self.player1_start = (WIDTH // 4 - PLAYER_WIDTH // 2, GROUND_Y - PLAYER_HEIGHT)
        self.player2_start = (
            WIDTH * 3 // 4 - PLAYER_WIDTH // 2,
            GROUND_Y - PLAYER_HEIGHT,
        )
        self.ball_start = (WIDTH // 2, GROUND_Y - BALL_RADIUS * 4)

        self.player1 = Player(*self.player1_start, self.p1_controls, character_p1)
        self.player2 = Player(
            *self.player2_start,
            self.p2_controls,
            character_p2,
            facing_right=False,
        )
        self.ball = Ball(*self.ball_start, self._create_ball_image())

        # feito com IA: grupos separam sprites principais e futuros powerups.
        self.all_sprites = pygame.sprite.Group(self.player1, self.player2, self.ball)
        self.players = pygame.sprite.Group(self.player1, self.player2)
        self.powerups = pygame.sprite.Group()
        self.particles = ParticleSystem()

        self.score_p1 = 0
        self.score_p2 = 0
        self.time_left = MATCH_DURATION
        self.state = "kickoff"
        self.kickoff_timer = KICKOFF_DURATION
        self.celebration_timer = 0

        self.left_goal = pygame.Rect(0, GROUND_Y - GOAL_HEIGHT, GOAL_WIDTH, GOAL_HEIGHT)
        self.right_goal = pygame.Rect(
            WIDTH - GOAL_WIDTH,
            GROUND_Y - GOAL_HEIGHT,
            GOAL_WIDTH,
            GOAL_HEIGHT,
        )

        self.hud_font = pygame.font.Font(None, 64)
        self.timer_font = pygame.font.Font(None, 42)

    def handle_events(self, events):
        """Handle gameplay events, including ESC to pause."""
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.change_scene(PauseScene(self.game, self))

    def update(self, dt):
        """Update timers, input, physics, collisions, goals, and transitions.

        Args:
            dt: Time elapsed since the previous frame, in seconds.

        During kickoff and normal play, the match timer decreases and both
        players receive input. In 1P mode, player 2 receives simple CPU input
        that follows the ball. Kicks apply fixed-force vectors from Player,
        passive player-ball collisions nudge the ball gently, goals increment
        the score and start a two-second celebration, and time expiration
        changes to GameOverScene with both scores.
        """
        if self.state == "celebrating":
            self._update_celebration(dt)
            return

        self.time_left = max(0, self.time_left - dt)
        if self.time_left <= 0:
            self.game.change_scene(GameOverScene(self.game, self.score_p1, self.score_p2))
            return

        if self.state == "kickoff":
            self.kickoff_timer -= dt
            if self.kickoff_timer <= 0:
                self.state = "playing"

        # feito com IA: entrada humana e CPU são aplicadas antes da física.
        keys = pygame.key.get_pressed()
        self.player1.handle_input(keys)
        if self.mode == "1P":
            self.player2.handle_input(self._get_cpu_keys())
        else:
            self.player2.handle_input(keys)

        for player in self.players:
            player.update(dt, GROUND_Y)
        self.ball.update(dt, GROUND_Y, WIDTH, self.gravity_mult)
        self.powerups.update(dt)
        self.particles.update(dt)

        # feito com IA: ações de chute têm prioridade sobre empurrões passivos.
        for player in self.players:
            kick_vector = player.try_kick(self.ball)
            if kick_vector is not None:
                self.ball.kick(*kick_vector)
                self.particles.emit_sparkle(*self.ball.rect.center, count=3)

        self._handle_player_ball_collisions()
        self._check_goals()

    def draw(self, surface):
        """Draw the stadium, invisible gameplay objects, particles, and HUD."""
        surface.blit(self.background, (0, 0))
        self._draw_field(surface)
        self.particles.draw(surface)
        self.all_sprites.draw(surface)
        self.powerups.draw(surface)
        self.draw_hud(surface)

    def draw_hud(self, surface):
        """Draw score and remaining time with high-contrast colors.

        Args:
            surface: Target pygame.Surface for the HUD.

        The score is centered at the top of the screen and the remaining time
        appears just below it. Text shadows improve contrast against stadium
        backgrounds.
        """
        score_text = f"{self.score_p1}  x  {self.score_p2}"
        time_text = str(max(0, int(self.time_left)))

        score_shadow = self.hud_font.render(score_text, True, BLACK)
        score_surface = self.hud_font.render(score_text, True, YELLOW)
        time_shadow = self.timer_font.render(time_text, True, BLACK)
        time_surface = self.timer_font.render(time_text, True, WHITE)

        score_rect = score_surface.get_rect(center=(WIDTH // 2, 38))
        time_rect = time_surface.get_rect(center=(WIDTH // 2, 88))

        surface.blit(score_shadow, score_rect.move(3, 3))
        surface.blit(score_surface, score_rect)
        surface.blit(time_shadow, time_rect.move(2, 2))
        surface.blit(time_surface, time_rect)

    def _update_celebration(self, dt):
        """Animate particles during the post-goal celebration window."""
        self.celebration_timer -= dt
        self.particles.update(dt)

        if self.celebration_timer <= 0:
            self._reset_positions()
            self.state = "kickoff"
            self.kickoff_timer = KICKOFF_DURATION

    def _handle_player_ball_collisions(self):
        """Push the ball softly when a player touches it without a kick."""
        for player in self.players:
            if not player.rect.colliderect(self.ball.rect):
                continue

            dx = self.ball.rect.centerx - player.rect.centerx
            dy = self.ball.rect.centery - player.rect.centery
            if dx == 0 and dy == 0:
                dx = 1

            length = max(1, (dx * dx + dy * dy) ** 0.5)
            self.ball.vel_x += (dx / length) * BALL_PUSH_FORCE
            self.ball.vel_y += (dy / length) * BALL_PUSH_FORCE * 0.5

    def _check_goals(self):
        """Detect goals, update score, and start celebration state."""
        if self.left_goal.collidepoint(self.ball.rect.center):
            self.score_p2 += 1
            self._start_goal_celebration()
        elif self.right_goal.collidepoint(self.ball.rect.center):
            self.score_p1 += 1
            self._start_goal_celebration()

    def _start_goal_celebration(self):
        """Begin the two-second goal celebration after scoring."""
        self.state = "celebrating"
        self.celebration_timer = CELEBRATION_DURATION
        self.ball.vel_x = 0
        self.ball.vel_y = 0
        self.particles.emit_sparkle(*self.ball.rect.center, count=18)

        if self.goal_sound is not None:
            self.goal_sound.play()

    def _reset_positions(self):
        """Reset players and ball to kickoff positions after a goal."""
        self.player1.rect.topleft = self.player1_start
        self.player1.vel_x = 0
        self.player1.vel_y = 0
        self.player1.facing_right = True
        self.player2.rect.topleft = self.player2_start
        self.player2.vel_x = 0
        self.player2.vel_y = 0
        self.player2.facing_right = False
        self.ball.reset(*self.ball_start)

    def _get_cpu_keys(self):
        """Return a simple CPU key state that follows and challenges the ball."""
        pressed = set()
        center_gap = self.ball.rect.centerx - self.player2.rect.centerx

        if center_gap < -20:
            pressed.add(self.p2_controls["left"])
        elif center_gap > 20:
            pressed.add(self.p2_controls["right"])

        if self.ball.rect.centery < self.player2.rect.centery - 70:
            pressed.add(self.p2_controls["jump"])

        if self.player2.rect.colliderect(self.ball.rect.inflate(40, 40)):
            pressed.add(self.p2_controls["kick"])

        return _PressedKeys(pressed)

    def _load_background(self, stadium):
        """Load or create the stadium background surface."""
        if isinstance(stadium, pygame.Surface):
            return pygame.transform.scale(stadium, (WIDTH, HEIGHT))

        if isinstance(stadium, dict):
            background = stadium.get("background")
            if isinstance(background, pygame.Surface):
                return pygame.transform.scale(background, (WIDTH, HEIGHT))

            background_path = stadium.get("background_path")
            if background_path:
                try:
                    image = pygame.image.load(background_path).convert()
                    return pygame.transform.scale(image, (WIDTH, HEIGHT))
                except (pygame.error, FileNotFoundError, OSError):
                    return self._create_default_background()

        return self._create_default_background()

    def _create_default_background(self):
        """Create a simple fallback stadium background."""
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill(BLUE)
        pygame.draw.rect(background, GRASS_GREEN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        return background

    def _draw_field(self, surface):
        """Draw simple field lines and goal hints over the background."""
        pygame.draw.line(surface, WHITE, (0, GROUND_Y), (WIDTH, GROUND_Y), 4)
        pygame.draw.line(surface, GRAY, (WIDTH // 2, GROUND_Y), (WIDTH // 2, HEIGHT), 3)

    def _create_ball_image(self):
        """Create a temporary circular ball image until final assets exist."""
        diameter = BALL_RADIUS * 2
        image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(image, WHITE, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
        pygame.draw.circle(image, BLACK, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS, 2)
        return image

    def _get_gravity_mult(self, stadium):
        """Read the optional stadium gravity multiplier."""
        if isinstance(stadium, dict):
            return stadium.get("gravity_mult", 1.0)
        return 1.0
