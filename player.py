import pygame
from config import *


class Player:
    def __init__(self, x, y, color,control):
        self.kick_timer = 0
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.color = color
        self.controls = control
        #------------------------- CHARACTER SELECTION ------------------------
        self.mass = PLAYER_MASS
        self.character = None
        self.skill_active = False
        self.skill_timer = 0
        self.skill_cooldown = 0

    def handle_input(self, keys, dt):
        direction = pygame.Vector2(0, 0)

        if keys[self.controls["up"]]:
            direction.y -= 1
        if keys[self.controls["down"]]:
            direction.y += 1
        if keys[self.controls["left"]]:
            direction.x -= 1
        if keys[self.controls["right"]]:
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

        #------------------------ SKILL UPDATE ------------------------
        if self.skill_active:
            self.skill_timer -= dt
            if self.skill_timer <= 0:
                self.skill_active = False
                if self.character == "Kunigami":
                    self.mass = PLAYER_MASS
        if self.skill_cooldown > 0:
            self.skill_cooldown -= dt
    #------------------------ COLLISIONS ------------------------
    # Xử lý va chạm giữa hai player
    def handle_player_collision(self, other):
        diff = other.pos - self.pos
        distance = diff.length()
        min_dist = PLAYER_RADIUS * 2

        if distance < min_dist and distance != 0:
            normal = diff.normalize()
            overlap = min_dist - distance

            # Bước 1: Tách 2 player ra theo khối lượng
            total_mass = self.mass + other.mass
            self.pos -= normal * (overlap * (other.mass / total_mass))
            other.pos += normal * (overlap * (self.mass / total_mass))

            # --- DỒN PHẦN DƯ ---
            # Kéo 2 đứa về lại sân (nếu bị đẩy văng ra), lấy phần văng ra đó lưu lại
            corr_self = self.handle_wall_collision()
            corr_other = other.handle_wall_collision()

            # Bắt thằng kia phải gánh phần bị dôi ra của mình
            self.pos += corr_other
            other.pos += corr_self

            # ép tường thêm lần nữa
            self.handle_wall_collision()
            other.handle_wall_collision()
            # -------------------------

            # Bước 2: Xử lý vận tốc (giữ nguyên như cũ)
            relative_velocity = self.vel - other.vel
            vel_along_normal = relative_velocity.dot(normal)

            if vel_along_normal > 0:
                return

            impulse = -(1 + RESTITUTION) * vel_along_normal
            impulse /= (1 / self.mass + 1 / other.mass)

            impulse_vector = impulse * normal

            self.vel += impulse_vector / self.mass
            other.vel -= impulse_vector / other.mass
    # Xử lý va chạm với tường
    def handle_wall_collision(self):
        # Tạo vector lưu phần khoảng cách bị dôi ra
        correction = pygame.Vector2(0, 0)

        min_x = -GOAL_DEPTH
        max_x = FIELD_WIDTH + GOAL_DEPTH
        min_y = -TOP_BOTTOM_MARGIN
        max_y = FIELD_HEIGHT + TOP_BOTTOM_MARGIN

        # Trục X
        if self.pos.x - PLAYER_RADIUS < min_x:
            correction.x = (min_x + PLAYER_RADIUS) - self.pos.x
            self.pos.x = min_x + PLAYER_RADIUS
            self.vel.x = 0
            
        elif self.pos.x + PLAYER_RADIUS > max_x:
            correction.x = (max_x - PLAYER_RADIUS) - self.pos.x
            self.pos.x = max_x - PLAYER_RADIUS
            self.vel.x = 0

        # Trục Y
        if self.pos.y - PLAYER_RADIUS < min_y:
            correction.y = (min_y + PLAYER_RADIUS) - self.pos.y
            self.pos.y = min_y + PLAYER_RADIUS
            self.vel.y = 0
            
        elif self.pos.y + PLAYER_RADIUS > max_y:
            correction.y = (max_y - PLAYER_RADIUS) - self.pos.y
            self.pos.y = max_y - PLAYER_RADIUS
            self.vel.y = 0

        return correction # Trả về để dùng dồn lực cho thằng kia
    # Xử lý va chạm với bóng
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
    #------------------------ SKILL ------------------------
    def activate_skill(self):
        if self.skill_cooldown > 0:
            return
        if self.character == "Kunigami":
            self.skill_active = True
            self.skill_timer = 5.0
            self.skill_cooldown = 10.0
            self.mass = 1000  # cực nặng, khó bị đẩy văng ra khỏi sân
    def information(self, character,color):
        self.character = character
        self.color = color
    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.pos.x + OFFSET_X), int(self.pos.y + OFFSET_Y)),
            PLAYER_RADIUS
        )
    def reset(self,x,y,color,control):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.kick_timer = 0
        self.color = color
        self.controls = control
