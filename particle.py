from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional
import math

import pygame


VectorGetter = Callable[[], pygame.Vector2]


def _lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def _smoothstep(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    lifetime: float
    color: tuple[int, int, int]
    size: float
    end_size: Optional[float] = None
    alpha: int = 255
    drag: float = 2.0
    gravity: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    target_getter: Optional[VectorGetter] = None
    seek_strength: float = 0.0
    max_speed: Optional[float] = None
    age: float = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age >= self.lifetime:
            return False

        if self.target_getter is not None:
            target = pygame.Vector2(self.target_getter())
            diff = target - self.pos
            distance = diff.length()
            if distance > 0:
                self.vel += diff.normalize() * self.seek_strength * dt
                if self.max_speed and self.vel.length() > self.max_speed:
                    self.vel.scale_to_length(self.max_speed)
                if distance < max(6.0, self.current_size() * 0.7):
                    return False

        self.vel += self.gravity * dt
        damping = max(0.0, 1.0 - self.drag * dt)
        self.vel *= damping
        self.pos += self.vel * dt
        return True

    def current_size(self) -> float:
        t = self.progress()
        end_size = self.end_size if self.end_size is not None else self.size
        return _lerp(self.size, end_size, _smoothstep(t))

    def current_alpha(self) -> int:
        fade = 1.0 - self.progress()
        return max(0, min(255, int(self.alpha * fade)))

    def progress(self) -> float:
        if self.lifetime <= 0:
            return 1.0
        return max(0.0, min(1.0, self.age / self.lifetime))

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        radius = max(1, int(self.current_size()))
        alpha = self.current_alpha()
        if alpha <= 0:
            return

        size = radius * 2 + 4
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(surface, (*self.color, alpha), center, radius)
        screen.blit(surface, (self.pos.x + offset.x - size / 2, self.pos.y + offset.y - size / 2))


@dataclass
class CrescentParticle(Particle):
    cut_ratio: float = 0.72
    cut_shift: float = 0.45

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        radius = max(2, int(self.current_size()))
        alpha = self.current_alpha()
        if alpha <= 0:
            return

        size = radius * 4
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = pygame.Vector2(size / 2, size / 2)

        if self.vel.length_squared() > 1e-6:
            direction = self.vel.normalize()
        else:
            direction = pygame.Vector2(-1, 0)

        offset_dir = pygame.Vector2(math.cos(math.atan2(direction.y, direction.x)),
                                    math.sin(math.atan2(direction.y, direction.x)))
        cut_center = center + offset_dir * (radius * self.cut_shift)
        moon_color = (*self.color, alpha)

        pygame.draw.circle(surface, moon_color, center, radius)
        pygame.draw.circle(surface, (0, 0, 0, 0), cut_center, max(1, int(radius * self.cut_ratio)))

        screen.blit(surface, (self.pos.x + offset.x - size / 2, self.pos.y + offset.y - size / 2))


@dataclass
class SquareParticle(Particle):
    angle: float = 0.0
    spin: float = 0.0

    def update(self, dt: float) -> bool:
        alive = super().update(dt)
        self.angle += self.spin * dt
        return alive

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        size = max(2, int(self.current_size() * 2))
        alpha = self.current_alpha()
        if alpha <= 0:
            return

        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surface, (*self.color, alpha), (0, 0, size, size), border_radius=max(0, size // 6))
        if abs(self.angle) > 0.01:
            surface = pygame.transform.rotate(surface, self.angle)

        rect = surface.get_rect(center=(self.pos.x + offset.x, self.pos.y + offset.y))
        screen.blit(surface, rect)


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def emit(self, particle: Particle) -> None:
        self.particles.append(particle)

    def clear(self) -> None:
        self.particles.clear()

    def update(self, dt: float) -> None:
        alive_particles = []
        for particle in self.particles:
            if particle.update(dt):
                alive_particles.append(particle)
        self.particles = alive_particles

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        for particle in self.particles:
            particle.draw(screen, offset)
