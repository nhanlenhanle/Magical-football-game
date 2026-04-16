from __future__ import annotations

from dataclasses import dataclass
import math
import random

import pygame

from config import OFFSET_X, OFFSET_Y
from particle import CrescentParticle, ParticleSystem, SquareParticle


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


@dataclass
class Shockwave:
    pos: pygame.Vector2
    duration: float = 0.7
    start_radius: float = 18.0
    end_radius: float = 250.0
    age: float = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        return self.age < self.duration

    def draw(self, screen: pygame.Surface) -> None:
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


class SkillEffectManager:
    def __init__(self) -> None:
        self.particles = ParticleSystem()
        self.shockwaves: list[Shockwave] = []
        self._rng = random.Random()
        self._skill_state: dict[int, bool] = {}
        self._emit_counters: dict[int, float] = {}
        self._isagi_overlay_alpha = 0.0

    def reset(self) -> None:
        self.particles.clear()
        self.shockwaves.clear()
        self._skill_state.clear()
        self._emit_counters.clear()
        self._isagi_overlay_alpha = 0.0

    def update(self, dt: float, ball, *players) -> None:
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
            else:
                self._emit_counters[player_key] = 0.0

            if player.character == "Isagi" and active_now:
                isagi_active = True

            self._skill_state[player_key] = active_now

        self.shockwaves = [wave for wave in self.shockwaves if wave.update(dt)]
        self.particles.update(dt)

        target_alpha = 105.0 if isagi_active else 0.0
        blend_speed = min(1.0, dt * 7.5)
        self._isagi_overlay_alpha += (target_alpha - self._isagi_overlay_alpha) * blend_speed

    def draw(self, screen: pygame.Surface) -> None:
        if self._isagi_overlay_alpha > 1:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            alpha = int(self._isagi_overlay_alpha)
            overlay.fill((95, 100, 110, alpha))
            screen.blit(overlay, (0, 0))

        offset = pygame.Vector2(OFFSET_X, OFFSET_Y)
        self.particles.draw(screen, offset)

        for wave in self.shockwaves:
            wave.draw(screen)

    def _on_skill_activated(self, player) -> None:
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

    def _emit_nagi_particles(self, player, dt: float) -> None:
        player_key = id(player)
        emission_rate = 28.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            self._spawn_nagi_particle(player, outer=True)

    def _burst_nagi_particles(self, player, count: int) -> None:
        for _ in range(count):
            self._spawn_nagi_particle(player, outer=False)

    def _emit_bachira_particles(self, player, ball, dt: float) -> None:
        player_key = id(player)
        emission_rate = 20.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            self._spawn_bachira_particle(player, ball, wide=True)

    def _burst_bachira_particles(self, player, count: int) -> None:
        for _ in range(count):
            self._spawn_bachira_particle(player, None, wide=False)

    def _emit_kunigami_particles(self, player, dt: float) -> None:
        player_key = id(player)
        emission_rate = 26.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            self._spawn_kunigami_particle(player, outward=False)

    def _burst_kunigami_particles(self, player, count: int) -> None:
        for _ in range(count):
            self._spawn_kunigami_particle(player, outward=True)

    def _emit_chigiri_particles(self, player, dt: float) -> None:
        player_key = id(player)
        emission_rate = 34.0
        total = self._emit_counters.get(player_key, 0.0) + dt * emission_rate
        emit_count = int(total)
        self._emit_counters[player_key] = total - emit_count

        for _ in range(emit_count):
            self._spawn_chigiri_particle(player)

    def _burst_chigiri_particles(self, player, count: int) -> None:
        for _ in range(count):
            self._spawn_chigiri_particle(player, burst=True)

    def _spawn_nagi_particle(self, player, outer: bool) -> None:
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

    def _emit_kick_particles(self, player, ball) -> None:
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
