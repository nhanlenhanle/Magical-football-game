import pygame
from config import *


class Player:
    def __init__(self, x, y, color,control):
        self.kick_timer = 0
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.color = color
        self.controls = control

        self.ball_ok=True
        self.acceleration = PLAYER_ACCELERATION
        self.damping = PLAYER_DAMPING
        self.max_speed = PLAYER_MAX_SPEED
        self.can_kick = True
        #------------------------- CHARACTER SELECTION ------------------------
        self.mass = PLAYER_MASS
        self.character = None
        self.skill_active = False
        self.skill_timer = 0
        self.skill_cooldown = 0
        #------------------------- BOT ------------------------
        self.is_bot = False
    @staticmethod
    def simulate_ball_step(pos, vel, dt):
        vel *= BALL_DAMPING
        pos += vel * dt

        # ================= WALL =================
        # TOP
        if pos.y - BALL_RADIUS < 0:
            pos.y = BALL_RADIUS
            vel.y *= -RESTITUTION

        # BOTTOM
        elif pos.y + BALL_RADIUS > FIELD_HEIGHT:
            pos.y = FIELD_HEIGHT - BALL_RADIUS
            vel.y *= -RESTITUTION

        # LEFT
        if pos.x - BALL_RADIUS < 0:
            if not (GOAL_TOP < pos.y < GOAL_BOTTOM):
                pos.x = BALL_RADIUS
                vel.x *= -RESTITUTION

        # RIGHT
        elif pos.x + BALL_RADIUS > FIELD_WIDTH:
            if not (GOAL_TOP < pos.y < GOAL_BOTTOM):
                pos.x = FIELD_WIDTH - BALL_RADIUS
                vel.x *= -RESTITUTION

        # ================= POSTS =================
        posts = [
            pygame.Vector2(0, GOAL_TOP),
            pygame.Vector2(0, GOAL_BOTTOM),
            pygame.Vector2(FIELD_WIDTH, GOAL_TOP),
            pygame.Vector2(FIELD_WIDTH, GOAL_BOTTOM),
        ]

        for post in posts:
            diff = pos - post
            dist = diff.length()
            min_dist = BALL_RADIUS + POST_RADIUS

            if dist < min_dist and dist != 0:
                normal = diff.normalize()

                # đẩy ra ngoài
                pos = post + normal * min_dist

                # phản xạ chuẩn
                vel = vel - 2 * vel.dot(normal) * normal
                vel *= 0.9

        return pos, vel
    @staticmethod
    def estimate_time(player, target):
        diff = target - player.pos
        dist = diff.length()

        if dist == 0:
            return 0

        dir = diff.normalize()
        v = player.vel
        a = PLAYER_ACCELERATION
        v_max = PLAYER_MAX_SPEED

        if v.length() > 0:
            v_parallel = v.dot(dir)
            v_perp = (v - v_parallel * dir).length()
        else:
            v_parallel = 0
            v_perp = 0

        # ===== xử lý (đổi hướng) =====
        t_perp = v_perp / a

        if v_parallel < 0:
            t_stop = -v_parallel / a
            s_stop = v_parallel * t_stop + 0.5 * a * t_stop**2
        else:
            t_stop = 0
            s_stop = 0

        dist = max(dist - s_stop, 0)
        v0 = max(v_parallel, 0)

        # ===== tăng tốc tới max =====
        t_acc = max((v_max - v0) / a, 0)
        s_acc = v0 * t_acc + 0.5 * a * t_acc**2

        if s_acc >= dist:
            t_move = (-v0 + (v0**2 + 2*a*dist)**0.5) / a
        else:
            s_remain = dist - s_acc
            t_const = s_remain / v_max
            t_move = t_acc + t_const

        return t_perp + t_stop + t_move
    def find_intercept(player, ball, dt):
        max_t = 2.0

        pos = ball.pos.copy()
        vel = ball.vel.copy()

        time = 0

        best_pos = pos.copy()
        best_diff = float('inf')

        while time < max_t:
            pos, vel = Player.simulate_ball_step(pos, vel, dt)

            t_needed = Player.estimate_time(player, pos)

            if t_needed <= time:
                return pos

            diff = abs(t_needed - time)
            if diff < best_diff:
                best_diff = diff
                best_pos = pos.copy()

            time += dt

        return best_pos
    def bot_update(self, opponent, ball, dt):
        target_me = Player.find_intercept(self, ball, dt)
        target_enemy = Player.find_intercept(opponent, ball, dt)

        t_me = Player.estimate_time(self, target_me)
        t_enemy = Player.estimate_time(opponent, target_enemy)
        target_pos = self.pos
        if t_me <= t_enemy:
            state = "ATTACK"
            target_pos = target_me
            direction = target_pos - self.pos
            self.vel += direction.normalize() * self.acceleration * dt
        elif t_enemy  < t_me:
            state = "DEFEND"
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
            self.vel += direction * self.acceleration * dt

    def update(self, other, dt, ball):
        self.vel *= self.damping

        # Giới hạn tốc độ tối đa
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)

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
                if self.character == "Isagi":
                    other.can_kick = True
                    other.vel = pygame.Vector2(0, 0)  # trả lại tốc độ cho đối thủ sau khi skill kết thúc
                if self.character == "Chigiri":
                    self.max_speed = PLAYER_MAX_SPEED
                    self.damping = PLAYER_DAMPING
                    self.acceleration = PLAYER_ACCELERATION
                if self.character == "Bachira":
                    self.ball_ok=True

            else:
                if self.character == "Isagi":
                    other.vel *= 0.005  # tiếp tục duy trì hiệu ứng giảm tốc độ đối thủ trong thời gian skill còn hoạt động
                if self.character == "Chigiri":
                    self.vel *= 1.1 # tiếp tục duy trì hiệu ứng tăng tốc độ của bản thân trong thời gian skill còn hoạt động
                if self.character == "Nagi":
                    diff = ball.pos - self.pos
                    if diff.length() < 200:
                        direction = diff.normalize()
                        ball.vel -= direction * 200 * dt
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

            # Tách 2 player ra theo khối lượng
            total_mass = self.mass + other.mass
            self.pos -= normal * (overlap * (other.mass / total_mass))
            other.pos += normal * (overlap * (self.mass / total_mass))

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

            # Xử lý vận tốc 
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
        if self.can_kick == False:
            return
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
    def activate_skill(self,other):
        if self.skill_cooldown > 0:
            return
        if self.character == "Kunigami":
            self.skill_active = True
            self.skill_timer = 10.0
            self.skill_cooldown = 5.0
            self.mass = 1000  # cực nặng, khó bị đẩy văng ra khỏi sân
        if self.character == "Isagi":
            self.skill_active = True
            self.skill_timer = 5.0
            self.skill_cooldown = 10.0
            other.vel *= 0.005  # giảm tốc độ đối thủ xuống cực thấp
            other.can_kick = False  # đối thủ không thể đá bóng trong thời gian này
        if self.character == "Chigiri":
            self.skill_active = True
            self.skill_timer = 10.0
            self.skill_cooldown = 5.0
            self.max_speed += 50 
            self.vel *= 1.5
            self.damping = 0.9
            self.acceleration += 200
        if self.character == "Bachira":
            self.skill_active = True
            self.skill_timer = 5.0
            self.skill_cooldown = 10.0
            self.ball_ok=False
        if self.character == "Nagi":
            self.skill_active = True
            self.skill_timer = 5.0
            self.skill_cooldown = 10.0
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