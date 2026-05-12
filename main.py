import pygame
import sys
import asyncio
import config as _config_module
from collections import deque
from config import *
from skill_replay import replay_buffer
from ball import Ball
from debug import DebugOverlay
from effect import SkillEffectManager
from render import draw_scene
from player import Player
from profile import PlayerProfile, UPGRADE_DEFS
#------------------------ CONTROLS------------------------
controls1 = {
    "up": pygame.K_w,
    "down": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d
}

controls2 = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT
}
#---------------------------------------------------------
action_keys = {
    "p1_kick": pygame.K_SPACE,
    "p2_kick": pygame.K_RETURN,
    "p1_skill": pygame.K_q,
    "p2_skill": pygame.K_RSHIFT,
}
settings = {
    "music_volume": 70,
    "sfx_volume": 80,
    "match_minutes": 3,
    "max_goals": 5,
}
BACK_BUTTON_RECT = pygame.Rect(WINDOW_WIDTH - 180, WINDOW_HEIGHT - 70, 140, 45)
CHARACTERS = [
    ("Isagi", (200, 40, 40)),
    ("Nagi", (40, 40, 200)),
    ("Bachira", (255, 215, 0)),
    ("Kunigami", (128, 0, 128)),
    ("Chigiri", (0, 255, 255)),
    ("Itachi", (95, 35, 135)),
]
ui_buttons = {}
game_mode = ""
REWIND_SECONDS = 3.0
REWIND_FRAME_COUNT = int(REWIND_SECONDS * 60)
ITACHI_FREEZE_SECONDS = 0.9
goal_log = []
last_toucher = None
_menu_logo = None
_menu_logo_failed = False
# ── Profile & Upgrade ──────────────────────────────────────────────────────
profile = PlayerProfile()
upgrade_tab = "physical"      # "physical" | "skill"
last_match_reward = None      # dict set khi trận kết thúc

# ========================= SOUND =========================
SOUND_KICK_PATH    = "assert/sound/kick.wav"
SOUND_GOAL_PATH    = "assert/sound/goal-cheer.wav"
SOUND_GENERAL_PATH = "assert/sound/general.mp3"
SOUND_ITACHI_PATH  = "assert/sound/effect skill/Itachi Mangekyou Sharingan Sound Effect - YouTube.mp3"
_snd_kick   = None
_snd_goal   = None
_snd_itachi = None
_music_playing = False


def get_menu_logo():
    global _menu_logo, _menu_logo_failed

    if _menu_logo is not None or _menu_logo_failed:
        return _menu_logo

    try:
        image = pygame.image.load(MENU_LOGO_IMAGE_PATH).convert_alpha()
        target_width = min(620, WINDOW_WIDTH - 120)
        scale = target_width / image.get_width()
        target_height = int(image.get_height() * scale)
        _menu_logo = pygame.transform.smoothscale(image, (target_width, target_height))
    except (pygame.error, FileNotFoundError):
        _menu_logo_failed = True

    return _menu_logo


# ========================= SOUND HELPERS =========================
def _apply_volume():
    """Cập nhật âm lượng cho music và sfx riêng biệt dựa trên settings."""
    music_vol = settings["music_volume"] / 100.0
    sfx_vol   = settings["sfx_volume"] / 100.0
    if _snd_kick:
        _snd_kick.set_volume(sfx_vol)
    if _snd_goal:
        _snd_goal.set_volume(sfx_vol)
    if _snd_itachi:
        _snd_itachi.set_volume(sfx_vol)
    pygame.mixer.music.set_volume(music_vol)


def _start_general_music():
    """Bắt đầu phát nhạc nền general."""
    global _music_playing
    if not _music_playing:
        try:
            pygame.mixer.music.load(SOUND_GENERAL_PATH)
            pygame.mixer.music.play(-1)  # Loop vô tận
            _music_playing = True
        except (pygame.error, FileNotFoundError):
            pass


def _stop_general_music():
    """Dừng nhạc nền general."""
    global _music_playing
    pygame.mixer.music.stop()
    _music_playing = False


def _play_kick_sound():
    """Phát âm thanh sút bóng."""
    if _snd_kick:
        _snd_kick.play()


def _play_goal_sound():
    """Phát âm thanh ăn mừng bàn thắng."""
    if _snd_goal:
        _snd_goal.play()

def _stop_goal_sound():
    """Dừng âm thanh ăn mừng bàn thắng."""
    if _snd_goal:
        _snd_goal.stop()


def _play_itachi_sound():
    """Phát âm thanh Itachi Mangekyou Sharingan khi dùng skill."""
    if _snd_itachi:
        _snd_itachi.play()


def _stop_itachi_sound():
    """Dừng âm thanh Itachi khi rewind kết thúc."""
    if _snd_itachi:
        _snd_itachi.stop()


def draw_button(screen, font, button_id, text, rect, base_color=(92, 134, 96), hover_color=(118, 165, 107), text_color=(245, 250, 238)):
    ui_buttons[button_id] = rect
    mouse_pos = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mouse_pos)
    color = hover_color if hovered else base_color
    pygame.draw.rect(screen, color, rect, border_radius=8)
    border_color = (235, 246, 218) if hovered else (150, 190, 140)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)
    label = font.render(text, True, text_color)
    screen.blit(
        label,
        (
            rect.centerx - label.get_width() // 2,
            rect.centery - label.get_height() // 2,
        ),
    )


def draw_back_button(screen, font):
    draw_button(
        screen,
        font,
        "back",
        "Back",
        BACK_BUTTON_RECT,
        base_color=(185, 45, 45),
        hover_color=(225, 70, 65),
    )


def draw_small_button(screen, font, button_id, text, rect):
    draw_button(
        screen,
        font,
        button_id,
        text,
        rect,
        base_color=(68, 105, 74),
        hover_color=(105, 150, 86),
    )


def draw_label(screen, font, text, center_x, center_y, color=(245, 250, 238)):
    label = font.render(text, True, color)
    screen.blit(
        label,
        (
            center_x - label.get_width() // 2,
            center_y - label.get_height() // 2,
        ),
    )


def draw_center_text(screen, font, lines, start_y, color=(245, 250, 238), gap=58):
    for index, text in enumerate(lines):
        label = font.render(text, True, color)
        screen.blit(label, (WINDOW_WIDTH // 2 - label.get_width() // 2, start_y + index * gap))


def format_key(key):
    return pygame.key.name(key).upper()


def choose_character(player, player_number, character_index):
    name, color = CHARACTERS[character_index]
    player.information(name, color=color)
    return player_number + 1


def reset_match(ball, player1, player2, effects):
    global game_mode

    game_mode = ""
    replay_buffer.clear()
    effects.reset()
    ball.reset()
    player1.reset(FIELD_WIDTH // 4, FIELD_HEIGHT // 2, player1.color, controls1)
    player2.reset(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2, player2.color, controls2)


def player_state(player):
    """Chụp trạng thái có thể thay đổi của cầu thủ để dùng cho rewind."""
    return {
        "pos": player.pos.copy(),
        "vel": player.vel.copy(),
        "kick_timer": player.kick_timer,
        "kicked": player.kicked,
        "ball_ok": player.ball_ok,
        "can_kick": player.can_kick,
        "just_kicked": player.just_kicked,
        "last_kick_direction": player.last_kick_direction.copy(),
        "mass": player.mass,
        "acceleration": player.acceleration,
        "damping": player.damping,
        "max_speed": player.max_speed,
        "skill_active": player.skill_active,
        "skill_timer": player.skill_timer,
        "skill_cooldown": player.skill_cooldown,
        "time_rewind": player.time_rewind,
        "rewind_timer": player.rewind_timer,
    }


def restore_player_state(player, state):
    """Khôi phục trạng thái cầu thủ từ snapshot rewind."""
    player.pos = state["pos"].copy()
    player.vel = state["vel"].copy()
    player.kick_timer = state["kick_timer"]
    player.kicked = state["kicked"]
    player.ball_ok = state["ball_ok"]
    player.can_kick = state["can_kick"]
    player.just_kicked = state["just_kicked"]
    player.last_kick_direction = state["last_kick_direction"].copy()
    player.mass = state["mass"]
    player.acceleration = state["acceleration"]
    player.damping = state["damping"]
    player.max_speed = state["max_speed"]
    player.skill_active = state["skill_active"]
    player.skill_timer = state["skill_timer"]
    player.skill_cooldown = state["skill_cooldown"]
    player.time_rewind = state["time_rewind"]
    player.rewind_timer = state["rewind_timer"]


def game_snapshot(ball, player1, player2, effects, ball_ok):
    """Chụp toàn bộ trạng thái trận đấu cho kỹ năng quay ngược của Itachi."""
    return {
        "ball_pos": ball.pos.copy(),
        "ball_vel": ball.vel.copy(),
        "p1": player_state(player1),
        "p2": player_state(player2),
        "effects": effects.get_state(),
        "ball_ok": ball_ok,
    }


def restore_game_snapshot(snapshot, ball, player1, player2, effects):
    """Khôi phục bóng, cầu thủ, hiệu ứng và trạng thái hiển thị bóng từ snapshot."""
    ball.pos = snapshot["ball_pos"].copy()
    ball.vel = snapshot["ball_vel"].copy()
    restore_player_state(player1, snapshot["p1"])
    restore_player_state(player2, snapshot["p2"])
    effects.set_state(snapshot["effects"])
    return snapshot["ball_ok"]


def finish_itachi_rewind(caster):
    """Kết thúc rewind của Itachi và đặt hồi chiêu cho người dùng kỹ năng."""
    caster.skill_active = False
    caster.skill_timer = 0
    caster.skill_cooldown = 15.0
    caster.time_rewind = False
    caster.rewind_timer = 0


def update_game(ball, player1, player2, dt, score_red, score_blue, match_time_left):
    """Cập nhật một frame gameplay thật và trả về điểm số cùng trạng thái bóng."""
    global game_mode, last_toucher
    keys = pygame.key.get_pressed()
    player1.handle_input(keys, dt)
    if player2.is_bot:
        if player2.bot_update(player1, ball, dt):
            _play_kick_sound()
    else:
        player2.handle_input(keys, dt)
    player1.update(player2, dt, ball)
    player2.update(player1, dt, ball)
    ball_ok = player1.ball_ok and player2.ball_ok
    player1.handle_player_collision(player2)
    player1.handle_wall_collision()
    player2.handle_wall_collision()
   # ball.apply_input(keys, dt)
    ball.update(player1,player2, dt)
    ball.handle_post_collision()
    if player1.handle_ball_collision(ball):
        last_toucher = 1
    if player2.handle_ball_collision(ball):
        last_toucher = 2

    goal = ball.handle_wall_collision()

    total_time = settings["match_minutes"] * 60
    elapsed = total_time - match_time_left

    if goal == "RED_GOAL":
        score_red += 1
        game_mode = "REPLAY"
        _play_goal_sound()
        if last_toucher == 1:
            goal_log.append({"time": elapsed, "player": 1, "type": "G"})
        else:
            goal_log.append({"time": elapsed, "player": 2, "type": "OG"})

    elif goal == "BLUE_GOAL":
        score_blue += 1
        game_mode = "REPLAY"
        _play_goal_sound()
        if last_toucher == 2:
            goal_log.append({"time": elapsed, "player": 2, "type": "G"})
        else:
            goal_log.append({"time": elapsed, "player": 1, "type": "OG"})
    return score_red, score_blue, ball_ok
#------------------------ Vẽ giao diện mở đầu------------------------
def draw_home(screen, font):
    ui_buttons.clear()
    screen.fill((73, 111, 82))

    logo = get_menu_logo()
    if logo is not None:
        logo_x = WINDOW_WIDTH // 2 - logo.get_width() // 2
        screen.blit(logo, (logo_x, 25))

    button_w = 320
    button_h = 55
    start_y = 250
    draw_button(screen, font, "home_play", "Vao game", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, start_y, button_w, button_h))
    draw_button(screen, font, "home_settings", "Setting", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, start_y + 72, button_w, button_h))
    draw_button(screen, font, "home_upgrade", "Nang cap", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, start_y + 144, button_w, button_h))
    pygame.display.flip()


def draw_menu(screen, font):
    ui_buttons.clear()
    """Vẽ menu đầu tiên để chọn chơi với bot hoặc PvP."""
    screen.fill((73, 111, 82))

    logo = get_menu_logo()
    if logo is not None:
        logo_x = WINDOW_WIDTH // 2 - logo.get_width() // 2
        screen.blit(logo, (logo_x, 35))
        options_y = 280
    else:
        title = font.render("HAXBALL", True, (245, 250, 238))
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 70))
        options_y = 200

    button_w = 340
    button_h = 58
    draw_button(screen, font, "mode_bot", "Play vs Bot", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, options_y, button_w, button_h))
    draw_button(screen, font, "mode_pvp", "Play PvP", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, options_y + 76, button_w, button_h))
    draw_back_button(screen, font)

    pygame.display.flip()


def draw_settings(screen, font, waiting_for_key):
    ui_buttons.clear()
    screen.fill((73, 111, 82))
    title = font.render("SETTING", True, (245, 250, 238))
    screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 35))

    if waiting_for_key:
        wait_text = font.render("Nhan phim moi...", True, (255, 235, 120))
        screen.blit(wait_text, (WINDOW_WIDTH // 2 - wait_text.get_width() // 2, 95))

    small_font = pygame.font.SysFont("Arial", 26)
    value_font = pygame.font.SysFont("Arial", 30)
    left_x = 75
    right_x = WINDOW_WIDTH // 2 + 25
    top_y = 130
    row_h = 62

    numeric_rows = [
        ("music_volume", "Nhac nen", f"{settings['music_volume']}%", left_x, top_y),
        ("sfx_volume", "Am thanh", f"{settings['sfx_volume']}%", left_x, top_y + row_h),
        ("match_minutes", "Thoi gian da", f"{settings['match_minutes']} phut", left_x, top_y + row_h * 2),
        ("max_goals", "So ban toi da", str(settings["max_goals"]), left_x, top_y + row_h * 3),
    ]
    key_rows = [
        ("p1_kick", "P1 sut", format_key(action_keys["p1_kick"]), right_x, top_y),
        ("p1_skill", "P1 skill", format_key(action_keys["p1_skill"]), right_x, top_y + row_h),
        ("p2_kick", "P2 sut", format_key(action_keys["p2_kick"]), right_x, top_y + row_h * 2),
        ("p2_skill", "P2 skill", format_key(action_keys["p2_skill"]), right_x, top_y + row_h * 3),
    ]

    for key, label_text, value, x, y in numeric_rows:
        draw_label(screen, small_font, label_text, x + 90, y + 25)
        draw_small_button(screen, value_font, f"{key}_down", "-", pygame.Rect(x + 205, y, 48, 48))
        draw_label(screen, value_font, value, x + 310, y + 24)
        draw_small_button(screen, value_font, f"{key}_up", "+", pygame.Rect(x + 370, y, 48, 48))

    for key, label_text, value, x, y in key_rows:
        draw_label(screen, small_font, label_text, x + 75, y + 25)
        color = (255, 235, 120) if waiting_for_key == key else (245, 250, 238)
        draw_button(
            screen,
            value_font,
            f"key_{key}",
            value,
            pygame.Rect(x + 155, y, 215, 48),
            text_color=color,
        )
    draw_back_button(screen, font)
    pygame.display.flip()


def draw_upgrade(screen, font):
    """Màn hình nâng cấp premium: profile bar + tabs + upgrade cards."""
    ui_buttons.clear()

    W, H = WINDOW_WIDTH, WINDOW_HEIGHT
    screen.fill((16, 18, 26))

    # ── Fonts ──────────────────────────────────────────────────────────────
    lv_font   = pygame.font.SysFont("Arial", 30, bold=True)
    pf_font   = pygame.font.SysFont("Arial", 20, bold=True)
    sm_font   = pygame.font.SysFont("Arial", 17)
    card_name = pygame.font.SysFont("Arial", 19, bold=True)
    card_desc = pygame.font.SysFont("Arial", 15)
    card_cost = pygame.font.SysFont("Arial", 16, bold=True)

    # ── Profile bar ────────────────────────────────────────────────────────
    bar_h = 64
    pygame.draw.rect(screen, (24, 28, 42), pygame.Rect(0, 0, W, bar_h))
    pygame.draw.line(screen, (50, 60, 88), (0, bar_h), (W, bar_h), 1)

    # Level badge
    lv_surf = lv_font.render(f"Lv.{profile.level}", True, (255, 215, 0))
    screen.blit(lv_surf, (18, bar_h // 2 - lv_surf.get_height() // 2))

    # XP bar
    xp_bx, xp_by, xp_bw, xp_bh2 = 100, 16, 260, 12
    xp_ratio = min(profile.xp / max(profile.xp_to_next(), 1), 1.0)
    pygame.draw.rect(screen, (38, 42, 60), pygame.Rect(xp_bx, xp_by, xp_bw, xp_bh2), border_radius=6)
    if xp_ratio > 0:
        pygame.draw.rect(screen, (70, 150, 255),
                         pygame.Rect(xp_bx, xp_by, int(xp_bw * xp_ratio), xp_bh2), border_radius=6)
    xp_lbl = sm_font.render(f"XP  {profile.xp} / {profile.xp_to_next()}", True, (140, 170, 220))
    screen.blit(xp_lbl, (xp_bx, xp_by + xp_bh2 + 4))

    # Coins
    coin_surf = pf_font.render(f"Coins: {profile.coins}", True, (255, 200, 50))
    screen.blit(coin_surf, (400, bar_h // 2 - coin_surf.get_height() // 2))

    # Title
    title_surf = lv_font.render("NANG CAP", True, (200, 210, 255))
    screen.blit(title_surf, (W - title_surf.get_width() - 18, bar_h // 2 - title_surf.get_height() // 2))

    # ── Tab buttons ─────────────────────────────────────────────────────────
    tab_y = bar_h + 8
    tab_h2, tab_w = 36, 150
    tabs = [("physical", "Physical"), ("skill", "Skill")]
    tabs_total = len(tabs) * tab_w + (len(tabs) - 1) * 16
    tab_sx = W // 2 - tabs_total // 2

    for i, (tk, tlabel) in enumerate(tabs):
        trect = pygame.Rect(tab_sx + i * (tab_w + 16), tab_y, tab_w, tab_h2)
        active = upgrade_tab == tk
        pygame.draw.rect(screen, (55, 100, 200) if active else (32, 36, 54), trect, border_radius=8)
        if active:
            pygame.draw.rect(screen, (100, 160, 255), trect, 2, border_radius=8)
        tf = pygame.font.SysFont("Arial", 20, bold=active)
        ts = tf.render(tlabel, True, (245, 250, 238))
        screen.blit(ts, (trect.centerx - ts.get_width() // 2, trect.centery - ts.get_height() // 2))
        ui_buttons[f"upgrade_tab_{tk}"] = trect

    # ── Cards ────────────────────────────────────────────────────────────────
    defs = UPGRADE_DEFS[upgrade_tab]
    card_w, card_h2 = 420, 108
    card_gap_x, card_gap_y = 18, 12
    per_row = 2
    total_cw = per_row * card_w + (per_row - 1) * card_gap_x
    sx = (W - total_cw) // 2
    sy = tab_y + tab_h2 + 14

    for i, udef in enumerate(defs):
        col = i % per_row
        row = i // per_row
        cx2 = sx + col * (card_w + card_gap_x)
        cy2 = sy + row * (card_h2 + card_gap_y)
        key = udef["key"]
        lvl = profile.get_stat_level(key)
        max_lvl = udef["max_level"]
        cost = profile.get_upgrade_cost(key)
        is_maxed = cost is None
        can_buy = profile.can_upgrade(key)

        # Card background & border
        if is_maxed:
            bg_col, bd_col = (22, 42, 28), (50, 180, 70)
        elif can_buy:
            bg_col, bd_col = (22, 28, 48), (70, 130, 255)
        else:
            bg_col, bd_col = (20, 22, 32), (44, 48, 68)

        card_rect = pygame.Rect(cx2, cy2, card_w, card_h2)
        pygame.draw.rect(screen, bg_col, card_rect, border_radius=10)
        pygame.draw.rect(screen, bd_col, card_rect, 2, border_radius=10)

        # Name & level
        nm = card_name.render(udef["name"], True, (225, 230, 255))
        lv_c = (60, 200, 80) if is_maxed else (255, 210, 0)
        lv_s = card_name.render(f"Lv.{lvl}/{max_lvl}", True, lv_c)
        screen.blit(nm, (cx2 + 12, cy2 + 9))
        screen.blit(lv_s, (cx2 + card_w - lv_s.get_width() - 12, cy2 + 9))

        # Progress bar (segmented)
        pb_x, pb_y2, pb_w, pb_h3 = cx2 + 12, cy2 + 34, card_w - 24, 10
        pygame.draw.rect(screen, (30, 34, 50), pygame.Rect(pb_x, pb_y2, pb_w, pb_h3), border_radius=5)
        if lvl > 0:
            fill_w = int(pb_w * lvl / max_lvl)
            fill_c = (50, 200, 75) if is_maxed else (70, 145, 255)
            pygame.draw.rect(screen, fill_c,
                             pygame.Rect(pb_x, pb_y2, fill_w, pb_h3), border_radius=5)
        for t in range(1, max_lvl):
            tx3 = pb_x + int(pb_w * t / max_lvl)
            pygame.draw.line(screen, (16, 18, 26), (tx3, pb_y2), (tx3, pb_y2 + pb_h3), 2)

        # Description (current bonus)
        bonus_pct = lvl * udef["bonus_per_level"] * 100
        desc_str = udef["desc_template"].format(bonus_pct)
        cap_pct  = udef["stat_cap"] * 100
        full_desc = f"{desc_str}  |  cap: {cap_pct:.0f}%"
        ds = card_desc.render(full_desc, True, (140, 160, 200))
        screen.blit(ds, (cx2 + 12, cy2 + 52))

        # Cost button or MAXED badge
        if is_maxed:
            ms = card_cost.render("✓ MAXED", True, (55, 210, 80))
            screen.blit(ms, (cx2 + card_w - ms.get_width() - 12, cy2 + card_h2 - ms.get_height() - 8))
        else:
            btn_w2, btn_bh = 128, 26
            btn_r = pygame.Rect(cx2 + card_w - btn_w2 - 10, cy2 + card_h2 - btn_bh - 8, btn_w2, btn_bh)
            btn_c = (55, 115, 210) if can_buy else (38, 40, 58)
            pygame.draw.rect(screen, btn_c, btn_r, border_radius=6)
            cost_s = card_cost.render(f"{cost} coins", True,
                                      (245, 250, 238) if can_buy else (90, 95, 120))
            screen.blit(cost_s, (btn_r.centerx - cost_s.get_width() // 2,
                                 btn_r.centery - cost_s.get_height() // 2))
            ui_buttons[f"upgrade_{key}"] = btn_r

    draw_back_button(screen, font)
    pygame.display.flip()



def _format_goal_time(seconds):
    """Chuyển số giây đã trôi qua thành chuỗi mm:ss."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def draw_result(screen, font, score_red, score_blue):
    """Vẽ màn hình kết quả trận đấu với timeline ghi bàn và phần thưởng."""
    ui_buttons.clear()
    screen.fill((30, 30, 38))

    big_font   = pygame.font.SysFont("Arial", 60, bold=True)
    sub_font   = pygame.font.SysFont("Arial", 28)
    small_font = pygame.font.SysFont("Arial", 21)
    rew_font   = pygame.font.SysFont("Arial", 19, bold=True)

    # Tiêu đề
    if score_red > score_blue:
        result_text = "Player 1 Win!"
        result_color = (255, 215, 0)
    elif score_blue > score_red:
        result_text = "Player 2 Win!"
        result_color = (255, 215, 0)
    else:
        result_text = "Chuan bi da pen...."
        result_color = (180, 180, 180)

    result_label = big_font.render(result_text, True, result_color)
    screen.blit(result_label, (WINDOW_WIDTH // 2 - result_label.get_width() // 2, 24))

    # Tỉ số
    score_font  = pygame.font.SysFont("Arial", 50, bold=True)
    score_str   = f"{score_red}  -  {score_blue}"
    score_label = score_font.render(score_str, True, (245, 250, 238))
    screen.blit(score_label, (WINDOW_WIDTH // 2 - score_label.get_width() // 2, 95))

    # Tên Player hai bên
    cx       = WINDOW_WIDTH // 2
    p1_label = sub_font.render("Player 1", True, (200, 80, 80))
    p2_label = sub_font.render("Player 2", True, (80, 80, 200))
    p1_col_x = cx - 175
    p2_col_x = cx + 175
    screen.blit(p1_label, (p1_col_x - p1_label.get_width() // 2, 158))
    screen.blit(p2_label, (p2_col_x - p2_label.get_width() // 2, 158))

    pygame.draw.line(screen, (80, 80, 90), (cx - 300, 192), (cx + 300, 192), 1)

    # Timeline ghi bàn
    p1_goals = [g for g in goal_log if g["player"] == 1]
    p2_goals = [g for g in goal_log if g["player"] == 2]
    row_y, row_gap = 200, 26
    for i, g in enumerate(p1_goals):
        color = (180, 180, 180) if g["type"] == "G" else (220, 120, 120)
        lbl   = small_font.render(f"{_format_goal_time(g['time'])}'  {g['type']}", True, color)
        screen.blit(lbl, (p1_col_x - lbl.get_width() // 2, row_y + i * row_gap))
    for i, g in enumerate(p2_goals):
        color = (180, 180, 180) if g["type"] == "G" else (220, 120, 120)
        lbl   = small_font.render(f"{_format_goal_time(g['time'])}'  {g['type']}", True, color)
        screen.blit(lbl, (p2_col_x - lbl.get_width() // 2, row_y + i * row_gap))

    max_rows    = max(len(p1_goals), len(p2_goals), 1)
    line_bottom = row_y + max_rows * row_gap + 5
    pygame.draw.line(screen, (60, 60, 70), (cx, 158), (cx, line_bottom), 1)

    # ── Reward panel ──────────────────────────────────────────────────────
    panel_y = max(line_bottom + 10, 335)
    if last_match_reward:
        rw = last_match_reward
        panel_w, panel_h = 380, 52
        panel_x = cx - panel_w // 2
        pygame.draw.rect(screen, (28, 32, 48), pygame.Rect(panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(screen, (60, 90, 180), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        xp_str   = f"+{rw['xp']} XP"
        coin_str = f"+{rw['coins']} Coins"
        lv_str   = "  ▲ LEVEL UP!" if rw.get("leveled_up") else f"  Lv.{profile.level}"
        full_str = f"{xp_str}    {coin_str}{lv_str}"
        rs = rew_font.render(full_str, True, (200, 230, 255))
        screen.blit(rs, (cx - rs.get_width() // 2, panel_y + panel_h // 2 - rs.get_height() // 2))
        panel_y += panel_h + 8

    # Nút ve Menu + Nang Cap
    btn_w_single = 240
    btn_h        = 50
    gap          = 20
    total_btn_w  = btn_w_single * 2 + gap
    btn_x_start  = cx - total_btn_w // 2
    btn_y        = max(panel_y + 4, 390)

    draw_button(screen, font, "result_home", "Ve Menu",
                pygame.Rect(btn_x_start, btn_y, btn_w_single, btn_h),
                base_color=(92, 134, 96), hover_color=(118, 165, 107))
    draw_button(screen, font, "result_upgrade", "Nang Cap",
                pygame.Rect(btn_x_start + btn_w_single + gap, btn_y, btn_w_single, btn_h),
                base_color=(55, 90, 180), hover_color=(80, 130, 230))
    pygame.display.flip()






def draw_character_select(screen, font, player_number):
    ui_buttons.clear()
    """Vẽ màn hình chọn nhân vật cho người chơi hiện tại."""
    if player_number == 1:
        screen.fill((20, 20, 20))
    else :
        screen.fill((50, 50, 50))
    text = font.render(f"Player {player_number} Choose Character", True, (255,255,255))

    isagi = font.render("1 - Isagi", True, (200,200,200))
    nagi = font.render("2 - Nagi", True, (200,200,200))
    bachira = font.render("3 - Bachira", True, (200,200,200))
    kunigami = font.render("4 - Kunigami", True, (200,200,200))
    chigiri = font.render("5 - Chigiri", True, (200,200,200))
    itachi = font.render("6 - Itachi", True, (200,200,200))
    
    screen.blit(text, (250, 100))
    screen.blit(isagi, (250, 200))
    screen.blit(nagi, (250, 250))
    screen.blit(bachira, (250, 300))
    screen.blit(kunigami, (250, 350))
    screen.blit(chigiri, (250, 400))
    screen.blit(itachi, (250, 450))
    screen.fill((63, 99, 75) if player_number == 1 else (73, 111, 82))
    text = font.render(f"Player {player_number} Choose Character", True, (255,255,255))
    screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 45))
    button_w = 260
    button_h = 56
    gap_x = 35
    gap_y = 24
    start_x = WINDOW_WIDTH // 2 - button_w - gap_x // 2
    start_y = 140
    for index, (name, color) in enumerate(CHARACTERS):
        col = index % 2
        row = index // 2
        rect = pygame.Rect(start_x + col * (button_w + gap_x), start_y + row * (button_h + gap_y), button_w, button_h)
        draw_button(screen, font, f"char_{index}", name, rect, base_color=(75, 112, 82), hover_color=color)
    draw_back_button(screen, font)

    pygame.display.flip()
async def main():
    """Chạy vòng lặp pygame gồm menu, gameplay, replay và rewind."""
    global game_mode, upgrade_tab, last_match_reward
    game_state = "HOME"  # HOME / MENU / SETTINGS / UPGRADE / PLAY_BOT / PLAY_PVP / PLAYING
    waiting_for_key = None
    pygame.init()
    pygame.mixer.init()

    # Load sounds
    global _snd_kick, _snd_goal, _snd_itachi, _music_playing
    try:
        _snd_kick = pygame.mixer.Sound(SOUND_KICK_PATH)
    except (pygame.error, FileNotFoundError):
        _snd_kick = None
    try:
        _snd_goal = pygame.mixer.Sound(SOUND_GOAL_PATH)
    except (pygame.error, FileNotFoundError):
        _snd_goal = None
    try:
        _snd_itachi = pygame.mixer.Sound(SOUND_ITACHI_PATH)
    except (pygame.error, FileNotFoundError):
        _snd_itachi = None

    _apply_volume()
    _start_general_music()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Haxball Solo Environment")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 40)

    # Game state
    ball = Ball()
    player1 = Player(FIELD_WIDTH // 4, FIELD_HEIGHT // 2, COLOR_TEAM_RED, controls1)
    player2 = Player(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2, COLOR_TEAM_BLUE, controls2)
    score_red = 0
    score_blue = 0
    debug_overlay = DebugOverlay()
    effects = SkillEffectManager()
    player_number = 1
    ball_ok = True
    match_time_left = settings["match_minutes"] * 60
    replay_playing = False
    replay_frames = []
    replay_index = 0
    rewind_history = deque(maxlen=REWIND_FRAME_COUNT)
    rewind_active = False
    rewind_frames = []
    rewind_index = 0
    rewind_caster = None
    rewind_freeze_timer = 0.0
    running = True 
    while running:            
        await asyncio.sleep(0)
        dt = clock.tick(60) / 1000.0
        if game_state == "HOME":
            draw_home(screen, font)
        elif game_state == "MENU":
            draw_menu(screen, font)
        elif game_state == "SETTINGS":
            draw_settings(screen, font, waiting_for_key)
        elif game_state == "UPGRADE":
            draw_upgrade(screen, font)
        elif game_state == "RESULT":
            draw_result(screen, font, score_red, score_blue)
        elif game_state == "PLAY_PVP":
            draw_character_select(screen, font, player_number)
        elif game_state == "PLAY_BOT":
            player2.is_bot = True
            if (player_number == 1):
                draw_character_select(screen, font, player_number)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                is_playing_screen = game_state == "PLAYING" or (game_state == "PLAY_BOT" and player_number == 2)
                if is_playing_screen:
                    continue
                if game_state == "RESULT":
                    for button_id, rect in ui_buttons.items():
                        if rect.collidepoint(event.pos) and button_id == "result_home":
                            reset_match(ball, player1, player2, effects)
                            player_number = 1
                            player2.is_bot = False
                            game_state = "HOME"
                            score_red = 0
                            score_blue = 0
                            match_time_left = settings["match_minutes"] * 60
                            goal_log.clear()
                            last_toucher = None
                            break
                    continue
                clicked = None
                for button_id, rect in ui_buttons.items():
                    if rect.collidepoint(event.pos):
                        clicked = button_id
                        break
                if clicked == "back" and game_state != "HOME" and not is_playing_screen:
                    waiting_for_key = None
                    if game_state in ("PLAY_BOT", "PLAY_PVP"):
                        player_number = 1
                        player2.is_bot = False
                    game_state = "HOME" if game_state in ("MENU", "SETTINGS", "UPGRADE") else "MENU"
                    continue
                if clicked == "home_play":
                    game_state = "MENU"
                    continue
                if clicked == "home_settings":
                    game_state = "SETTINGS"
                    continue
                if clicked == "home_upgrade":
                    game_state = "UPGRADE"
                    continue
                if clicked == "result_home":
                    reset_match(ball, player1, player2, effects)
                    player_number = 1
                    player2.is_bot = False
                    game_state = "HOME"
                    score_red = 0
                    score_blue = 0
                    match_time_left = settings["match_minutes"] * 60
                    goal_log.clear()
                    last_toucher = None
                    _start_general_music()
                    continue
                if clicked == "result_upgrade":
                    game_state = "UPGRADE"
                    continue
                if clicked and clicked.startswith("upgrade_tab_"):
                    upgrade_tab = clicked.replace("upgrade_tab_", "", 1)
                    continue
                if clicked and clicked.startswith("upgrade_") and not clicked.startswith("upgrade_tab_"):
                    key = clicked.replace("upgrade_", "", 1)
                    profile.purchase_upgrade(key)
                    continue
                if clicked == "mode_bot":
                    reset_match(ball, player1, player2, effects)
                    score_red = 0
                    score_blue = 0
                    match_time_left = settings["match_minutes"] * 60
                    goal_log.clear()
                    last_toucher = None
                    player_number = 1
                    player2.is_bot = True
                    game_state = "PLAY_BOT"
                    _apply_volume()
                    continue
                if clicked == "mode_pvp":
                    reset_match(ball, player1, player2, effects)
                    score_red = 0
                    score_blue = 0
                    match_time_left = settings["match_minutes"] * 60
                    goal_log.clear()
                    last_toucher = None
                    player_number = 1
                    player2.is_bot = False
                    game_state = "PLAY_PVP"
                    _apply_volume()
                    continue
                if clicked in ("music_volume_down", "music_volume_up"):
                    delta = -10 if clicked.endswith("_down") else 10
                    settings["music_volume"] = max(0, min(100, settings["music_volume"] + delta))
                    _apply_volume()
                    continue
                if clicked in ("sfx_volume_down", "sfx_volume_up"):
                    delta = -10 if clicked.endswith("_down") else 10
                    settings["sfx_volume"] = max(0, min(100, settings["sfx_volume"] + delta))
                    _apply_volume()
                    continue
                if clicked in ("match_minutes_down", "match_minutes_up"):
                    delta = -1 if clicked.endswith("_down") else 1
                    settings["match_minutes"] = max(1, min(10, settings["match_minutes"] + delta))
                    continue
                if clicked in ("max_goals_down", "max_goals_up"):
                    delta = -1 if clicked.endswith("_down") else 1
                    settings["max_goals"] = max(1, min(10, settings["max_goals"] + delta))
                    continue
                if clicked and clicked.startswith("key_"):
                    waiting_for_key = clicked.replace("key_", "", 1)
                    continue
                if clicked and clicked.startswith("char_"):
                    character_index = int(clicked.replace("char_", "", 1))
                    if player_number == 1:
                        player_number = choose_character(player1, player_number, character_index)
                    else:
                        choose_character(player2, player_number, character_index)
                        game_state = "PLAYING"
                        profile.apply_to_player(player1, _config_module)
                        _stop_general_music()
                    continue
            if event.type == pygame.KEYDOWN:
                is_playing_screen = game_state == "PLAYING" or (game_state == "PLAY_BOT" and player_number == 2)
                if waiting_for_key is not None:
                    if event.key != pygame.K_ESCAPE:
                        action_keys[waiting_for_key] = event.key
                    waiting_for_key = None
                    continue
                if debug_overlay.handle_event(event):
                    continue
                if event.key == pygame.K_ESCAPE and game_state != "HOME" and not is_playing_screen:
                    if game_state in ("PLAY_BOT", "PLAY_PVP"):
                        player_number = 1
                        player2.is_bot = False
                    game_state = "HOME" if game_state in ("MENU", "SETTINGS", "UPGRADE") else "MENU"
                    continue
                if game_state in ("HOME", "MENU", "SETTINGS", "UPGRADE", "PLAY_PVP") or (game_state == "PLAY_BOT" and player_number == 1):
                    continue
                if game_state == "HOME":
                    if event.key == pygame.K_1:
                        game_state = "MENU"
                    elif event.key == pygame.K_2:
                        game_state = "SETTINGS"
                    elif event.key == pygame.K_3:
                        game_state = "UPGRADE"
                    continue
                if game_state == "SETTINGS":
                    if event.key == pygame.K_1:
                        settings["music_volume"] = (settings["music_volume"] + 10) % 110
                        _apply_volume()
                    elif event.key == pygame.K_2:
                        settings["sfx_volume"] = (settings["sfx_volume"] + 10) % 110
                        _apply_volume()
                    elif event.key == pygame.K_3:
                        waiting_for_key = "p1_kick"
                    elif event.key == pygame.K_4:
                        waiting_for_key = "p1_skill"
                    elif event.key == pygame.K_5:
                        waiting_for_key = "p2_kick"
                    elif event.key == pygame.K_6:
                        waiting_for_key = "p2_skill"
                    elif event.key == pygame.K_7:
                        settings["match_minutes"] = 1 if settings["match_minutes"] >= 10 else settings["match_minutes"] + 1
                    elif event.key == pygame.K_8:
                        settings["max_goals"] = 1 if settings["max_goals"] >= 10 else settings["max_goals"] + 1
                    continue
                if game_state == "UPGRADE":
                    continue
                if game_state == "MENU":
                    if event.key == pygame.K_1:
                        reset_match(ball, player1, player2, effects)
                        score_red = 0
                        score_blue = 0
                        match_time_left = settings["match_minutes"] * 60
                        player_number = 1
                        player2.is_bot = True
                        game_state = "PLAY_BOT"
                    elif event.key == pygame.K_2:
                        reset_match(ball, player1, player2, effects)
                        score_red = 0
                        score_blue = 0
                        match_time_left = settings["match_minutes"] * 60
                        player_number = 1
                        player2.is_bot = False
                        game_state = "PLAY_PVP"
                    continue
                elif game_state == "PLAY_PVP" or (game_state == "PLAY_BOT" and player_number == 1):
                    if event.key == pygame.K_1 and player_number == 1:
                        player1.information("Isagi", color=(200, 40, 40))  # Đỏ
                        # player1.character = "Isagi"
                        player_number += 1
                    elif event.key == pygame.K_2 and player_number == 1:
                        player1.information("Nagi", color=(40, 40, 200))  # Xanh
                        # player1.character = "Nagi"
                        player_number += 1
                    elif event.key == pygame.K_3 and player_number == 1:
                        player1.information("Bachira", color=(255, 215, 0))  # Vàng
                        # player1.character = "Bachira"
                        player_number += 1
                    elif event.key == pygame.K_4 and player_number == 1:
                        player1.information("Kunigami", color=(128, 0, 128))  # Tím
                        # player1.character = "Kunigami"
                        player_number += 1
                    elif event.key == pygame.K_5 and player_number == 1:
                        player1.information("Chigiri", color=(0, 255, 255))  # Cyan
                        # player1.character = "Chigiri"
                        player_number += 1
                    elif event.key == pygame.K_6 and player_number == 1:
                        player1.information("Itachi", color=(95, 35, 135))
                        player_number += 1
                    elif event.key == pygame.K_1 and player_number == 2:
                        player2.information("Isagi", color=(200, 40, 40))  # Đỏ
                        # player2.character = "Isagi"
                        game_state = "PLAYING"
                    elif event.key == pygame.K_2 and player_number == 2:
                        player2.information("Nagi", color=(40, 40, 200))  # Xanh
                        # player2.character = "Nagi"
                        game_state = "PLAYING"
                    elif event.key == pygame.K_3 and player_number == 2:
                        player2.information("Bachira", color=(255, 215, 0))  # Vàng
                        # player2.character = "Bachira"
                        game_state = "PLAYING"
                    elif event.key == pygame.K_4 and player_number == 2:
                        player2.information("Kunigami", color=(128, 0, 128))  # Tím
                        # player2.character = "Kunigami"
                        game_state = "PLAYING"
                    elif event.key == pygame.K_5 and player_number == 2:
                        player2.information("Chigiri", color=(0, 255, 255))  # Cyan
                        # player2.character = "Chigiri"
                        game_state = "PLAYING"
                    elif event.key == pygame.K_6 and player_number == 2:
                        player2.information("Itachi", color=(95, 35, 135))
                        game_state = "PLAYING"
                        _stop_general_music()
                    continue
                elif game_state == "PLAYING" or (game_state == "PLAY_BOT" and player_number == 2):
                    if rewind_active or rewind_freeze_timer > 0:
                        continue
                    if event.key == action_keys["p1_kick"]:
                        if player1.kick(ball):
                            _play_kick_sound()
                    if event.key == action_keys["p2_kick"] and not player2.is_bot:
                        if player2.kick(ball):
                            _play_kick_sound()
                    if event.key == action_keys["p1_skill"]:
                        player1.activate_skill(player2)
                    if event.key == action_keys["p2_skill"] and not player2.is_bot:
                        player2.activate_skill(player1)
                    continue
        if game_state != "PLAYING" and game_state != "PLAY_BOT":
            continue
        if player_number == 1:
            continue
        if game_mode != "REPLAY" and not rewind_active and rewind_freeze_timer <= 0:
            match_time_left -= dt
            if match_time_left <= 0 or score_red >= settings["max_goals"] or score_blue >= settings["max_goals"]:
                game_state = "RESULT"
                # Trao thưởng dựa trên kết quả
                if score_red > score_blue:
                    res = "win"
                elif score_blue > score_red:
                    res = "loss"
                else:
                    res = "draw"
                last_match_reward = profile.award_match(res)
                
                _start_general_music()
                continue
        if game_mode != "REPLAY" and not rewind_active and rewind_freeze_timer <= 0:
            if player1.time_rewind:
                rewind_caster = player1
            elif player2.time_rewind:
                rewind_caster = player2
            else:
                rewind_caster = None

            if rewind_caster is not None:
                rewind_frames = list(rewind_history)
                if not rewind_frames:
                    rewind_frames = [game_snapshot(ball, player1, player2, effects, ball_ok)]
                rewind_index = len(rewind_frames) - 1
                rewind_active = True
                _play_itachi_sound()

        if rewind_active:
            if rewind_index >= 0:
                ball_ok = restore_game_snapshot(
                    rewind_frames[rewind_index], ball, player1, player2, effects
                )
                effects.set_itachi_overlay(True, dt)
                rewind_index -= 1
            else:
                rewind_active = False
                _stop_itachi_sound()
                finish_itachi_rewind(rewind_caster)
                effects.start_itachi_converge(rewind_caster.pos)
                rewind_freeze_timer = ITACHI_FREEZE_SECONDS
                rewind_history.clear()
        elif rewind_freeze_timer > 0:
            rewind_freeze_timer -= dt
            effects.update_freeze_effects(dt)
            if rewind_freeze_timer <= 0:
                rewind_caster = None
                rewind_frames = []
                rewind_history.append(game_snapshot(ball, player1, player2, effects, ball_ok))
        elif game_mode == "REPLAY":
            if not replay_playing:
                replay_frames = replay_buffer.get_frames()
                replay_index = max(0, len(replay_frames) - 300)
                replay_playing = True

            if replay_index < len(replay_frames):
                frame = replay_frames[replay_index]

                ball.pos = frame["ball_pos"].copy()
                ball.vel = frame["ball_vel"].copy()
                player1.pos = frame["p1_pos"].copy()
                player1.vel = frame["p1_vel"].copy()
                player2.pos = frame["p2_pos"].copy()
                player2.vel = frame["p2_vel"].copy()
                effects.set_state(frame.get("effects"))

                replay_index += 1
            else:
                replay_playing = False
                game_mode = ""
                replay_buffer.clear()
                effects.reset()
                ball.reset()
                player1.reset(FIELD_WIDTH // 4, FIELD_HEIGHT // 2, player1.color, controls1)
                player2.reset(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2, player2.color, controls2)
                ball_ok = True
                _stop_goal_sound()
        else:
            # UPDATE
            score_red, score_blue, ball_ok = update_game(
                ball, player1,player2, dt, score_red, score_blue, match_time_left
            )
            effects.update(dt, ball, player1, player2)
            replay_buffer.save(ball, player1, player2, effects)
            rewind_history.append(game_snapshot(ball, player1, player2, effects, ball_ok))
        # RENDER
        draw_scene(screen, ball, ball_ok, player1, player2, score_red, score_blue, font, effects, debug_overlay, match_time_left)


    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
