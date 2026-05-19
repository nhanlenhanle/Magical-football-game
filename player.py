import pygame
from config import *
from team_bot import NormalBot


class Player:
    """Cầu thủ do người chơi hoặc bot điều khiển, gồm di chuyển, va chạm, AI và kỹ năng."""

    def __init__(self, x, y, color,control):
        """Tạo cầu thủ tại vị trí spawn với màu và bộ phím điều khiển."""
        self.kick_timer = 0
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.spawn_x = x
        self.color = color
        self.controls = control
        self.kick_force = KICK_FORCE
        self.kicked = False

        self.ball_ok=True
        self.acceleration = PLAYER_ACCELERATION
        self.damping = PLAYER_DAMPING
        self.max_speed = PLAYER_MAX_SPEED
        self.can_kick = True
        self.just_kicked = False
        self.last_kick_direction = pygame.Vector2(0, 0)
        #------------------------- CHARACTER SELECTION ------------------------
        self.mass = PLAYER_MASS
        self.character = None
        self.skill_active = False
        self.skill_timer = 0
        self.skill_cooldown = 0

        
        self.time_rewind = False
        self.rewind_timer = 0
        #------------------------- BOT ------------------------
        self.is_bot = False
        self.bot_ai = None
        self._reset_debug_info()
        self.cache_target_clear=pygame.Vector2(0,0)

        # Upgrade bonuses (set by profile.apply_to_player)
        self.kick_power_bonus = 0.0
        self.cooldown_reduction_bonus = 0.0
        self.skill_duration_bonus = 0.0
        self.skill_effectiveness_bonus = 0.0
        
    def _reset_debug_info(self):
        """Đặt lại thông tin debug từng frame dùng cho debug overlay."""
        self.debug_info = {
            "state": "IDLE",
            "target": None,
            "intercept": None,
            "shot_direction": pygame.Vector2(0, 0),
            "should_kick": False,
            "is_pressed": False,
            "time_to_ball": 0.0,
            "enemy_time_to_ball": 0.0,
            "ball_distance": 0.0,
            "path_clear": None,
        }

    def bot_update(self, opponent, ball, dt):
        """Delegate bot control to the configured bot AI."""
        if self.bot_ai is not None:
            return self.bot_ai.bot_update(opponent, ball, dt)
        return NormalBot(self).bot_update(opponent, ball, dt)

    def handle_input(self, keys, dt):
        """Áp dụng input bàn phím vào vận tốc của cầu thủ."""
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
        """Cập nhật vật lý cầu thủ, bộ đếm thời gian, kỹ năng và debug."""
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
                    other.vel = pygame.Vector2(0, 0)  
                if self.character == "Chigiri":
                    self.max_speed = PLAYER_MAX_SPEED
                    self.damping = PLAYER_DAMPING
                    self.acceleration = PLAYER_ACCELERATION
                if self.character == "Bachira":
                    self.ball_ok=True

            else:
                if self.character == "Isagi":
                    other.vel = pygame.Vector2(0,0)
                if self.character == "Chigiri":
                    self.vel *= 1.1 
                if self.character == "Nagi":
                    diff = ball.pos - self.pos
                    if diff.length() < 200:
                        direction = diff.normalize()
                        ball.vel -= direction * 200 * dt
        if self.skill_cooldown > 0:
            self.skill_cooldown -= dt

        self.debug_info["ball_distance"] = (ball.pos - self.pos).length()
        if not self.is_bot:
            preview_direction = pygame.Vector2(0, 0)
            diff = ball.pos - self.pos
            if diff.length_squared() > 1e-6:
                preview_direction = diff.normalize()

            self.debug_info["state"] = "MANUAL"
            self.debug_info["target"] = None
            self.debug_info["intercept"] = ball.pos.copy()
            self.debug_info["shot_direction"] = preview_direction
            self.debug_info["should_kick"] = self.can_kick and self.kick_timer <= 0 and self.debug_info["ball_distance"] < PLAYER_RADIUS + BALL_RADIUS + KICK_RANGE
            self.debug_info["is_pressed"] = False
            self.debug_info["time_to_ball"] = NormalBot.estimate_time(self, ball.pos)
            self.debug_info["enemy_time_to_ball"] = NormalBot.estimate_time(other, ball.pos)
            self.debug_info["path_clear"] = None
    #------------------------ COLLISIONS ------------------------
    # Xử lý va chạm giữa hai player
    def handle_player_collision(self, other):
        """Xử lý va chạm vật lý giữa cầu thủ này và cầu thủ khác."""
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
        """Giữ cầu thủ trong vùng chơi và trả về phần hiệu chỉnh vị trí."""
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
        """Xử lý va chạm giữa cầu thủ này và bóng."""
        diff = ball.pos - self.pos
        distance = diff.length()
        min_dist = PLAYER_RADIUS + BALL_RADIUS

        if distance < min_dist and distance != 0:
            self.kicked=False
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
        """Sút bóng nếu bóng trong tầm và cầu thủ được phép sút."""
        if self.can_kick == False:
            return
        if self.kick_timer > 0:
            return

        diff = ball.pos - self.pos
        distance = diff.length()
        min_dist = PLAYER_RADIUS + BALL_RADIUS + KICK_RANGE

        if distance < min_dist and distance != 0:

            direction = diff.normalize()
            force = self.kick_force * (1 + self.kick_power_bonus)
            ball.vel += direction * force

            self.kicked=True
            self.kick_timer = KICK_COOLDOWN
            self.just_kicked = True
            self.last_kick_direction = direction.copy()
            return True
    #------------------------ SKILL ------------------------
    def activate_skill(self,other):
        """Kích hoạt kỹ năng nhân vật nếu kỹ năng không trong thời gian hồi chiêu."""
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
            other.can_kick = False  # đối thủ không thể thay bóng trong thời gian này
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
        if self.character == "Itachi":
            self.skill_active = True
            self.skill_timer = 3.0
            self.skill_cooldown = 15.0
            self.time_rewind = True
            self.rewind_timer = 3.0
    def information(self, character,color):
        """Gán nhân vật đã chọn và màu hiển thị cho cầu thủ."""
        self.character = character
        self.color = color
    def draw(self, screen):
        """Vẽ cầu thủ dưới dạng hình tròn trong tọa độ sân."""
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.pos.x + OFFSET_X), int(self.pos.y + OFFSET_Y)),
            PLAYER_RADIUS
        )
    def reset(self,x,y,color,control):
        """Đưa cầu thủ về spawn và xóa trạng thái di chuyển, sút, kỹ năng."""
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.spawn_x = x
        self.kick_timer = 0
        self.color = color
        self.controls = control
        self.just_kicked = False
        self.last_kick_direction = pygame.Vector2(0, 0)
        self.ball_ok = True
        self.can_kick = True
        self.kicked = False
        self.mass = PLAYER_MASS
        self.acceleration = PLAYER_ACCELERATION
        self.damping = PLAYER_DAMPING
        self.max_speed = PLAYER_MAX_SPEED
        self.skill_active = False
        self.skill_timer = 0
        self.skill_cooldown = 0
        self.time_rewind = False
        self.rewind_timer = 0
        self._reset_debug_info()
