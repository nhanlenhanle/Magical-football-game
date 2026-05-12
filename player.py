import pygame
from config import *


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

    @staticmethod
    def simulate_ball_step(pos, vel, dt):
        """Mô phỏng một bước vật lý bóng đơn giản để AI dự đoán."""
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
                pos = post + normal * min_dist

                vel = vel - 2 * vel.dot(normal) * normal
                vel *= 0.9

        return pos, vel
    @staticmethod
    def estimate_time(player, target):
        """Ước lượng thời gian cầu thủ cần để đến một điểm mục tiêu."""
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
    @staticmethod
    def find_intercept_info(player, ball, dt):
        """Dự đoán vị trí bóng trong tương lai mà cầu thủ có thể chạm tới tốt nhất."""
        max_t = 2.0
        sim_dt = max(1 / 180, min(dt, 1 / 60))

        pos = ball.pos.copy()
        vel = ball.vel.copy()
        time = 0.0

        best_pos = pos.copy()
        best_vel = vel.copy()
        best_time = 0.0
        best_diff = float('inf')

        while time < max_t:
            pos, vel = Player.simulate_ball_step(pos, vel, sim_dt)
            time += sim_dt

            t_needed = Player.estimate_time(player, pos)

            if t_needed <= time:
                return {"pos": pos.copy(), "vel": vel.copy(), "time": time}

            diff = abs(t_needed - time)
            if diff < best_diff:
                best_diff = diff
                best_pos = pos.copy()
                best_vel = vel.copy()
                best_time = time

        return {"pos": best_pos, "vel": best_vel, "time": best_time}
    #Hàm đưa ra vị trí với thời gian ngắn nhất mà bot có thể tới
    @staticmethod
    def find_intercept(player, ball, dt):
        """Trả về riêng vị trí dự đoán để cầu thủ chặn bóng."""
        return Player.find_intercept_info(player, ball, dt)["pos"]
    #Hàm phòng thủ
    #Phòng thủ bằng cách chạy theo tia từ player.pos đến điểm giữa của gôn bot
    def jockey_position(self, ball, opponent):
        """Chọn vị trí phòng thủ giữa đối thủ và gôn của cầu thủ này."""
        my_goal = pygame.Vector2(FIELD_WIDTH, FIELD_HEIGHT // 2)
        
        goal_to_ball_vec = opponent.pos - my_goal
        dist_to_goal = goal_to_ball_vec.length()
        
        if dist_to_goal == 0:
            return my_goal
            
        dir_to_ball = goal_to_ball_vec.normalize()
        ball_control_dist = 0 # (ball.pos - opponent.pos).length()

        if ball_control_dist > PLAYER_RADIUS + BALL_RADIUS + 30 or dist_to_goal < 180:
            return ball.pos  # Lao thẳng vào bóng

        dynamic_buffer = min(100, dist_to_goal * 0.3) 
        
        target = opponent.pos - dir_to_ball * dynamic_buffer

        return target
    # @staticmethod
    # def ball_fly_goal(ball, dt, goal_x=FIELD_WIDTH):
    #     max_t = 3.0
    #     sim_dt = max(1 / 180, min(dt, 1 / 60))
    #     pos = ball.pos.copy()
    #     vel = ball.vel.copy()
    #     time = 0.0
    #     last_pos = pos.copy()
    #     last_vel = vel.copy()

    #     while time < max_t:
    #         last_pos = pos.copy()
    #         last_vel = vel.copy()
    #         pos, vel = Player.simulate_ball_step(pos, vel, sim_dt)
    #         time += sim_dt

    #         if goal_x >= FIELD_WIDTH:
    #             if GOAL_TOP < pos.y < GOAL_BOTTOM and pos.x - BALL_RADIUS / 3 > FIELD_WIDTH:
    #                 return {
    #                     "time": time,
    #                     "pos": pos.copy(),
    #                     "vel": vel.copy(),
    #                     "last_pos": last_pos,
    #                     "last_vel": last_vel,
    #                 }
    #         else:
    #             if GOAL_TOP < pos.y < GOAL_BOTTOM and pos.x + BALL_RADIUS / 3 < 0:
    #                 return {
    #                     "time": time,
    #                     "pos": pos.copy(),
    #                     "vel": vel.copy(),
    #                     "last_pos": last_pos,
    #                     "last_vel": last_vel,
    #                 }

    #         if vel.length_squared() < 25:
    #             break

    #     return None

    # @staticmethod
    # def should_bank_save(player, intercept_pos, intercept_vel, my_goal):
    #     goal_vec = my_goal - intercept_pos
    #     if goal_vec.length_squared() <= 1e-6:
    #         return False

    #     goal_dir = goal_vec.normalize()
    #     bot_run_vec = intercept_pos - player.pos

    #     bot_dot = 0.0
    #     if bot_run_vec.length_squared() > 1e-6:
    #         bot_dot = bot_run_vec.normalize().dot(goal_dir)

    #     ball_dot = 0.0
    #     if intercept_vel.length_squared() > 1e-6:
    #         ball_dot = intercept_vel.normalize().dot(goal_dir)

    #     return bot_dot > 0.15 and ball_dot > 0.15

    # @staticmethod
    # def goal_bank_target(intercept_pos):
    #     inset_x = FIELD_WIDTH
    #     inset_y = 10
    #     top_target = pygame.Vector2(inset_x, GOAL_TOP - inset_y)
    #     bottom_target = pygame.Vector2(inset_x, GOAL_BOTTOM + inset_y)

    #     if abs(intercept_pos.y - top_target.y) <= abs(intercept_pos.y - bottom_target.y):
    #         return top_target
    #     return bottom_target
    def find_best_clear(self,ball,bot_intercept):
        """Chọn mục tiêu phá bóng an toàn và dễ tiếp cận hơn cho bot."""
        dir = self.pos - ball.pos
        target_top = pygame.Vector2(FIELD_WIDTH-5,5)
        target_bottom = pygame.Vector2(FIELD_WIDTH-5,FIELD_HEIGHT-5)
        self.cache_target_clear=pygame.Vector2(0,0)
        B = (target_top - bot_intercept)
        C = (target_bottom - bot_intercept)
        if (B.length()<=C.length()):
            return target_top
        return target_bottom
    @staticmethod
    def is_player_ball_line_on_goal(self, ball):
        """Kiểm tra cầu thủ có thể sút bóng về phía gôn trái hay không."""
        A = self.pos
        dir = ball.pos - self.pos
        if dir.length_squared() < 1e-6:
            return False
        shot_dir = (ball.pos - self.pos).normalize()
        final_vel = ball.vel + shot_dir * KICK_FORCE
        goal_x = 0
        if final_vel.x >= 0:
            return False
        if abs(final_vel.x) < 1e-6:
            return False
        t = (goal_x - A.x) / final_vel.x
        if t <= 0:
            return False
        y_hit = A.y + final_vel.y * t
        Radius=POST_RADIUS + BALL_RADIUS + 1
        if GOAL_TOP + Radius <= y_hit <= GOAL_BOTTOM - Radius:
            return True
    def is_not_player_ball_line_on_goal(self, ball):
        """Kiểm tra cầu thủ có thể phá bóng khỏi vùng gôn phải hay không."""
        A = self.pos
        dir = ball.pos - self.pos
        if dir.length_squared() < 1e-6:
            return False
        shot_dir = (ball.pos - self.pos).normalize()
        final_vel = ball.vel + shot_dir * KICK_FORCE
        goal_x = FIELD_WIDTH
        if final_vel.x <= 0:
            return False
        if abs(final_vel.x) < 1e-6:
            return False
        t = (goal_x - A.x) / final_vel.x
        if t <= 0:
            return False
        y_hit = A.y + final_vel.y * t
        Radius=POST_RADIUS + BALL_RADIUS + 1
        if GOAL_TOP - Radius > y_hit or  y_hit > GOAL_BOTTOM + Radius:
            return True
    def find_best_goal_target(ball_pos, goal_center, goal_top, goal_bottom):
        """Chọn điểm hợp lệ tốt nhất trong miệng gôn để sút."""
        
        Radius=POST_RADIUS + BALL_RADIUS + 0.01
        if GOAL_TOP + Radius <= goal_center.y <= GOAL_BOTTOM - Radius:
            return goal_center

        if ball_pos.y > goal_center.y:
            return goal_top
        else:
            return goal_bottom
    @staticmethod
    def orbit_attack_target(player_pos, ball_pos, base_target):
        """Dịch mục tiêu tiếp cận vòng quanh bóng khi đường vào trực tiếp không tốt."""
        ball_to_target = base_target - ball_pos
        ball_to_player = player_pos - ball_pos

        if ball_to_target.length_squared() <= 1e-6 or ball_to_player.length_squared() <= 1e-6:
            return base_target

        side_alignment = ball_to_player.normalize().dot(ball_to_target.normalize())
        if side_alignment >= -0.15:
            return base_target

        perpendicular = pygame.Vector2(-ball_to_target.y, ball_to_target.x)
        if perpendicular.length_squared() <= 1e-6:
            return base_target

        perpendicular = perpendicular.normalize()
        orbit_radius = PLAYER_RADIUS + BALL_RADIUS + 18
        candidate_a = base_target + perpendicular * orbit_radius
        candidate_b = base_target - perpendicular * orbit_radius

        if (candidate_a - player_pos).length_squared() <= (candidate_b - player_pos).length_squared():
            return candidate_a
        return candidate_b
    def NEED_SPAM(self, opponent, ball):
        """Trả về True nếu bot nên áp sát và spam tranh bóng ở cự ly gần."""
        if (ball.pos-self.pos).normalize().dot((ball.pos-opponent.pos).normalize())<0 and (ball.pos-self.pos).normalize().x<0:
           return((self.pos-opponent.pos).length() - (PLAYER_RADIUS*2 + BALL_RADIUS + 150) <= 0)
        return False
    def bot_update(self, opponent, ball, dt):
        """Cập nhật di chuyển, chọn mục tiêu và quyết định sút của bot trong một frame."""

        enemy_goal_center = pygame.Vector2(0, FIELD_HEIGHT // 2)
        my_goal = pygame.Vector2(FIELD_WIDTH, FIELD_HEIGHT // 2)

        bot_intercept_info = Player.find_intercept_info(self, ball, dt)
        bot_intercept = bot_intercept_info["pos"]
        t_bot = Player.estimate_time(self, bot_intercept)

        enemy_intercept = Player.find_intercept(opponent, ball, dt)
        t_enemy = Player.estimate_time(opponent, enemy_intercept)

        target = self.pos
        state = "IDLE"
        should_kick = False
        is_pressed = False
        planned_shot_direction = pygame.Vector2(0, 0)
        path_clear = None
        diff = ball.pos - self.pos

        if (ball.pos-self.pos).normalize().dot((ball.pos-opponent.pos).normalize())<0 and (ball.pos-self.pos).normalize().x<0:
            ok = 0.3
        else:
            ok = -0.15
        check_ok = (self.pos-ball.pos).normalize().dot((self.pos-opponent.pos).normalize())<0 and (ball.pos-self.pos).normalize().x>0
        check_ok = check_ok and (t_bot > t_enemy + 0.15)
        if t_bot > t_enemy + ok and (not check_ok):
            state = "DEFEND"
        elif t_bot - t_enemy < 0.15 and t_bot - t_enemy > -1 and diff.normalize().x >=0:
            state = "CLEAR"
        elif self.NEED_SPAM(opponent,ball):
            state = "SPAM"
        elif diff.length() < PLAYER_RADIUS + BALL_RADIUS + KICK_RANGE:
            state = "ATTACK"
        else:
            state = "ATTACK"
        if state == "CLEAR":
            vec_excepted = self.find_best_clear(ball,bot_intercept) - ball.pos
            vec = vec_excepted - ball.vel
            if vec.length_squared() > 1e-6:
                planned_shot_direction = vec.normalize()
                bot_to_ball = ball.pos - self.pos
                target = ball.pos - planned_shot_direction * (PLAYER_RADIUS + BALL_RADIUS+0.1)
                if bot_to_ball.length_squared() > 1e-6:
                    behind_alignment = bot_to_ball.normalize().dot(planned_shot_direction)
                else:
                    behind_alignment = 1.0
                if behind_alignment > 0.98 or Player.is_not_player_ball_line_on_goal(self,ball):
                    should_kick = True
                else:
                    should_kick = False
                    target = Player.orbit_attack_target(self.pos, ball.pos, target)
            else:
                target = ball.pos
                should_kick = False
        elif state == "DEFEND":
            self.cache_target_clear=pygame.Vector2(0,0)
            target = Player.jockey_position(self, ball, opponent)
        elif state == "ATTACK":
            self.cache_target_clear=pygame.Vector2(0,0)
            goal_center = enemy_goal_center
            goal_top = pygame.Vector2(0, GOAL_TOP + 0.1)
            goal_bottom = pygame.Vector2(0, GOAL_BOTTOM - 0.1)
            
            best_goal_target = Player.find_best_goal_target(ball.pos, goal_center, goal_top, goal_bottom)
            attack_vec_excepted = best_goal_target - ball.pos
            attack_vec = attack_vec_excepted - ball.vel
            check_it = self.is_not_player_ball_line_on_goal(ball) and ball.pos.x>=FIELD_WIDTH-200
            if attack_vec.length_squared() > 1e-6:
                planned_shot_direction = attack_vec.normalize()
                target = ball.pos - planned_shot_direction * (PLAYER_RADIUS + BALL_RADIUS+0.1)
                bot_to_ball = ball.pos - self.pos
                if bot_to_ball.length_squared() > 1e-12:
                    behind_alignment = bot_to_ball.normalize().dot(planned_shot_direction)
                else:
                    behind_alignment = 1.0
                if behind_alignment > 0.99 or Player.is_player_ball_line_on_goal(self,ball) or check_it:
                    should_kick = True
                else:
                    should_kick = False
                    target = Player.orbit_attack_target(self.pos, ball.pos, target)
            else:
                target = ball.pos
                should_kick = False
        elif state == "SPAM":
            should_kick = True
            target = ball.pos
        direction = target - self.pos
        hack_speed = 1.05
        if direction.length() > 0.5:
            direction = direction.normalize()
            self.vel += direction * self.acceleration * dt * hack_speed

        kicked = False
        if should_kick:
            if diff.length() < PLAYER_RADIUS + BALL_RADIUS + KICK_RANGE:
                kicked = self.kick(ball)
        self.debug_info["state"] = state
        self.debug_info["target"] = target.copy()
        self.debug_info["intercept"] = bot_intercept.copy()
        self.debug_info["shot_direction"] = planned_shot_direction.copy()
        self.debug_info["should_kick"] = should_kick
        self.debug_info["is_pressed"] = is_pressed
        self.debug_info["time_to_ball"] = t_bot
        self.debug_info["enemy_time_to_ball"] = t_enemy
        self.debug_info["ball_distance"] = (ball.pos - self.pos).length()
        self.debug_info["path_clear"] = path_clear
        return kicked

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
            self.debug_info["time_to_ball"] = Player.estimate_time(self, ball.pos)
            self.debug_info["enemy_time_to_ball"] = Player.estimate_time(other, ball.pos)
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
            force = KICK_FORCE * (1 + self.kick_power_bonus)
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
