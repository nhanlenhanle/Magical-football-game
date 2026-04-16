from __future__ import annotations

import math

import pygame

from config import BALL_RADIUS, FIELD_HEIGHT, FIELD_WIDTH, OFFSET_X, OFFSET_Y


def _vector_angle_deg(vec: pygame.Vector2) -> float | None:
    if vec.length_squared() <= 1e-6:
        return None
    return math.degrees(math.atan2(-vec.y, vec.x))


class DebugOverlay:
    def __init__(self) -> None:
        self.enabled = False
        self.show_vectors = True
        self.show_text = True
        self.show_help = True
        self._font_small: pygame.font.Font | None = None
        self._font_tiny: pygame.font.Font | None = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_F3:
            self.enabled = not self.enabled
            return True
        if event.key == pygame.K_F4:
            self.show_vectors = not self.show_vectors
            return True
        if event.key == pygame.K_F5:
            self.show_text = not self.show_text
            return True
        if event.key == pygame.K_F6:
            self.show_help = not self.show_help
            return True
        return False

    def draw(self, screen: pygame.Surface, ball, player1, player2) -> None:
        if not self.enabled:
            return

        self._ensure_fonts()

        if self.show_vectors:
            self._draw_pitch_guides(screen, ball, player1, player2)
        if self.show_text:
            self._draw_panel(screen, ball, player1, player2)
        if self.show_help:
            self._draw_help(screen)

    def _ensure_fonts(self) -> None:
        if self._font_small is None:
            self._font_small = pygame.font.SysFont("Consolas", 16)
        if self._font_tiny is None:
            self._font_tiny = pygame.font.SysFont("Consolas", 13)

    def _draw_pitch_guides(self, screen: pygame.Surface, ball, player1, player2) -> None:
        ball_pos = self._screen_pos(ball.pos)
        pygame.draw.circle(screen, (255, 245, 120), ball_pos, BALL_RADIUS + 10, 1)

        self._draw_player_vectors(screen, ball, player1, (255, 110, 110))
        self._draw_player_vectors(screen, ball, player2, (100, 190, 255))

    def _draw_player_vectors(self, screen: pygame.Surface, ball, player, color: tuple[int, int, int]) -> None:
        player_pos = self._screen_pos(player.pos)
        info = getattr(player, "debug_info", {})

        target = info.get("target")
        if target is not None:
            target_pos = self._screen_pos(target)
            pygame.draw.line(screen, (255, 214, 92), player_pos, target_pos, 2)
            pygame.draw.circle(screen, (255, 214, 92), target_pos, 4)

        intercept = info.get("intercept")
        if intercept is not None:
            intercept_pos = self._screen_pos(intercept)
            pygame.draw.line(screen, (88, 255, 210), player_pos, intercept_pos, 1)
            pygame.draw.circle(screen, (88, 255, 210), intercept_pos, 4, 1)

        shot_dir = self._get_shot_direction(player, ball)
        if shot_dir is not None:
            shot_end = player.pos + shot_dir * 65
            pygame.draw.line(screen, color, player_pos, self._screen_pos(shot_end), 3)

        pygame.draw.line(screen, (190, 190, 190), player_pos, self._screen_pos(ball.pos), 1)

    def _draw_panel(self, screen: pygame.Surface, ball, player1, player2) -> None:
        panel = pygame.Surface((360, 170), pygame.SRCALPHA)
        panel.fill((12, 16, 22, 190))
        screen.blit(panel, (12, 12))

        lines = [
            self._build_player_line("P1", player1, ball),
            self._build_player_line("P2", player2, ball),
            f"Ball speed {ball.vel.length():6.1f}",
            f"Debug: F3 all | F4 lines {'on' if self.show_vectors else 'off'} | F5 text {'on' if self.show_text else 'off'}",
        ]

        y = 20
        for line in lines:
            rendered = self._font_small.render(line, True, (238, 242, 247))
            screen.blit(rendered, (22, y))
            y += 28

    def _build_player_line(self, label: str, player, ball) -> str:
        info = getattr(player, "debug_info", {})
        shot_dir = self._get_shot_direction(player, ball)
        angle = _vector_angle_deg(shot_dir) if shot_dir is not None else None
        angle_text = "---" if angle is None else f"{angle:6.1f}"
        state = info.get("state", "IDLE")
        pressed = "Y" if info.get("is_pressed") else "N"
        should_kick = "Y" if info.get("should_kick") else "N"
        t_me = info.get("time_to_ball", 0.0)
        t_enemy = info.get("enemy_time_to_ball", 0.0)
        dist = (ball.pos - player.pos).length()

        return (
            f"{label} {str(player.character or 'None')[:8]:8} "
            f"ang {angle_text}  state {state:6}  kick {should_kick}  press {pressed}  "
            f"d {dist:6.1f}  t {t_me:4.2f}/{t_enemy:4.2f}"
        )

    def _draw_help(self, screen: pygame.Surface) -> None:
        help_text = "F3 debug  F4 vectors  F5 text  F6 help"
        rendered = self._font_tiny.render(help_text, True, (245, 245, 245))
        rect = rendered.get_rect(bottomleft=(14, OFFSET_Y + FIELD_HEIGHT + 28))
        shadow = self._font_tiny.render(help_text, True, (0, 0, 0))
        screen.blit(shadow, rect.move(1, 1))
        screen.blit(rendered, rect)

    def _get_shot_direction(self, player, ball) -> pygame.Vector2 | None:
        info = getattr(player, "debug_info", {})
        shot_dir = info.get("shot_direction")
        if isinstance(shot_dir, pygame.Vector2) and shot_dir.length_squared() > 1e-6:
            return shot_dir.normalize()

        diff = ball.pos - player.pos
        if diff.length_squared() > 1e-6:
            return diff.normalize()
        return None

    @staticmethod
    def _screen_pos(pos: pygame.Vector2) -> tuple[int, int]:
        x = int(pos.x + OFFSET_X)
        y = int(pos.y + OFFSET_Y)
        return x, y
