from __future__ import annotations

import copy
from dataclasses import dataclass
import math
from pathlib import Path
import random

import pygame

from config import ITACHI_FRAME_ALPHA, ITACHI_FRAME_DIR, ITACHI_FRAME_DURATION, OFFSET_X, OFFSET_Y
from particle import CrescentParticle, ParticleSystem, SquareParticle


def _ease_out_cubic(t: float) -> float:
    """Làm mượt giá trị chuẩn hóa theo kiểu nhanh lúc đầu và chậm dần về cuối."""
    return 1.0 - (1.0 - t) ** 3


@dataclass
class Shockwave:
    """Hiệu ứng vòng tròn lan rộng khi một số kỹ năng được kích hoạt."""

    pos: pygame.Vector2
    duration: float = 0.7
    start_radius: float = 18.0
    end_radius: float = 250.0
    age: float = 0.0

    def update(self, dt: float) -> bool:
        """Cập nhật shockwave và trả về True nếu hiệu ứng còn tồn tại."""
        self.age += dt
        return self.age < self.duration

    def draw(self, screen: pygame.Surface) -> None:
        """Vẽ shockwave dưới dạng vòng tròn lan rộng và mờ dần."""
        progress = min(1.0, self.age / self.duration)
        eased = _ease_out_cubic(progress)
        radius = self.start_radius + (self.end_radius - self.start_radius) * eased
        alpha = int(180 * (1.0 - progress))
        width = max(2, int(7 - progress * 4))

        size = int(radius * 2 + width * 6)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(surface, (230, 235, 245, alpha), center, int(radius), width)
        screen.blit(surface, (self.pos.x + OFFSET_X - size / 2, self.pos.y + OFFSET_Y - size / 2))


@dataclass
class ConvergeCircle:
    """Hiệu ứng vòng tròn hội tụ sau khi kỹ năng quay ngược của Itachi kết thúc."""

    pos: pygame.Vector2
    duration: float = 0.9
    start_radius: float = 360.0
    end_radius: float = 22.0
    age: float = 0.0

    def update(self, dt: float) -> bool:
        """Cập nhật hiệu ứng hội tụ và trả về True nếu nó còn hiển thị."""
        self.age += dt
        return self.age < self.duration

    def draw(self, screen: pygame.Surface) -> None:
        """Vẽ vòng tròn mờ dần và co lại về vị trí mục tiêu."""
        progress = min(1.0, self.age / self.duration)
        eased = _ease_out_cubic(progress)
        radius = self.start_radius + (self.end_radius - self.start_radius) * eased
        alpha = int(220 * (1.0 - progress))
        width = max(3, int(10 - progress * 5))

        size = int(radius * 2 + width * 6)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(surface, (180, 40, 210, alpha), center, int(radius), width)
        pygame.draw.circle(surface, (245, 235, 255, max(0, alpha - 30)), center, max(4, int(radius * 0.25)), 2)
        screen.blit(surface, (self.pos.x + OFFSET_X - size / 2, self.pos.y + OFFSET_Y - size / 2))


class SkillEffectManager:
    """Quản lý toàn bộ hiệu ứng tạm thời từ cú sút và kỹ năng nhân vật."""

    def __init__(self) -> None:
        """Khởi tạo danh sách hiệu ứng rỗng và trạng thái overlay."""
        self.particles = ParticleSystem()
        self.shockwaves: list[Shockwave] = []
        self._rng = random.Random()
        self._skill_state: dict[int, bool] = {}
        self._emit_counters: dict[int, float] = {}
        self._isagi_overlay_alpha = 0.0
        self._itachi_overlay_alpha = 0.0
        self._itachi_frame_time = 0.0
        self._itachi_frames: list[pygame.Surface] | None = None
        self._itachi_frames_failed = False
        self._converge_circles: list[ConvergeCircle] = []

    def reset(self) -> None:
        """Xóa mọi particle, sóng, overlay và trạng thái kỹ năng đang lưu."""
        self.particles.clear()
        self.shockwaves.clear()
        self._converge_circles.clear()
        self._skill_state.clear()
        self._emit_counters.clear()
        self._isagi_overlay_alpha = 0.0
        self._itachi_overlay_alpha = 0.0
        self._itachi_frame_time = 0.0

    def get_state(self) -> dict:
        """Chụp snapshot deep-copy để phát lại replay hoặc quay ngược thời gian."""
        return {
            "particles": copy.deepcopy(self.particles.particles),
            "shockwaves": copy.deepcopy(self.shockwaves),
            "converge_circles": copy.deepcopy(self._converge_circles),
            "skill_state": self._skill_state.copy(),
            "emit_counters": self._emit_counters.copy(),
            "isagi_overlay_alpha": self._isagi_overlay_alpha,
            "itachi_overlay_alpha": self._itachi_overlay_alpha,
            "itachi_frame_time": self._itachi_frame_time,
        }

    def set_state(self, state: dict | None) -> None:
        """Khôi phục snapshot hiệu ứng đã được chụp trước đó."""
        if state is None:
            self.reset()
            return

        self.particles.particles = copy.deepcopy(state["particles"])
        self.shockwaves = copy.deepcopy(state["shockwaves"])
        self._converge_circles = copy.deepcopy(state.get("converge_circles", []))
        self._skill_state = state["skill_state"].copy()
        self._emit_counters = state["emit_counters"].copy()
        self._isagi_overlay_alpha = state["isagi_overlay_alpha"]
        # Itachi screen animation is controlled by the live rewind timeline.
        # Replaying old effect snapshots here would keep snapping it back to frame 0.

    def set_itachi_overlay(self, active: bool, dt: float) -> None:
        """Làm mượt overlay tối của Itachi theo hướng hiện hoặc ẩn."""
        target_alpha = float(ITACHI_FRAME_ALPHA) if active else 0.0
        blend_speed = min(1.0, dt * 9.0)
        self._itachi_overlay_alpha += (target_alpha - self._itachi_overlay_alpha) * blend_speed
        if active:
            self._itachi_frame_time = min(ITACHI_FRAME_DURATION, self._itachi_frame_time + dt)
        elif self._itachi_overlay_alpha <= 1:
            self._itachi_frame_time = 0.0

    def start_itachi_converge(self, pos: pygame.Vector2) -> None:
        """Tạo vòng tròn hội tụ sau rewind tại vị trí của Itachi."""
        self._converge_circles.append(ConvergeCircle(pos.copy()))

    def update_freeze_effects(self, dt: float) -> None:
        """Chỉ cập nhật hiệu ứng ở pha đứng hình khi gameplay đang tạm dừng."""
        self._converge_circles = [circle for circle in self._converge_circles if circle.update(dt)]
        self.set_itachi_overlay(False, dt)

    def update(self, dt: float, ball, *players) -> None:
        """Cập nhật particle kỹ năng, tia sút, shockwave và overlay trong một frame."""
        isagi_active = False

        for player in players:
            if player is None:
                continue

            player_key = id(player)
            active_now = bool(player.skill_active)
            was_active = self._skill_state.get(player_key, False)

            if active_now and not was_active:
                self._on_skill_activated(player)

            if player.just_kicked:
                self._emit_kick_particles(player, ball)
                player.just_kicked = False

            if player.character == "Nagi" and active_now:
                self._emit_nagi_particles(player, dt)
            elif player.character == "Bachira" and active_now:
                self._emit_bachira_particles(player, ball, dt)
            elif player.character == "Kunigami" and active_now:
                self._emit_kunigami_particles(player, dt)
            elif player.character == "Chigiri" and active_now:
                self._emit_chigiri_particles(player, dt)
            elif player.character == "Itachi" and active_now:
                self._emit_itachi_particles(player, dt)
            else:
                self._emit_counters[player_key] = 0.0

            if player.character == "Isagi" and active_now:
                isagi_active = True

            self._skill_state[player_key] = active_now

        self.shockwaves = [wave for wave in self.shockwaves if wave.update(dt)]
        self._converge_circles = [circle for circle in self._converge_circles if circle.update(dt)]
        self.particles.update(dt)

        target_alpha = 105.0 if isagi_active else 0.0
        blend_speed = min(1.0, dt * 7.5)
        self._isagi_overlay_alpha += (target_alpha - self._isagi_overlay_alpha) * blend_speed
        self.set_itachi_overlay(False, dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Vẽ overlay trước, sau đó đến particle, shockwave và vòng hội tụ."""
        if self._itachi_overlay_alpha > 1:
            if not self._draw_itachi_frame_overlay(screen):
                overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                alpha = int(self._itachi_overlay_alpha)
                overlay.fill((12, 8, 22, alpha))
                screen.blit(overlay, (0, 0))

        if self._isagi_overlay_alpha > 1:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            alpha = int(self._isagi_overlay_alpha)
            overlay.fill((95, 100, 110, alpha))
            screen.blit(overlay, (0, 0))

        offset = pygame.Vector2(OFFSET_X, OFFSET_Y)
        self.particles.draw(screen, offset)

        for wave in self.shockwaves:
            wave.draw(screen)

        for circle in self._converge_circles:
            circle.draw(screen)

    def _load_itachi_frames(self) -> list[pygame.Surface]:
        if self._itachi_frames is not None or self._itachi_frames_failed:
            return self._itachi_frames or []

        frame_paths = sorted(Path(ITACHI_FRAME_DIR).glob("*.png"))
        if not frame_paths:
            self._itachi_frames_failed = True
            return []

        try:
            frames = []
            for path in frame_paths:
                frames.append(pygame.image.load(str(path)).convert_alpha())
            self._itachi_frames = frames
        except pygame.error:
            self._itachi_frames = []
            self._itachi_frames_failed = True

        return self._itachi_frames or []

    def _draw_itachi_frame_overlay(self, screen: pygame.Surface) -> bool:
        frames = self._load_itachi_frames()
        if not frames:
            return False

        progress = min(1.0, self._itachi_frame_time / ITACHI_FRAME_DURATION)
        frame_index = min(len(frames) - 1, int(progress * len(frames)))
        frame = frames[frame_index]
        screen_w, screen_h = screen.get_size()
        scale = max(screen_w / frame.get_width(), screen_h / frame.get_height())
        draw_size = (int(frame.get_width() * scale), int(frame.get_height() * scale))

        scaled_frame = pygame.transform.smoothscale(frame, draw_size)
        scaled_frame.set_alpha(int(self._itachi_overlay_alpha))
        screen.blit(
            scaled_frame,
            ((screen_w - draw_size[0]) // 2, (screen_h - draw_size[1]) // 2),
        )
        return True

    def _on_skill_activated(self, player) -> None:
        """Phát hiệu ứng bùng nổ một lần khi kỹ năng vừa được kích hoạt."""
        if player.character == "Isagi":
            self.shockwaves.append(Shockwave(player.pos.copy()))
        elif player.character == "Nagi":
            self._burst_nagi_particles(player, count=16)
        elif player.character == "Bachira":
            self._burst_bachira_particles(player, count=16)
        elif player.character == "Kunigami":
            self._burst_kunigami_particles(player, count=18)
        elif player.character == "Chigiri":
            self._burst_chigiri_particles(player, count=14)
        elif player.character == "Itachi":
            self.shockwaves.append(Shockwave(player.pos.copy(), duration=0.55, end_radius=190.0))

    def _emit_nagi_particles(self, player, dt: float) -> None:
        """Phát particle bay quanh Nagi liên tục khi kỹ năng đang bật."""
        player_key = id(player)
        emission_rate = 28.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            self._spawn_nagi_particle(player, outer=True)

    def _burst_nagi_particles(self, player, count: int) -> None:
        """Phát hiệu ứng bùng nổ ban đầu của Nagi."""
        for _ in range(count):
            self._spawn_nagi_particle(player, outer=False)

    def _emit_bachira_particles(self, player, ball, dt: float) -> None:
        """Phát particle của Bachira quanh bóng khi kỹ năng đang bật."""
        player_key = id(player)
        emission_rate = 20.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            self._spawn_bachira_particle(player, ball, wide=True)

    def _burst_bachira_particles(self, player, count: int) -> None:
        """Phát hiệu ứng bùng nổ ban đầu của Bachira."""
        for _ in range(count):
            self._spawn_bachira_particle(player, None, wide=False)

    def _emit_kunigami_particles(self, player, dt: float) -> None:
        """Phát vệt lửa của Kunigami khi kỹ năng đang bật."""
        player_key = id(player)
        emission_rate = 26.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            self._spawn_kunigami_particle(player, outward=False)

    def _burst_kunigami_particles(self, player, count: int) -> None:
        """Phát hiệu ứng bùng nổ ban đầu của Kunigami."""
        for _ in range(count):
            self._spawn_kunigami_particle(player, outward=True)

    def _emit_chigiri_particles(self, player, dt: float) -> None:
        """Phát vệt tốc độ của Chigiri khi kỹ năng đang bật."""
        player_key = id(player)
        emission_rate = 34.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            self._spawn_chigiri_particle(player)

    def _burst_chigiri_particles(self, player, count: int) -> None:
        """Phát hiệu ứng tăng tốc ban đầu của Chigiri."""
        for _ in range(count):
            self._spawn_chigiri_particle(player, burst=True)

    def _spawn_nagi_particle(self, player, outer: bool) -> None:
        """Tạo một particle hình lưỡi liềm của Nagi bay về phía cầu thủ."""
        angle = self._rng.uniform(0.0, math.tau)
        direction = pygame.Vector2(math.cos(angle), math.sin(angle))
        min_radius, max_radius = (85.0, 145.0) if outer else (50.0, 110.0)
        distance = self._rng.uniform(min_radius, max_radius)

        spawn_pos = player.pos + direction * distance
        tangent = pygame.Vector2(-direction.y, direction.x) * self._rng.uniform(-25.0, 25.0)
        inward_velocity = -direction * self._rng.uniform(80.0, 140.0)

        moon = CrescentParticle(
            pos=spawn_pos,
            vel=inward_velocity + tangent,
            lifetime=self._rng.uniform(0.55, 1.0),
            color=(236, 240, 255),
            size=self._rng.uniform(4.0, 7.0),
            end_size=0.8,
            alpha=self._rng.randint(160, 230),
            drag=1.0,
            target_getter=lambda player=player: player.pos,
            seek_strength=self._rng.uniform(180.0, 320.0),
            max_speed=260.0,
        )
        self.particles.emit(moon)

    def _spawn_bachira_particle(self, player, ball, wide: bool) -> None:
        """Tạo một particle hình vuông của Bachira gần cầu thủ hoặc bóng."""
        center = ball.pos if ball is not None else player.pos
        angle = self._rng.uniform(0.0, math.tau)
        orbit = pygame.Vector2(math.cos(angle), math.sin(angle))
        spread = self._rng.uniform(26.0, 80.0 if wide else 55.0)
        origin = pygame.Vector2(center) + orbit * spread
        velocity = orbit.rotate(self._rng.uniform(-65.0, 65.0)) * self._rng.uniform(35.0, 90.0)

        particle = SquareParticle(
            pos=origin,
            vel=velocity,
            lifetime=self._rng.uniform(0.45, 0.8),
            color=(255, 214, 52),
            size=self._rng.uniform(3.0, 6.0),
            end_size=0.8,
            alpha=self._rng.randint(150, 220),
            drag=1.3,
            angle=self._rng.uniform(0.0, 360.0),
            spin=self._rng.uniform(-320.0, 320.0),
        )
        self.particles.emit(particle)

    def _spawn_kunigami_particle(self, player, outward: bool) -> None:
        """Tạo một particle tia lửa của Kunigami."""
        angle = self._rng.uniform(0.0, math.tau)
        direction = pygame.Vector2(math.cos(angle), math.sin(angle))
        origin = player.pos + direction * self._rng.uniform(6.0, 18.0)
        speed = self._rng.uniform(45.0, 110.0 if outward else 70.0)

        ember = SquareParticle(
            pos=origin,
            vel=direction * speed,
            lifetime=self._rng.uniform(0.4, 0.75),
            color=self._rng.choice([(255, 111, 44), (255, 154, 61), (255, 204, 110)]),
            size=self._rng.uniform(3.5, 6.5),
            end_size=0.9,
            alpha=self._rng.randint(150, 230),
            drag=1.8,
            gravity=pygame.Vector2(0, -15),
            angle=self._rng.uniform(0.0, 360.0),
            spin=self._rng.uniform(-240.0, 240.0),
        )
        self.particles.emit(ember)

    def _spawn_chigiri_particle(self, player, burst: bool = False) -> None:
        """Tạo một vệt tốc độ của Chigiri phía sau cầu thủ."""
        move_dir = player.vel.normalize() if player.vel.length_squared() > 1e-6 else pygame.Vector2(1, 0)
        side = pygame.Vector2(-move_dir.y, move_dir.x) * self._rng.uniform(-8.0, 8.0)
        origin = player.pos - move_dir * self._rng.uniform(8.0, 18.0) + side
        velocity = -move_dir * self._rng.uniform(70.0, 150.0 if burst else 120.0) + side * 3.0

        streak = SquareParticle(
            pos=origin,
            vel=velocity,
            lifetime=self._rng.uniform(0.24, 0.45),
            color=self._rng.choice([(255, 94, 122), (255, 142, 163), (255, 215, 223)]),
            size=self._rng.uniform(2.8, 5.0),
            end_size=0.6,
            alpha=self._rng.randint(150, 215),
            drag=2.4,
            angle=self._rng.uniform(0.0, 360.0),
            spin=self._rng.uniform(-420.0, 420.0),
        )
        self.particles.emit(streak)

    def _emit_itachi_particles(self, player, dt: float) -> None:
        """Phát particle tối quanh người dùng kỹ năng quay ngược của Itachi."""
        player_key = id(player)
        emission_rate = 24.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            angle = self._rng.uniform(0.0, math.tau)
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))
            origin = player.pos + direction * self._rng.uniform(25.0, 90.0)
            velocity = -direction * self._rng.uniform(45.0, 120.0)

            particle = SquareParticle(
                pos=origin,
                vel=velocity,
                lifetime=self._rng.uniform(0.35, 0.75),
                color=self._rng.choice([(120, 35, 180), (170, 50, 210), (235, 230, 255)]),
                size=self._rng.uniform(3.0, 5.5),
                end_size=0.6,
                alpha=self._rng.randint(145, 220),
                drag=1.6,
                angle=self._rng.uniform(0.0, 360.0),
                spin=self._rng.uniform(-300.0, 300.0),
            )
            self.particles.emit(particle)

    def _emit_kick_particles(self, player, ball) -> None:
        """Phát tia sáng nhỏ theo hướng của cú sút."""
        if ball is None:
            return

        kick_dir = player.last_kick_direction
        if kick_dir.length_squared() <= 1e-6:
            kick_dir = pygame.Vector2(1 if getattr(player, "spawn_x", 0) <= getattr(ball.pos, "x", 0) else -1, 0)
        else:
            kick_dir = kick_dir.normalize()

        for _ in range(8):
            spread = kick_dir.rotate(self._rng.uniform(-55.0, 55.0))
            speed = self._rng.uniform(80.0, 180.0)
            color = self._rng.choice([(255, 255, 255), (224, 239, 255), (255, 225, 150)])

            spark = SquareParticle(
                pos=ball.pos.copy(),
                vel=spread * speed,
                lifetime=self._rng.uniform(0.18, 0.35),
                color=color,
                size=self._rng.uniform(2.2, 4.2),
                end_size=0.5,
                alpha=self._rng.randint(150, 220),
                drag=3.2,
                angle=self._rng.uniform(0.0, 360.0),
                spin=self._rng.uniform(-540.0, 540.0),
            )
            self.particles.emit(spark)
