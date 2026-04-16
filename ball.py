import pygame
from config import *


class Ball:
    def __init__(self):
        self.pos = pygame.Vector2(FIELD_WIDTH // 2, FIELD_HEIGHT // 2)
        self.vel = pygame.Vector2(0, 0)

    # def apply_input(self, keys, dt):
    #     if keys[pygame.K_UP]:
    #         self.vel.y -= FORCE * dt
    #     if keys[pygame.K_DOWN]:
    #         self.vel.y += FORCE * dt
    #     if keys[pygame.K_LEFT]:
    #         self.vel.x -= FORCE * dt
    #     if keys[pygame.K_RIGHT]:
    #         self.vel.x += FORCE * dt

    def update(self, player1, player2, dt):
        self.vel *= BALL_DAMPING

        # Giới hạn tốc độ tối đa
        can_move = True
        if self.vel.length() > BALL_MAX_SPEED:
            self.vel.scale_to_length(BALL_MAX_SPEED)
        if player1.skill_active and player1.skill_timer > 0 and player1.character == "Isagi":
            can_move = False
        if player2.skill_active and player2.skill_timer > 0 and player2.character == "Isagi":
            can_move = False
        if can_move:
            self.pos += self.vel * dt

    def handle_wall_collision(self):

        # Top
        if self.pos.y - BALL_RADIUS < 0:
            self.pos.y = BALL_RADIUS
            self.vel.y *= -RESTITUTION

        # Bottom
        if self.pos.y + BALL_RADIUS > FIELD_HEIGHT:
            self.pos.y = FIELD_HEIGHT - BALL_RADIUS
            self.vel.y *= -RESTITUTION

        # Left
        if self.pos.x - BALL_RADIUS < 0:
            if GOAL_TOP < self.pos.y < GOAL_BOTTOM:
                if self.pos.x + BALL_RADIUS /3 < 0:
                    return "BLUE_GOAL"
            else:
                self.pos.x = BALL_RADIUS
                self.vel.x *= -RESTITUTION

        # Right
        if self.pos.x + BALL_RADIUS > FIELD_WIDTH:
            if GOAL_TOP < self.pos.y < GOAL_BOTTOM:
                if self.pos.x - BALL_RADIUS /3 > FIELD_WIDTH:
                    return "RED_GOAL"
            else:
                self.pos.x = FIELD_WIDTH - BALL_RADIUS
                self.vel.x *= -RESTITUTION

        return None
    def handle_post_collision(self):

        posts = [
            pygame.Vector2(0, GOAL_TOP),
            pygame.Vector2(0, GOAL_BOTTOM),
            pygame.Vector2(FIELD_WIDTH, GOAL_TOP),
            pygame.Vector2(FIELD_WIDTH, GOAL_BOTTOM),
        ]

        for post in posts:

            diff = self.pos - post
            distance = diff.length()

            min_dist = BALL_RADIUS + POST_RADIUS

            if distance < min_dist and distance != 0:

                # Normalize
                normal = diff.normalize()

                # Push ball out
                self.pos = post + normal * min_dist

                # Reflect velocity
                self.vel = self.vel - 2 * self.vel.dot(normal) * normal
                # nhẹ damping sau va chạm vào cột
                self.vel *= 0.9
    def reset(self):
        self.pos = pygame.Vector2(FIELD_WIDTH // 2, FIELD_HEIGHT // 2)
        self.vel = pygame.Vector2(0, 0)