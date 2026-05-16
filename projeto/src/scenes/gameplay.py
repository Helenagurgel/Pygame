"""Core gameplay scene for Head Soccer DesSoft."""

import math
import random

import pygame

from src.entities.ball import Ball
from src.entities.cpu_ai import CPUController
from src.entities.player import Player
from src.entities.powerup import BigBall, FireBall, Freeze, GiantPlayer, LowGravity, SmallBall, PowerUpSpawner
from src.scenes.base_scene import Scene
from src.settings import (
    BALL_PUSH_FORCE,
    BALL_RADIUS,
    BLACK,
    BLUE,
    CELEBRATION_DURATION,
    GOAL_HEIGHT,
    GOAL_WIDTH,
    GRASS_GREEN,
    GRAY,
    GROUND_Y,
    HEIGHT,
    KICK_RANGE,
    KICKOFF_DURATION,
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
from src.utils.asset_loader import AssetLoader
from src.utils.particle import ParticleSystem


_TRAIL_SPEED_THRESHOLD = 8
_KICKOFF_ZOOM_PEAK = 1.25


class _PressedKeys:
    """Small key-state adapter used by the CPU player."""

    def __init__(self, pressed_keys):
        """Store a set with pygame key constants considered pressed."""
        self.pressed_keys = pressed_keys

    def __getitem__(self, key):
        """Return True when the requested key is active."""
        return key in self.pressed_keys


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
        self.character_p1 = character_p1 or {"name": "Jogador 1"}
        self.character_p2 = character_p2 or {"name": "Jogador 2"}
        self.gravity_mult = self._get_gravity_mult(stadium)
        self.background = self._load_background(stadium)

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

        self.player1 = Player(*self.player1_start, self.p1_controls, self._load_character_sprites(character_p1))
        self.player2 = Player(
            *self.player2_start,
            self.p2_controls,
            self._load_character_sprites(character_p2),
            facing_right=False,
        )
        self.ball = Ball(*self.ball_start, self._create_ball_image())
        self.cpu = (
            CPUController(self.player2, self.ball, self.difficulty or "medium")
            if self.mode == "1P"
            else None
        )

        # feito com IA: grupos separam sprites principais e futuros powerups.
        self.last_kicker = self.player1

        self.all_sprites = pygame.sprite.Group(self.player1, self.player2, self.ball)
        self.players = pygame.sprite.Group(self.player1, self.player2)
        self.powerups = pygame.sprite.Group()
        self.particles = ParticleSystem()
        self._powerup_spawner = PowerUpSpawner(self.powerups)
        self._powerup_effects = []  # [[powerup, target, remaining_ms], ...]

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
        self.goal_font = pygame.font.Font(None, 120)
        self.golden_goal_font = pygame.font.Font(None, 38)
        self._scorer = None
        self.golden_goal = False
        self._golden_goal_blink = 0.0

        # Pre-create fixed-size surfaces used every frame to avoid per-frame allocation.
        _glow_r = BALL_RADIUS + 8
        _glow_sz = _glow_r * 2 + 4
        self._kick_range_glow = pygame.Surface((_glow_sz, _glow_sz), pygame.SRCALPHA)
        pygame.draw.circle(
            self._kick_range_glow, (255, 255, 120, 140),
            (_glow_r + 2, _glow_r + 2), _glow_r, 3,
        )
        self._kick_glow_offset = _glow_r + 2
        self._kickoff_canvas = pygame.Surface((WIDTH, HEIGHT))

        self._music_name = stadium.get("music_name", "gameplay") if isinstance(stadium, dict) else "gameplay"
        self._player_characters = {
            self.player1: self.character_p1,
            self.player2: self.character_p2,
        }
        self.game.sounds.play_music(self._music_name)

    def handle_events(self, events):
        """Handle gameplay events, including ESC to pause."""
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                from src.scenes.pause import PauseScene
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
        if self.time_left <= 0 and not self.golden_goal:
            if self.score_p1 == self.score_p2:
                self.golden_goal = True
            else:
                from src.scenes.game_over import GameOverScene
                self.game.change_scene(
                    GameOverScene(
                        self.game,
                        self.score_p1,
                        self.score_p2,
                        self.character_p1,
                        self.character_p2,
                    )
                )
                return

        if self.golden_goal:
            self._golden_goal_blink += dt

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
            if player.just_jumped:
                self.game.sounds.play_sfx("jump")
        self.ball.update(dt, GROUND_Y, WIDTH, self.gravity_mult)
        if self.ball.just_bounced:
            self.game.sounds.play_sfx("bounce")
        self.powerups.update(dt)
        self._powerup_spawner.update(dt)
        self._update_powerup_effects(dt)
        self.particles.update(dt)

        ball_speed = math.hypot(self.ball.vel_x, self.ball.vel_y)
        if ball_speed > _TRAIL_SPEED_THRESHOLD:
            trail_color = (255, 140, 0) if self.ball.on_fire else (200, 200, 230)
            self.particles.emit_trail(
                *self.ball.rect.center,
                self.ball.vel_x, self.ball.vel_y,
                color=trail_color,
            )

        if self.ball.on_fire:
            self.particles.emit_sparkle(
                self.ball.rect.centerx + random.randint(-8, 8),
                self.ball.rect.centery + random.randint(-8, 8),
                count=1,
            )

        # feito com IA: ações de chute têm prioridade sobre empurrões passivos.
        for player in self.players:
            kick_vector = player.try_kick(self.ball)
            if kick_vector is not None:
                self.last_kicker = player
                m = self.ball.kick_mult
                self.ball.kick(kick_vector[0] * m, kick_vector[1] * m)
                self.particles.emit_sparkle(*self.ball.rect.center, count=3)
                self.game.sounds.play_sfx("kick")

        self._handle_player_ball_collisions()
        self._handle_powerup_collisions()
        self._check_goals()

    def draw(self, surface):
        """Draw the full frame: scene, celebration overlays, and HUD.

        During the kickoff state the scene is rendered to a temporary canvas
        first, then blitted to *surface* with a zoom effect centred on the
        field. During celebration the 'GOOOL!' text is drawn on top before the
        HUD so it appears beneath score and timer.
        """
        if self.state == "kickoff":
            self._draw_scene(self._kickoff_canvas)
            self._blit_with_kickoff_zoom(surface, self._kickoff_canvas)
        else:
            self._draw_scene(surface)
        if self.state == "celebrating":
            self._draw_goal_text(surface)
        self.draw_hud(surface)

    def _draw_scene(self, surface):
        """Draw all in-world elements — background, field, particles, sprites.

        Args:
            surface: Target pygame.Surface. May be the real display or a
                temporary canvas when the kickoff zoom is active.
        """
        surface.blit(self.background, (0, 0))
        self._draw_field(surface)
        self.particles.draw(surface)
        self.all_sprites.draw(surface)
        self.powerups.draw(surface)
        self._draw_powerup_overlays(surface)
        self._draw_kick_range_indicator(surface)

    def _blit_with_kickoff_zoom(self, surface, canvas):
        """Scale *canvas* with a triangular zoom and blit it onto *surface*.

        Args:
            surface: The real display surface to blit the zoomed image onto.
            canvas: A (WIDTH × HEIGHT) surface with the scene already drawn.

        The zoom peaks at _KICKOFF_ZOOM_PEAK at the midpoint of the kickoff
        window and returns smoothly to 1.0 at both ends, creating a quick
        camera-zoom-in-and-out effect centred on the screen.
        """
        progress = 1.0 - self.kickoff_timer / KICKOFF_DURATION
        if progress < 0.5:
            zoom = 1.0 + (progress * 2.0) * (_KICKOFF_ZOOM_PEAK - 1.0)
        else:
            zoom = 1.0 + ((1.0 - progress) * 2.0) * (_KICKOFF_ZOOM_PEAK - 1.0)

        if abs(zoom - 1.0) < 0.005:
            surface.blit(canvas, (0, 0))
            return

        new_w = int(WIDTH * zoom)
        new_h = int(HEIGHT * zoom)
        scaled = pygame.transform.scale(canvas, (new_w, new_h))
        surface.blit(scaled, ((WIDTH - new_w) // 2, (HEIGHT - new_h) // 2))

    def _draw_goal_text(self, surface):
        """Draw a large blinking 'GOOOL!' text centred on the screen.

        Args:
            surface: Target pygame.Surface, drawn on top of the scene but
                beneath the HUD so score and timer remain readable.

        The text blinks at approximately 5 Hz by toggling visibility based on
        ``celebration_timer`` so it is always readable during the 2-second
        window while still feeling energetic.
        """
        if int(self.celebration_timer * 5) % 2 == 0:
            return
        text = self.goal_font.render("GOOOL!", True, YELLOW)
        shadow = self.goal_font.render("GOOOL!", True, BLACK)
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        surface.blit(shadow, rect.move(5, 5))
        surface.blit(text, rect)

    def _draw_kick_range_indicator(self, surface):
        """Draw a subtle glow ring around the ball when any player can kick it.

        Args:
            surface: Target pygame.Surface where the ring is drawn.

        Checks every player's distance to the ball against KICK_RANGE. When
        at least one player is within range a semi-transparent yellow circle
        is drawn around the ball so the player knows a kick is available
        without cluttering the screen at all other times.
        """
        for player in self.players:
            dx = self.ball.rect.centerx - player.rect.centerx
            dy = self.ball.rect.centery - player.rect.centery
            if math.hypot(dx, dy) < KICK_RANGE:
                surface.blit(self._kick_range_glow, (
                    self.ball.rect.centerx - self._kick_glow_offset,
                    self.ball.rect.centery - self._kick_glow_offset,
                ))
                break

    def draw_hud(self, surface):
        """Draw score and remaining time with high-contrast colors.

        Args:
            surface: Target pygame.Surface for the HUD.

        The score is centered at the top of the screen and the remaining time
        appears just below it. Text shadows improve contrast against stadium
        backgrounds.
        """
        score_text = f"{self.score_p1}  x  {self.score_p2}"

        score_shadow = self.hud_font.render(score_text, True, BLACK)
        score_surface = self.hud_font.render(score_text, True, YELLOW)
        score_rect = score_surface.get_rect(center=(WIDTH // 2, 38))
        surface.blit(score_shadow, score_rect.move(3, 3))
        surface.blit(score_surface, score_rect)

        if self.golden_goal:
            if int(self._golden_goal_blink * 4) % 2 == 0:
                gg_color = (255, 215, 0)
                gg_text = "GOL DE OURO!"
                gg_shadow = self.golden_goal_font.render(gg_text, True, BLACK)
                gg_surface = self.golden_goal_font.render(gg_text, True, gg_color)
                gg_rect = gg_surface.get_rect(center=(WIDTH // 2, 88))
                surface.blit(gg_shadow, gg_rect.move(2, 2))
                surface.blit(gg_surface, gg_rect)
        else:
            time_text = str(max(0, int(self.time_left)))
            time_shadow = self.timer_font.render(time_text, True, BLACK)
            time_surface = self.timer_font.render(time_text, True, WHITE)
            time_rect = time_surface.get_rect(center=(WIDTH // 2, 88))
            surface.blit(time_shadow, time_rect.move(2, 2))
            surface.blit(time_surface, time_rect)

    def _update_celebration(self, dt):
        """Animate the scorer, particles, and the sparkle trickle during the post-goal window.

        Ticks the scorer's celebrate animation once per frame so the winning
        player keeps playing its special animation while the physics loop is
        paused. Also emits a small random sparkle near the scorer each frame
        to keep the celebration visually lively throughout the 2-second window.
        """
        self.celebration_timer -= dt
        self.particles.update(dt)

        if self._scorer is not None:
            self._scorer.tick_celebrate()
            if random.random() < 0.4:
                self.particles.emit_sparkle(
                    self._scorer.rect.centerx + random.randint(-20, 20),
                    self._scorer.rect.top + random.randint(-10, 10),
                    count=2,
                )

        if self.celebration_timer <= 0:
            self.game.sounds.stop_music()
            self.game.sounds.play_music(self._music_name)
            self._scorer = None
            if self.golden_goal:
                from src.scenes.game_over import GameOverScene
                self.game.change_scene(
                    GameOverScene(
                        self.game,
                        self.score_p1,
                        self.score_p2,
                        self.character_p1,
                        self.character_p2,
                    )
                )
                return
            self._reset_positions()
            self.state = "kickoff"
            self.kickoff_timer = KICKOFF_DURATION

    def _handle_player_ball_collisions(self):
        """Push the ball softly when a player's mask overlaps the ball's mask.

        Uses pixel-perfect mask collision (pygame.sprite.collide_mask) so the
        push only triggers when the player sprite visually touches the ball,
        not just when their bounding boxes overlap. Both sprites must have a
        ``mask`` attribute; Player.update() and Ball._rotate_from_velocity()
        rebuild their masks every frame.
        """
        for player in self.players:
            if player.is_kicking:
                continue
            if not pygame.sprite.collide_mask(player, self.ball):
                continue

            dx = self.ball.rect.centerx - player.rect.centerx
            dy = self.ball.rect.centery - player.rect.centery
            if dx == 0 and dy == 0:
                dx = 1

            length = max(1, (dx * dx + dy * dy) ** 0.5)
            nx = dx / length
            ny = dy / length

            # Fully resolve penetration: push until masks no longer overlap.
            for _ in range(30):
                if not pygame.sprite.collide_mask(player, self.ball):
                    break
                mx = int(nx * 3) or (1 if nx >= 0 else -1)
                my = int(ny * 3) or (1 if ny >= 0 else -1)
                self.ball.rect.x += mx
                self.ball.rect.y += my

            # Reflect any inward velocity so the ball bounces off cleanly.
            dot = self.ball.vel_x * nx + self.ball.vel_y * ny
            approach = -dot
            if dot < 0:
                self.ball.vel_x -= 2 * dot * nx
                self.ball.vel_y -= 2 * dot * ny

            if approach > 3:
                self.game.sounds.play_sfx("bounce")
                self.particles.emit_sparkle(*self.ball.rect.center, count=1)

            self.ball.vel_x += nx * BALL_PUSH_FORCE
            # Never push the ball downward; let gravity handle it.
            self.ball.vel_y += min(ny, 0) * BALL_PUSH_FORCE

    def _check_goals(self):
        """Detect goals, update score, and start celebration state."""
        if self.left_goal.collidepoint(self.ball.rect.center):
            self.score_p2 += 1
            self._start_goal_celebration(self.player2, self.left_goal)
        elif self.right_goal.collidepoint(self.ball.rect.center):
            self.score_p1 += 1
            self._start_goal_celebration(self.player1, self.right_goal)

    def _start_goal_celebration(self, scorer, goal_rect):
        """Begin the two-second goal celebration after scoring.

        Args:
            scorer: The Player who scored the goal. Their celebrate animation
                will play for the duration of the celebration window.
            goal_rect: The pygame.Rect of the goal mouth where the ball
                entered, used to emit the particle burst at the right spot.

        Emits a large particle burst inside the goal mouth and a secondary
        burst at the ball position, stores the scorer for animation ticking,
        and plays the goal and whistle sound effects.
        """
        self._scorer = scorer
        self.state = "celebrating"
        self.celebration_timer = CELEBRATION_DURATION
        self.ball.vel_x = 0
        self.ball.vel_y = 0
        for _ in range(4):
            self.particles.emit_sparkle(
                goal_rect.centerx + random.randint(-goal_rect.width // 2, goal_rect.width // 2),
                goal_rect.centery + random.randint(-goal_rect.height // 2, goal_rect.height // 2),
                count=7,
            )
        self.particles.emit_sparkle(*self.ball.rect.center, count=12)
        char_name = self._player_characters[scorer].get("name", "")
        self.game.sounds.play_goal_celebration(char_name)
        self.game.sounds.play_sfx("whistle")

    def _reset_positions(self):
        """Reset players and ball to kickoff positions after a goal."""
        self._clear_powerup_effects()
        self.last_kicker = self.player1
        self.player1.rect.topleft = self.player1_start
        self.player1.vel_x = 0
        self.player1.vel_y = 0
        self.player1.facing_right = True
        self.player2.rect.topleft = self.player2_start
        self.player2.vel_x = 0
        self.player2.vel_y = 0
        self.player2.facing_right = False
        self.ball.reset(*self.ball_start)

    def _update_powerup_effects(self, dt):
        """Tick all active power-up effect timers and expire finished ones."""
        for i in reversed(range(len(self._powerup_effects))):
            effect = self._powerup_effects[i]
            effect[2] -= dt * 1000
            if effect[2] <= 0:
                effect[0].expire(effect[1])
                self._powerup_effects.pop(i)

    def _handle_powerup_collisions(self):
        """Collect field power-ups on ball contact only.

        All power-ups are activated when the ball touches them.
        GiantPlayer benefits the last player who kicked the ball.
        Freeze targets the opponent of that last kicker.
        LowGravity targets the scene to modify gravity_mult.
        A power-up type already active is ignored to prevent stacking.
        """
        for powerup in list(self.powerups):
            cls = type(powerup)
            if any(isinstance(e[0], cls) for e in self._powerup_effects):
                continue

            if not powerup.rect.colliderect(self.ball.rect):
                continue

            if isinstance(powerup, (FireBall, BigBall, SmallBall)):
                target = self.ball
            elif isinstance(powerup, Freeze):
                target = self.player2 if self.last_kicker is self.player1 else self.player1
            elif isinstance(powerup, LowGravity):
                target = self
            else:
                target = self.last_kicker

            powerup.kill()
            powerup.apply(target)
            self._powerup_effects.append([powerup, target, powerup.duration_ms])
            self.particles.emit_sparkle(*powerup.rect.center, count=6)
            self.game.sounds.play_sfx("powerup")

    def _clear_powerup_effects(self):
        """Expire all active effects on goal; field power-ups and spawn timer persist."""
        for effect in self._powerup_effects:
            effect[0].expire(effect[1])
        self._powerup_effects.clear()

    def _draw_powerup_overlays(self, surface):
        """Draw tinted overlays on frozen players and the flaming ball."""
        for player in self.players:
            if player.frozen:
                overlay = pygame.Surface(player.rect.size, pygame.SRCALPHA)
                overlay.fill((100, 180, 255, 110))
                surface.blit(overlay, player.rect)
        if self.ball.on_fire:
            overlay = pygame.Surface(self.ball.rect.size, pygame.SRCALPHA)
            overlay.fill((255, 100, 0, 100))
            surface.blit(overlay, self.ball.rect)

    def _get_cpu_keys(self):
        """Return CPU key state from the difficulty-aware AI controller."""
        decision = self.cpu.decide(0)
        pressed = set()
        if decision["left"]:
            pressed.add(self.p2_controls["left"])
        if decision["right"]:
            pressed.add(self.p2_controls["right"])
        if decision["jump"]:
            pressed.add(self.p2_controls["jump"])
        if decision["kick"]:
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
        """Load the ball sprite, falling back to a drawn circle if missing."""
        diameter = BALL_RADIUS * 2
        try:
            image = pygame.image.load("assets/images/ball/Bola.png").convert_alpha()
            return pygame.transform.scale(image, (diameter, diameter))
        except (pygame.error, FileNotFoundError, OSError):
            image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(image, WHITE, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
            pygame.draw.circle(image, BLACK, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS, 2)
            return image

    def _get_gravity_mult(self, stadium):
        """Read the optional stadium gravity multiplier."""
        if isinstance(stadium, dict):
            return stadium.get("gravity_mult", 1.0)
        return 1.0

    @staticmethod
    def _load_character_sprites(character_data):
        """Return a copy of character_data with sprites populated from sprite_path."""
        import copy
        data = copy.copy(character_data)
        sprite_path = data.get("sprite_path", "")
        frame = AssetLoader.load_image(
            sprite_path, scale=(PLAYER_WIDTH, PLAYER_HEIGHT)
        )
        data["sprites"] = {state: [frame] for state in ("idle", "run", "jump", "kick", "celebrate")}
        return data
