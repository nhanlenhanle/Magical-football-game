import pygame
from config import *

class NormalBot:
    """Bot cơ bản điều khiển cầu thủ đuổi theo bóng và sút về gôn đối phương."""
    def __init__(self, player):
        """Khởi tạo bot với cầu thủ mục tiêu để điều khiển."""
        object.__setattr__(self, "player", player)

    def __getattr__(self, name):
        return getattr(self.player, name)

    def __setattr__(self, name, value):
        if name == "player":
            object.__setattr__(self, name, value)
        else:
            setattr(self.player, name, value)

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
    #         pos, vel = DefBot.simulate_ball_step(pos, vel, sim_dt)
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

        # ===== x? lý (d?i hu?ng) =====
        t_perp = v_perp / a

        if v_parallel < 0:
            t_stop = -v_parallel / a
            s_stop = v_parallel * t_stop + 0.5 * a * t_stop**2
        else:
            t_stop = 0
            s_stop = 0

        dist = max(dist - s_stop, 0)
        v0 = max(v_parallel, 0)

        # ===== tang t?c t?i max =====
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
            pos, vel = AttackBot.simulate_ball_step(pos, vel, sim_dt)
            time += sim_dt

            t_needed = AttackBot.estimate_time(player, pos)

            if t_needed <= time:
                return {"pos": pos.copy(), "vel": vel.copy(), "time": time}

            diff = abs(t_needed - time)
            if diff < best_diff:
                best_diff = diff
                best_pos = pos.copy()
                best_vel = vel.copy()
                best_time = time

        return {"pos": best_pos, "vel": best_vel, "time": best_time}
    #Hàm dua ra v? trí v?i th?i gian ng?n nh?t mà bot có th? t?i
    @staticmethod
    def find_intercept(player, ball, dt):
        """Trả về riêng vị trí dự đoán để cầu thủ chạm bóng."""
        return AttackBot.find_intercept_info(player, ball, dt)["pos"]
    #Hàm phòng th?
    #Phòng th? b?ng cách ch?y theo tia t? player.pos d?n di?m gi?a c?a gôn bot
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
            return ball.pos  # Lao th?ng vào bóng

        dynamic_buffer = min(100, dist_to_goal * 0.3) 
        
        target = opponent.pos - dir_to_ball * dynamic_buffer

        return target
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
        """Chọn điểm hợp lý tốt nhất trong miệng gôn để sút."""
        
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
        orbit_radius = PLAYER_RADIUS + BALL_RADIUS + 5
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

        bot_intercept_info = AttackBot.find_intercept_info(self, ball, dt)
        bot_intercept = bot_intercept_info["pos"]
        t_bot = AttackBot.estimate_time(self, bot_intercept)

        enemy_intercept = AttackBot.find_intercept(opponent, ball, dt)
        t_enemy = AttackBot.estimate_time(opponent, enemy_intercept)

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
                if behind_alignment > 0.98 or AttackBot.is_not_player_ball_line_on_goal(self,ball):
                    should_kick = True
                else:
                    should_kick = False
                    target = AttackBot.orbit_attack_target(self.pos, ball.pos, target)
            else:
                target = ball.pos
                should_kick = False
        elif state == "DEFEND":
            self.cache_target_clear=pygame.Vector2(0,0)
            target = AttackBot.jockey_position(self, ball, opponent)
        elif state == "ATTACK":
            self.cache_target_clear=pygame.Vector2(0,0)
            goal_center = enemy_goal_center
            goal_top = pygame.Vector2(0, GOAL_TOP + 0.1)
            goal_bottom = pygame.Vector2(0, GOAL_BOTTOM - 0.1)
            
            best_goal_target = AttackBot.find_best_goal_target(ball.pos, goal_center, goal_top, goal_bottom)
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
                if behind_alignment > 0.99 or AttackBot.is_player_ball_line_on_goal(self,ball) or check_it:
                    should_kick = True
                else:
                    should_kick = False
                    target = AttackBot.orbit_attack_target(self.pos, ball.pos, target)
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











class AttackBot:
    """Bot tấn công chuyên dụng, dự đoán điểm rơi của bóng để dứt điểm."""
    def __init__(self, player):
        """Khởi tạo bot tấn công với cầu thủ mục tiêu."""
        object.__setattr__(self, "player", player)

    def __getattr__(self, name):
        return getattr(self.player, name)

    def __setattr__(self, name, value):
        if name == "player":
            object.__setattr__(self, name, value)
        else:
            setattr(self.player, name, value)

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

        # ===== x? lý (d?i hu?ng) =====
        t_perp = v_perp / a

        if v_parallel < 0:
            t_stop = -v_parallel / a
            s_stop = v_parallel * t_stop + 0.5 * a * t_stop**2
        else:
            t_stop = 0
            s_stop = 0

        dist = max(dist - s_stop, 0)
        v0 = max(v_parallel, 0)

        # ===== tang t?c t?i max =====
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
            pos, vel = AttackBot.simulate_ball_step(pos, vel, sim_dt)
            time += sim_dt

            t_needed = AttackBot.estimate_time(player, pos)

            if t_needed <= time:
                return {"pos": pos.copy(), "vel": vel.copy(), "time": time}

            diff = abs(t_needed - time)
            if diff < best_diff:
                best_diff = diff
                best_pos = pos.copy()
                best_vel = vel.copy()
                best_time = time

        return {"pos": best_pos, "vel": best_vel, "time": best_time}
    #Hàm dua ra v? trí v?i th?i gian ng?n nh?t mà bot có th? t?i
    @staticmethod
    def find_intercept(player, ball, dt):
        """Trả về riêng vị trí dự đoán để cầu thủ chạm bóng."""
        return AttackBot.find_intercept_info(player, ball, dt)["pos"]
    #Hàm phòng th?
    #Phòng th? b?ng cách ch?y theo tia t? player.pos d?n di?m gi?a c?a gôn bot
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
            return ball.pos  # Lao th?ng vào bóng

        dynamic_buffer = min(100, dist_to_goal * 0.3) 
        
        target = opponent.pos - dir_to_ball * dynamic_buffer

        return target
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
        """Chọn điểm hợp lý tốt nhất trong miệng gôn để sút."""
        
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
        orbit_radius = PLAYER_RADIUS + BALL_RADIUS + 5
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

        bot_intercept_info = AttackBot.find_intercept_info(self, ball, dt)
        bot_intercept = bot_intercept_info["pos"]
        t_bot = AttackBot.estimate_time(self, bot_intercept)

        enemy_intercept = AttackBot.find_intercept(opponent, ball, dt)
        t_enemy = AttackBot.estimate_time(opponent, enemy_intercept)

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
        if diff.length() < PLAYER_RADIUS + BALL_RADIUS + KICK_RANGE:
            state = "ATTACK"
        elif t_bot > t_enemy + 2:
            state = "DEFEND"
        elif self.NEED_SPAM(opponent,ball):
            state = "SPAM"
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
                if behind_alignment > 0.98 or AttackBot.is_not_player_ball_line_on_goal(self,ball):
                    should_kick = True
                else:
                    should_kick = False
                    target = AttackBot.orbit_attack_target(self.pos, ball.pos, target)
            else:
                target = ball.pos
                should_kick = False
        elif state == "DEFEND":
            self.cache_target_clear=pygame.Vector2(0,0)
            target = AttackBot.jockey_position(self, ball, opponent)
        elif state == "ATTACK":
            self.cache_target_clear=pygame.Vector2(0,0)
            goal_center = enemy_goal_center
            goal_top = pygame.Vector2(0, GOAL_TOP + 0.1)
            goal_bottom = pygame.Vector2(0, GOAL_BOTTOM - 0.1)
            
            best_goal_target = AttackBot.find_best_goal_target(ball.pos, goal_center, goal_top, goal_bottom)
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
                if behind_alignment > 0.99 or AttackBot.is_player_ball_line_on_goal(self,ball) or check_it:
                    should_kick = True
                else:
                    should_kick = False
                    target = AttackBot.orbit_attack_target(self.pos, ball.pos, target)
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



class DefBot:
    """Bot phòng thủ, bảo vệ gôn nhà và hỗ trợ phá bóng khi cần thiết."""
    def __init__(self, player, attack_bot=None):
        """Khởi tạo bot phòng thủ, có thể nhận thêm thông tin từ bot tấn công đồng đội."""
        object.__setattr__(self, "player", player)
        object.__setattr__(self, "attack_bot", attack_bot)
        object.__setattr__(self, "attack_bot_pos", None)

    def __getattr__(self, name):
        return getattr(self.player, name)

    def __setattr__(self, name, value):
        if name in ("player", "attack_bot", "attack_bot_pos"):
            object.__setattr__(self, name, value)
        else:
            setattr(self.player, name, value)

    def get_attack_bot_pos(self):
        """Lấy vị trí hiện tại của bot tấn công đồng đội."""
        if self.attack_bot is None:
            return None
        return self.attack_bot.player.pos.copy()

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

        # ===== x? lý (d?i hu?ng) =====
        t_perp = v_perp / a

        if v_parallel < 0:
            t_stop = -v_parallel / a
            s_stop = v_parallel * t_stop + 0.5 * a * t_stop**2
        else:
            t_stop = 0
            s_stop = 0

        dist = max(dist - s_stop, 0)
        v0 = max(v_parallel, 0)

        # ===== tang t?c t?i max =====
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
            pos, vel = DefBot.simulate_ball_step(pos, vel, sim_dt)
            time += sim_dt

            t_needed = DefBot.estimate_time(player, pos)

            if t_needed <= time:
                return {"pos": pos.copy(), "vel": vel.copy(), "time": time}

            diff = abs(t_needed - time)
            if diff < best_diff:
                best_diff = diff
                best_pos = pos.copy()
                best_vel = vel.copy()
                best_time = time

        return {"pos": best_pos, "vel": best_vel, "time": best_time}
    #Hàm dua ra v? trí v?i th?i gian ng?n nh?t mà bot có th? t?i
    @staticmethod
    def find_intercept(player, ball, dt):
        """Trả về riêng vị trí dự đoán để cầu thủ chạm bóng."""
        return DefBot.find_intercept_info(player, ball, dt)["pos"]
    @staticmethod
    def ball_fly_goal(ball, dt, goal_x=FIELD_WIDTH):
        """Dự đoán liệu bóng có đang bay thẳng vào gôn nhà hay không."""
        max_t = 3.0
        sim_dt = max(1 / 180, min(dt, 1 / 60))
        pos = ball.pos.copy()
        vel = ball.vel.copy()
        time = 0.0
        last_pos = pos.copy()
        last_vel = vel.copy()

        while time < max_t:

            last_pos = pos.copy()

            pos, vel = DefBot.simulate_ball_step(
                pos,
                vel,
                sim_dt
            )

            if (
                last_pos.x <= FIELD_WIDTH
                and
                pos.x > FIELD_WIDTH
            ):
                cross_y = (last_pos.y + pos.y) * 0.5

                if GOAL_TOP < cross_y < GOAL_BOTTOM:
                    return {
                        "time": time,
                        "pos": pos.copy(),
                        "vel": vel.copy(),
                        "last_pos": last_pos,
                        "last_vel": last_vel,
                    }

            if vel.length_squared() < 25:
                break

        return None
    #Hàm phòng th?
    #Phòng th? b?ng cách ch?y theo tia t? player.pos d?n di?m gi?a c?a gôn bot
    def jockey_position(self, ball, opponent):
        """Chọn vị trí phòng thủ tối ưu giữa đối thủ và gôn nhà."""
        my_goal = pygame.Vector2(FIELD_WIDTH, FIELD_HEIGHT // 2)
        goal_to_ball_vec = opponent.pos - my_goal
        dist_to_goal = goal_to_ball_vec.length()
        goal_top_pos = pygame.Vector2(
            FIELD_WIDTH,
            GOAL_TOP
        )

        goal_bottom_pos = pygame.Vector2(
            FIELD_WIDTH,
            GOAL_BOTTOM
        )

        to_player = self.pos - ball.pos
        to_my_goal1 = goal_top_pos - ball.pos
        to_my_goal2 = goal_bottom_pos - ball.pos

        player_goal_alignment1 = (
            to_player.normalize().dot(
                to_my_goal1.normalize()
            )
        )
        player_goal_alignment2 = (
            to_player.normalize().dot(
                to_my_goal2.normalize()
            )
        )

        to_attack_bot = self.attack_bot.pos - ball.pos
        alignment1 = to_attack_bot.normalize().dot(
            to_my_goal1.normalize()
        )
        alignment2 = to_attack_bot.normalize().dot(
            to_my_goal2.normalize()
        )
        if self.attack_bot.pos.x < self.pos.x+10+PLAYER_RADIUS*2:
            return my_goal
        dir_to_ball = goal_to_ball_vec.normalize()
        ball_control_dist = 0 # (ball.pos - opponent.pos).length()
        if (alignment1 < -0.2 or alignment2 < -0.2):
            if ball_control_dist > PLAYER_RADIUS + BALL_RADIUS + 1000 or dist_to_goal < 280:
                return ball.pos.copy()  # Lao th?ng vào bóng

        dynamic_buffer = min(100, dist_to_goal * 0.3) 
        
        target = opponent.pos - dir_to_ball * dynamic_buffer
        target.x = max(target.x, FIELD_WIDTH - FIELD_WIDTH * 0.3)
        return target
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
        """Chọn điểm hợp lý tốt nhất trong miệng gôn để sút."""
        
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
        orbit_radius = PLAYER_RADIUS + BALL_RADIUS + 5
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
        self.attack_bot_pos = self.get_attack_bot_pos()

        enemy_goal_center = pygame.Vector2(0, FIELD_HEIGHT // 2)
        my_goal = pygame.Vector2(FIELD_WIDTH, FIELD_HEIGHT // 2)

        bot_intercept_info = DefBot.find_intercept_info(self, ball, dt)
        bot_intercept = bot_intercept_info["pos"]
        t_bot = DefBot.estimate_time(self, bot_intercept)

        enemy_intercept = DefBot.find_intercept(opponent, ball, dt)
        t_enemy = DefBot.estimate_time(opponent, enemy_intercept)

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
        goal_prediction = self.ball_fly_goal(ball, dt)
        if t_bot > t_enemy - 0.15:
            state = "DEFEND"
        elif t_bot - t_enemy < 0.15 and t_bot - t_enemy > -1 and diff.normalize().x >=0:
            state = "CLEAR"
        elif self.NEED_SPAM(opponent,ball):
            state = "SPAM"
        elif diff.length() < PLAYER_RADIUS + BALL_RADIUS + KICK_RANGE:
            state = "ATTACK"
        else:
            state = "ATTACK"
        okkkk = False
        if goal_prediction is not None:
            if target!=goal_prediction["pos"]:
                target = goal_prediction["pos"]
                should_kick = True
                okkkk = True
            else:
                state = "CLEAR"
                okkkk = False
        if not okkkk:
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
                    if behind_alignment > 0.98 or DefBot.is_not_player_ball_line_on_goal(self,ball):
                        should_kick = True
                    else:
                        should_kick = False
                        target = DefBot.orbit_attack_target(self.pos, ball.pos, target)
                else:
                    target = ball.pos
                    should_kick = False
            elif state == "DEFEND":
                self.cache_target_clear=pygame.Vector2(0,0)
                target = DefBot.jockey_position(self, ball, opponent)
            elif state == "ATTACK":
                self.cache_target_clear=pygame.Vector2(0,0)
                goal_center = enemy_goal_center
                goal_top = pygame.Vector2(0, GOAL_TOP + 0.1)
                goal_bottom = pygame.Vector2(0, GOAL_BOTTOM - 0.1)
                
                best_goal_target = DefBot.find_best_goal_target(ball.pos, goal_center, goal_top, goal_bottom)
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
                    if behind_alignment > 0.99 or DefBot.is_player_ball_line_on_goal(self,ball) or check_it:
                        should_kick = True
                    else:
                        should_kick = False
                        target = DefBot.orbit_attack_target(self.pos, ball.pos, target)
                else:
                    target = ball.pos
                    should_kick = False
            elif state == "SPAM":
                should_kick = True
                target = ball.pos
        target.x = max(target.x, FIELD_WIDTH - FIELD_WIDTH * 0.5)
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


