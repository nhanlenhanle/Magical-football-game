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
    def bot_update(self, opponent, ball, dt):
        # =========================
        # 0. PREDICTION (Tính đường cắt bóng)
        # =========================
        my_goal = pygame.Vector2(FIELD_WIDTH, FIELD_HEIGHT / 2)
        enemy_goal = pygame.Vector2(0, FIELD_HEIGHT / 2)

        # Tính thời gian dự kiến để Bot chạy tới bóng
        # Dùng vận tốc bóng (ball.vel) để tính xem 0.3s -> 0.4s nữa bóng sẽ lăn tới đâu
        time_to_reach = min(0.4, (ball.pos - self.pos).length() / (self.max_speed + 1))
        pred_ball_pos = ball.pos + ball.vel * time_to_reach
        
        # Đảm bảo điểm dự đoán không bị lọt ra ngoài sân
        pred_ball_pos.x = max(20, min(FIELD_WIDTH - 20, pred_ball_pos.x))
        pred_ball_pos.y = max(20, min(FIELD_HEIGHT - 20, pred_ball_pos.y))

        # Dùng vị trí DỰ ĐOÁN để đánh giá khoảng cách thay vì vị trí bóng hiện tại
        dist_to_ball = (pred_ball_pos - self.pos).length()
        opp_dist_to_ball = (pred_ball_pos - opponent.pos).length()
        
        # Các cờ trạng thái vật lý vẫn dùng vị trí gốc
        dist_actual = (ball.pos - self.pos).length()
        is_possessing = dist_actual < PLAYER_RADIUS + BALL_RADIUS + 8
        can_kick = dist_actual < PLAYER_RADIUS + BALL_RADIUS + KICK_RANGE
        safe_margin = PLAYER_RADIUS + BALL_RADIUS + 15

        # =========================
        # 1. SHOT OPTIONS (Tối ưu tìm góc sút hiểm nhất)
        # =========================
        opp_goal_top = pygame.Vector2(0, GOAL_TOP + BALL_RADIUS + 5)
        opp_goal_bottom = pygame.Vector2(0, GOAL_BOTTOM - BALL_RADIUS - 5)
        virtual_top = pygame.Vector2(0, -FIELD_HEIGHT / 2)
        virtual_bottom = pygame.Vector2(0, FIELD_HEIGHT + FIELD_HEIGHT / 2)

        shot_options = [opp_goal_top, opp_goal_bottom, virtual_top, virtual_bottom]
        
        best_shot = enemy_goal
        max_clearance = -1 # Tìm góc thoáng nhất
        
        for shot in shot_options:
            A = ball.pos
            B = shot
            P = opponent.pos
            AB = B - A
            AP = P - A

            if AB.length_squared() > 0:
                t = AP.dot(AB) / AB.length_squared()
                t = max(0.0, min(1.0, t))
                closest = A + AB * t
                dist_to_line = (P - closest).length()

                # So sánh: Thay vì lấy góc đầu tiên, Bot sẽ duyệt hết và chọn quỹ đạo SÚT XA ĐỊCH NHẤT
                if dist_to_line > max_clearance:
                    max_clearance = dist_to_line
                    best_shot = shot

        # =========================
        # 2. STATE
        # =========================
        if dist_to_ball < opp_dist_to_ball:
            state = "ATTACK"
        else:
            state = "DEFEND"

        current_accel = self.acceleration

        # =========================
        # 3. DEFENSE (Cắt bóng + Phá ra biên)
        # =========================
        if state == "DEFEND":
            if opp_dist_to_ball > 150:
                # Địch ở xa: Đón lõng đường chuyền/đường lăn của bóng
                target = my_goal + (pred_ball_pos - my_goal) * 0.4
            else:
                # ÁP SÁT CẮT BÓNG VÀ PHÁ RA BIÊN
                # Mục tiêu: Đẩy bóng về 2 góc sân của địch (Tránh xa gôn nhà)
                if ball.pos.y > FIELD_HEIGHT / 2:
                    clearance_target = pygame.Vector2(0, 0) # Góc trên
                else:
                    clearance_target = pygame.Vector2(0, FIELD_HEIGHT) # Góc dưới
                    
                # Tính hướng để Bot đứng sao cho khi húc/sút, bóng bay về clearance_target
                clear_dir = (pred_ball_pos - clearance_target).normalize()
                
                # Chạy thẳng tới ĐIỂM CẮT BÓNG (future_pos) thay vì đuổi theo bóng
                target = pred_ball_pos + clear_dir * 18
                current_accel = self.acceleration * 1.3 # Buff 30% tốc độ để nhoài người cắt bóng

            if can_kick:
                self.kick(ball)

        # =========================
        # 4. ATTACK (Đè + Giữ + Ép sân)
        # =========================
        else:
            # Lấy vị trí bóng tương lai để làm đà sút
            shot_dir = (best_shot - pred_ball_pos)
            if shot_dir.length() > 0:
                target = pred_ball_pos - shot_dir.normalize() * 15
            else:
                target = pred_ball_pos

            if is_possessing:
                block_dir = ball.pos - opponent.pos
                if block_dir.length() > 0:
                    block_dir = block_dir.normalize()
                    target = ball.pos - block_dir * 20

                current_accel *= 0.15
                if self.vel.length() > self.max_speed * 0.4:
                    self.vel *= 0.8

                push_dir = enemy_goal - ball.pos
                if push_dir.length() > 0:
                    ball.vel += push_dir.normalize() * 50 # Ép bóng trôi nhanh hơn

        # =========================
        # 5. MOVE
        # =========================
        direction = target - self.pos
        if direction.length() > 2:
            direction = direction.normalize()
            self.vel += direction * current_accel * dt

        # =========================
        # 6. KICK LOGIC (Siết góc sút)
        # =========================
        if can_kick:
            if opp_dist_to_ball < safe_margin:
                self.kick(ball)
                return

            bot_to_ball = (ball.pos - self.pos)
            ball_to_goal = (best_shot - ball.pos)

            if bot_to_ball.length() > 0 and ball_to_goal.length() > 0:
                bot_to_ball = bot_to_ball.normalize()
                ball_to_goal = ball_to_goal.normalize()

                # Siết góc sút (Từ 0.85 lên 0.92): Đòi hỏi Bot ngắm cực kỳ chuẩn và thẳng form mới vung chân
                if bot_to_ball.dot(ball_to_goal) > 0.92:
                    self.kick(ball)

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
            self.skill_timer = 2.0
            self.skill_cooldown = 15.0
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
