import pygame
from config import *


class Player:
    def __init__(self, x, y, color):
        self.kick_timer = 0
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.color = color

    def handle_input(self, keys, dt):
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_d]:
            direction.x += 1

        if direction.length() > 0:
            direction = direction.normalize()
            self.vel += direction * PLAYER_ACCELERATION * dt

    def update(self, dt):
        self.vel *= PLAYER_DAMPING

        # Giới hạn tốc độ tối đa
        if self.vel.length() > PLAYER_MAX_SPEED:
            self.vel.scale_to_length(PLAYER_MAX_SPEED)

        self.pos += self.vel * dt

        if self.kick_timer > 0:
            self.kick_timer -= dt
            
    def handle_wall_collision(self):

        min_x = -GOAL_DEPTH
        max_x = FIELD_WIDTH + GOAL_DEPTH

        min_y = -TOP_BOTTOM_MARGIN
        max_y = FIELD_HEIGHT + TOP_BOTTOM_MARGIN

        if self.pos.x - PLAYER_RADIUS < min_x:
            self.pos.x = min_x + PLAYER_RADIUS

        if self.pos.x + PLAYER_RADIUS > max_x:
            self.pos.x = max_x - PLAYER_RADIUS

        if self.pos.y - PLAYER_RADIUS < min_y:
            self.pos.y = min_y + PLAYER_RADIUS

        if self.pos.y + PLAYER_RADIUS > max_y:
            self.pos.y = max_y - PLAYER_RADIUS

    def kick(self, ball):

        if self.kick_timer > 0:
            return

        diff = ball.pos - self.pos
        distance = diff.length()
        min_dist = PLAYER_RADIUS + BALL_RADIUS + KICK_RANGE

        if distance < min_dist and distance != 0:

            direction = diff.normalize()
            ball.vel += direction * KICK_FORCE
            self.kick_timer = KICK_COOLDOWN

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.pos.x + OFFSET_X), int(self.pos.y + OFFSET_Y)),
            PLAYER_RADIUS
        )
    def handle_ball_collision(self, ball):
        diff = ball.pos - self.pos
        distance = diff.length()
        min_dist = PLAYER_RADIUS + BALL_RADIUS

        if distance < min_dist and distance != 0:

            normal = diff.normalize()
            overlap = min_dist - distance

            # Tách hai vật ra
            total_mass = PLAYER_MASS + BALL_MASS
            ball.pos += normal * (overlap * (PLAYER_MASS / total_mass))
            self.pos -= normal * (overlap * (BALL_MASS / total_mass))

            # Relative velocity
            relative_velocity = ball.vel - self.vel
            vel_along_normal = relative_velocity.dot(normal)

            if vel_along_normal > 0:
                return True

            impulse = -(1 + RESTITUTION_BALL_AND_PLAYER) * vel_along_normal
            impulse /= (1 / PLAYER_MASS + 1 / BALL_MASS)

            impulse_vector = impulse * normal

            ball.vel += impulse_vector / BALL_MASS
            self.vel -= impulse_vector / PLAYER_MASS
            return True

        return False
