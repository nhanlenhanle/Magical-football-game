import pygame
from config import *
from profile import UPGRADE_DEFS


_menu_logo = None
_menu_logo_failed = False


def get_menu_logo():
    """Tải và scale logo cho menu chính, cache lại để dùng sau."""
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


def draw_button(screen, font, ui_buttons, button_id, text, rect, base_color=(92, 134, 96), hover_color=(118, 165, 107), text_color=(245, 250, 238)):
    """Vẽ một nút bấm có hiệu ứng hover và lưu rect vào ui_buttons để xử lý click."""
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


def draw_back_button(screen, font, ui_buttons, back_button_rect):
    """Vẽ nút 'Back' mặc định dùng trong các menu con."""
    draw_button(
        screen,
        font,
        ui_buttons,
        "back",
        "Back",
        back_button_rect,
        base_color=(185, 45, 45),
        hover_color=(225, 70, 65),
    )


def draw_small_button(screen, font, ui_buttons, button_id, text, rect):
    """Vẽ một nút bấm kích thước nhỏ, thường dùng cho việc tăng/giảm thông số."""
    draw_button(
        screen,
        font,
        ui_buttons,
        button_id,
        text,
        rect,
        base_color=(68, 105, 74),
        hover_color=(105, 150, 86),
    )


def draw_label(screen, font, text, center_x, center_y, color=(245, 250, 238)):
    """Vẽ một dòng văn bản căn giữa tại tọa độ cho trước."""
    label = font.render(text, True, color)
    screen.blit(
        label,
        (
            center_x - label.get_width() // 2,
            center_y - label.get_height() // 2,
        ),
    )


def format_key(key):
    """Chuyển đổi mã phím Pygame thành tên phím viết hoa để hiển thị."""
    return pygame.key.name(key).upper()


def draw_home(screen, font, ui_buttons):
    """Vẽ màn hình trang chủ (Home) với logo và các nút chức năng chính."""
    ui_buttons.clear()
    screen.fill((73, 111, 82))

    logo = get_menu_logo()
    if logo is not None:
        logo_x = WINDOW_WIDTH // 2 - logo.get_width() // 2
        screen.blit(logo, (logo_x, 25))

    button_w = 320
    button_h = 55
    start_y = 250
    draw_button(screen, font, ui_buttons, "home_play", "Vao game", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, start_y, button_w, button_h))
    draw_button(screen, font, ui_buttons, "home_settings", "Setting", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, start_y + 72, button_w, button_h))
    draw_button(screen, font, ui_buttons, "home_upgrade", "Nang cap", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, start_y + 144, button_w, button_h))
    pygame.display.flip()


def draw_menu(screen, font, ui_buttons, back_button_rect):
    """Vẽ màn hình chọn chế độ chơi (PvB hoặc PvP)."""
    ui_buttons.clear()
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
    draw_button(screen, font, ui_buttons, "mode_bot", "Play vs Bot", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, options_y, button_w, button_h))
    draw_button(screen, font, ui_buttons, "mode_pvp", "Play PvP", pygame.Rect(WINDOW_WIDTH // 2 - button_w // 2, options_y + 76, button_w, button_h))
    draw_back_button(screen, font, ui_buttons, back_button_rect)

    pygame.display.flip()


def draw_settings(screen, font, ui_buttons, settings, action_keys, waiting_for_key, back_button_rect):
    """Vẽ màn hình cài đặt âm lượng, thời gian và cấu hình phím điều khiển."""
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
        draw_small_button(screen, value_font, ui_buttons, f"{key}_down", "-", pygame.Rect(x + 205, y, 48, 48))
        draw_label(screen, value_font, value, x + 310, y + 24)
        draw_small_button(screen, value_font, ui_buttons, f"{key}_up", "+", pygame.Rect(x + 370, y, 48, 48))

    for key, label_text, value, x, y in key_rows:
        draw_label(screen, small_font, label_text, x + 75, y + 25)
        color = (255, 235, 120) if waiting_for_key == key else (245, 250, 238)
        draw_button(
            screen,
            value_font,
            ui_buttons,
            f"key_{key}",
            value,
            pygame.Rect(x + 155, y, 215, 48),
            text_color=color,
        )
    draw_back_button(screen, font, ui_buttons, back_button_rect)
    pygame.display.flip()


def draw_upgrade(screen, font, ui_buttons, profile, upgrade_tab, back_button_rect):
    """Vẽ giao diện nâng cấp chỉ số nhân vật với hệ thống tab và các thẻ nâng cấp."""
    ui_buttons.clear()

    W, H = WINDOW_WIDTH, WINDOW_HEIGHT
    screen.fill((16, 18, 26))

    lv_font = pygame.font.SysFont("Arial", 30, bold=True)
    pf_font = pygame.font.SysFont("Arial", 20, bold=True)
    sm_font = pygame.font.SysFont("Arial", 17)
    card_name = pygame.font.SysFont("Arial", 19, bold=True)
    card_desc = pygame.font.SysFont("Arial", 15)
    card_cost = pygame.font.SysFont("Arial", 16, bold=True)

    bar_h = 64
    pygame.draw.rect(screen, (24, 28, 42), pygame.Rect(0, 0, W, bar_h))
    pygame.draw.line(screen, (50, 60, 88), (0, bar_h), (W, bar_h), 1)

    lv_surf = lv_font.render(f"Lv.{profile.level}", True, (255, 215, 0))
    screen.blit(lv_surf, (18, bar_h // 2 - lv_surf.get_height() // 2))

    xp_bx, xp_by, xp_bw, xp_bh2 = 100, 16, 260, 12
    xp_ratio = min(profile.xp / max(profile.xp_to_next(), 1), 1.0)
    pygame.draw.rect(screen, (38, 42, 60), pygame.Rect(xp_bx, xp_by, xp_bw, xp_bh2), border_radius=6)
    if xp_ratio > 0:
        pygame.draw.rect(screen, (70, 150, 255), pygame.Rect(xp_bx, xp_by, int(xp_bw * xp_ratio), xp_bh2), border_radius=6)
    xp_lbl = sm_font.render(f"XP  {profile.xp} / {profile.xp_to_next()}", True, (140, 170, 220))
    screen.blit(xp_lbl, (xp_bx, xp_by + xp_bh2 + 4))

    coin_surf = pf_font.render(f"Coins: {profile.coins}", True, (255, 200, 50))
    screen.blit(coin_surf, (400, bar_h // 2 - coin_surf.get_height() // 2))

    title_surf = lv_font.render("NANG CAP", True, (200, 210, 255))
    screen.blit(title_surf, (W - title_surf.get_width() - 18, bar_h // 2 - title_surf.get_height() // 2))

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

        if is_maxed:
            bg_col, bd_col = (22, 42, 28), (50, 180, 70)
        elif can_buy:
            bg_col, bd_col = (22, 28, 48), (70, 130, 255)
        else:
            bg_col, bd_col = (20, 22, 32), (44, 48, 68)

        card_rect = pygame.Rect(cx2, cy2, card_w, card_h2)
        pygame.draw.rect(screen, bg_col, card_rect, border_radius=10)
        pygame.draw.rect(screen, bd_col, card_rect, 2, border_radius=10)

        nm = card_name.render(udef["name"], True, (225, 230, 255))
        lv_c = (60, 200, 80) if is_maxed else (255, 210, 0)
        lv_s = card_name.render(f"Lv.{lvl}/{max_lvl}", True, lv_c)
        screen.blit(nm, (cx2 + 12, cy2 + 9))
        screen.blit(lv_s, (cx2 + card_w - lv_s.get_width() - 12, cy2 + 9))

        pb_x, pb_y2, pb_w, pb_h3 = cx2 + 12, cy2 + 34, card_w - 24, 10
        pygame.draw.rect(screen, (30, 34, 50), pygame.Rect(pb_x, pb_y2, pb_w, pb_h3), border_radius=5)
        if lvl > 0:
            fill_w = int(pb_w * lvl / max_lvl)
            fill_c = (50, 200, 75) if is_maxed else (70, 145, 255)
            pygame.draw.rect(screen, fill_c, pygame.Rect(pb_x, pb_y2, fill_w, pb_h3), border_radius=5)
        for t in range(1, max_lvl):
            tx3 = pb_x + int(pb_w * t / max_lvl)
            pygame.draw.line(screen, (16, 18, 26), (tx3, pb_y2), (tx3, pb_y2 + pb_h3), 2)

        bonus_pct = lvl * udef["bonus_per_level"] * 100
        desc_str = udef["desc_template"].format(bonus_pct)
        cap_pct = udef["stat_cap"] * 100
        full_desc = f"{desc_str}  |  cap: {cap_pct:.0f}%"
        ds = card_desc.render(full_desc, True, (140, 160, 200))
        screen.blit(ds, (cx2 + 12, cy2 + 52))

        if is_maxed:
            ms = card_cost.render("MAXED", True, (55, 210, 80))
            screen.blit(ms, (cx2 + card_w - ms.get_width() - 12, cy2 + card_h2 - ms.get_height() - 8))
        else:
            btn_w2, btn_bh = 128, 26
            btn_r = pygame.Rect(cx2 + card_w - btn_w2 - 10, cy2 + card_h2 - btn_bh - 8, btn_w2, btn_bh)
            btn_c = (55, 115, 210) if can_buy else (38, 40, 58)
            pygame.draw.rect(screen, btn_c, btn_r, border_radius=6)
            cost_s = card_cost.render(f"{cost} coins", True, (245, 250, 238) if can_buy else (90, 95, 120))
            screen.blit(cost_s, (btn_r.centerx - cost_s.get_width() // 2, btn_r.centery - cost_s.get_height() // 2))
            ui_buttons[f"upgrade_{key}"] = btn_r

    draw_back_button(screen, font, ui_buttons, back_button_rect)
    pygame.display.flip()


def _format_goal_time(seconds):
    """Định dạng thời gian (giây) thành chuỗi mm:ss."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def draw_result(screen, font, ui_buttons, score_red, score_blue, goal_log, last_match_reward, profile):
    """Vẽ màn hình kết quả sau trận đấu, bao gồm bảng tỉ số, lịch sử ghi bàn và phần thưởng."""
    ui_buttons.clear()
    screen.fill((30, 30, 38))

    big_font = pygame.font.SysFont("Arial", 60, bold=True)
    sub_font = pygame.font.SysFont("Arial", 28)
    small_font = pygame.font.SysFont("Arial", 21)
    rew_font = pygame.font.SysFont("Arial", 19, bold=True)

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

    score_font = pygame.font.SysFont("Arial", 50, bold=True)
    score_str = f"{score_red}  -  {score_blue}"
    score_label = score_font.render(score_str, True, (245, 250, 238))
    screen.blit(score_label, (WINDOW_WIDTH // 2 - score_label.get_width() // 2, 95))

    cx = WINDOW_WIDTH // 2
    p1_label = sub_font.render("Player 1", True, (200, 80, 80))
    p2_label = sub_font.render("Player 2", True, (80, 80, 200))
    p1_col_x = cx - 175
    p2_col_x = cx + 175
    screen.blit(p1_label, (p1_col_x - p1_label.get_width() // 2, 158))
    screen.blit(p2_label, (p2_col_x - p2_label.get_width() // 2, 158))

    pygame.draw.line(screen, (80, 80, 90), (cx - 300, 192), (cx + 300, 192), 1)

    p1_goals = [g for g in goal_log if g["player"] == 1]
    p2_goals = [g for g in goal_log if g["player"] == 2]
    row_y, row_gap = 200, 26
    for i, g in enumerate(p1_goals):
        color = (180, 180, 180) if g["type"] == "G" else (220, 120, 120)
        lbl = small_font.render(f"{_format_goal_time(g['time'])}'  {g['type']}", True, color)
        screen.blit(lbl, (p1_col_x - lbl.get_width() // 2, row_y + i * row_gap))
    for i, g in enumerate(p2_goals):
        color = (180, 180, 180) if g["type"] == "G" else (220, 120, 120)
        lbl = small_font.render(f"{_format_goal_time(g['time'])}'  {g['type']}", True, color)
        screen.blit(lbl, (p2_col_x - lbl.get_width() // 2, row_y + i * row_gap))

    max_rows = max(len(p1_goals), len(p2_goals), 1)
    line_bottom = row_y + max_rows * row_gap + 5
    pygame.draw.line(screen, (60, 60, 70), (cx, 158), (cx, line_bottom), 1)

    panel_y = max(line_bottom + 10, 335)
    if last_match_reward:
        rw = last_match_reward
        panel_w, panel_h = 380, 52
        panel_x = cx - panel_w // 2
        pygame.draw.rect(screen, (28, 32, 48), pygame.Rect(panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(screen, (60, 90, 180), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        xp_str = f"+{rw['xp']} XP"
        coin_str = f"+{rw['coins']} Coins"
        lv_str = "  LEVEL UP!" if rw.get("leveled_up") else f"  Lv.{profile.level}"
        full_str = f"{xp_str}    {coin_str}{lv_str}"
        rs = rew_font.render(full_str, True, (200, 230, 255))
        screen.blit(rs, (cx - rs.get_width() // 2, panel_y + panel_h // 2 - rs.get_height() // 2))
        panel_y += panel_h + 8

    btn_w_single = 240
    btn_h = 50
    gap = 20
    total_btn_w = btn_w_single * 2 + gap
    btn_x_start = cx - total_btn_w // 2
    btn_y = max(panel_y + 4, 390)

    draw_button(screen, font, ui_buttons, "result_home", "Ve Menu", pygame.Rect(btn_x_start, btn_y, btn_w_single, btn_h), base_color=(92, 134, 96), hover_color=(118, 165, 107))
    draw_button(screen, font, ui_buttons, "result_upgrade", "Nang Cap", pygame.Rect(btn_x_start + btn_w_single + gap, btn_y, btn_w_single, btn_h), base_color=(55, 90, 180), hover_color=(80, 130, 230))
    pygame.display.flip()


def draw_character_select(screen, font, ui_buttons, player_number, characters, back_button_rect):
    """Vẽ màn hình chọn nhân vật cho từng người chơi."""
    ui_buttons.clear()
    screen.fill((63, 99, 75) if player_number == 1 else (73, 111, 82))
    text = font.render(f"Player {player_number} Choose Character", True, (255, 255, 255))
    screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 45))
    button_w = 260
    button_h = 56
    gap_x = 35
    gap_y = 24
    start_x = WINDOW_WIDTH // 2 - button_w - gap_x // 2
    start_y = 140
    for index, (name, color) in enumerate(characters):
        col = index % 2
        row = index // 2
        rect = pygame.Rect(start_x + col * (button_w + gap_x), start_y + row * (button_h + gap_y), button_w, button_h)
        draw_button(screen, font, ui_buttons, f"char_{index}", name, rect, base_color=(75, 112, 82), hover_color=color)
    draw_back_button(screen, font, ui_buttons, back_button_rect)

    pygame.display.flip()


def draw_scene(screen, ball, ball_ok, player1, player2, score_red, score_blue, font, effects=None, debug_overlay=None, match_time_left=None, extra_players=None):
    """Vẽ toàn bộ trận đấu gồm sân, cầu thủ, bóng, điểm số, hiệu ứng và debug."""

    # =========================
    # BACKGROUND
    # =========================
    screen.fill((80, 110, 60))  # nền ngoài sân đậm hơn

    # =========================
    # FIELD
    # =========================
    pygame.draw.rect(
        screen,
        COLOR_GRASS,
        (OFFSET_X, OFFSET_Y, FIELD_WIDTH, FIELD_HEIGHT)
    )

    # Middle line
    pygame.draw.line(
        screen,
        COLOR_LINES,
        (OFFSET_X + FIELD_WIDTH // 2, OFFSET_Y),
        (OFFSET_X + FIELD_WIDTH // 2, OFFSET_Y + FIELD_HEIGHT),
        3
    )

    # Kickoff circle
    pygame.draw.circle(
        screen,
        COLOR_LINES,
        (OFFSET_X + FIELD_WIDTH // 2, OFFSET_Y + FIELD_HEIGHT // 2),
        KICKOFF_RADIUS,
        3
    )

    # =========================
    # GOALS
    # =========================

    # Goal lines (front)
    pygame.draw.line(
        screen,
        player1.color,
        (OFFSET_X, OFFSET_Y + GOAL_TOP),
        (OFFSET_X, OFFSET_Y + GOAL_BOTTOM),
        2
    )

    pygame.draw.line(
        screen,
        player2.color,
        (OFFSET_X + FIELD_WIDTH, OFFSET_Y + GOAL_TOP),
        (OFFSET_X + FIELD_WIDTH, OFFSET_Y + GOAL_BOTTOM),
        2
    )
    # =========================
    # Goal frame (3 sides)
    # =========================
    # Right
    pygame.draw.line(screen, COLOR_LINES,
                     (OFFSET_X + FIELD_WIDTH, OFFSET_Y + GOAL_TOP),
                     (OFFSET_X + FIELD_WIDTH + GOAL_DEPTH, OFFSET_Y + GOAL_TOP), 3)

    pygame.draw.line(screen, COLOR_LINES,
                     (OFFSET_X + FIELD_WIDTH, OFFSET_Y + GOAL_BOTTOM),
                     (OFFSET_X + FIELD_WIDTH + GOAL_DEPTH, OFFSET_Y + GOAL_BOTTOM), 3)

    pygame.draw.line(screen, COLOR_LINES,
                     (OFFSET_X + FIELD_WIDTH + GOAL_DEPTH, OFFSET_Y + GOAL_TOP),
                     (OFFSET_X + FIELD_WIDTH + GOAL_DEPTH, OFFSET_Y + GOAL_BOTTOM), 3)

    # Left
    pygame.draw.line(screen, COLOR_LINES,
                     (OFFSET_X, OFFSET_Y + GOAL_TOP),
                     (OFFSET_X - GOAL_DEPTH, OFFSET_Y + GOAL_TOP), 3)

    pygame.draw.line(screen, COLOR_LINES,
                     (OFFSET_X, OFFSET_Y + GOAL_BOTTOM),
                     (OFFSET_X - GOAL_DEPTH, OFFSET_Y + GOAL_BOTTOM), 3)

    pygame.draw.line(screen, COLOR_LINES,
                     (OFFSET_X - GOAL_DEPTH, OFFSET_Y + GOAL_TOP),
                     (OFFSET_X - GOAL_DEPTH, OFFSET_Y + GOAL_BOTTOM), 3)
    # =========================
    # Goal posts
    # =========================

    # Left posts
    pygame.draw.circle(screen, COLOR_LINES,
                    (OFFSET_X, OFFSET_Y + GOAL_TOP),
                    POST_RADIUS)

    pygame.draw.circle(screen, COLOR_LINES,
                    (OFFSET_X, OFFSET_Y + GOAL_BOTTOM),
                    POST_RADIUS)

    # Right posts
    right_x = OFFSET_X + FIELD_WIDTH

    pygame.draw.circle(screen, COLOR_LINES,
                    (right_x, OFFSET_Y + GOAL_TOP),
                    POST_RADIUS)

    pygame.draw.circle(screen, COLOR_LINES,
                    (right_x, OFFSET_Y + GOAL_BOTTOM),
                    POST_RADIUS)

    # =========================
    # BALL
    # =========================
    if ball_ok:
        pygame.draw.circle(
            screen,
            COLOR_BALL,
            (int(ball.pos.x + OFFSET_X),
            int(ball.pos.y + OFFSET_Y)),
            BALL_RADIUS
        )

        pygame.draw.circle(
            screen,
            COLOR_BALL_OUTLINE,
            (int(ball.pos.x + OFFSET_X),
            int(ball.pos.y + OFFSET_Y)),
            BALL_RADIUS,
            2
        )

    # =========================
    # SCORE (simple)
    # =========================
    score_text = font.render(
        f"{score_red}  -  {score_blue}",
        True,
        COLOR_SCORE
    )

    screen.blit(
        score_text,
        (WINDOW_WIDTH // 2 - score_text.get_width() // 2, 20)
    )
    if match_time_left is not None:
        seconds_left = max(0, int(match_time_left))
        time_text = font.render(f"{seconds_left // 60:02d}:{seconds_left % 60:02d}", True, COLOR_SCORE)
        screen.blit(
            time_text,
            (WINDOW_WIDTH // 2 - time_text.get_width() // 2, 58)
        )
    player1.draw(screen)
    player2.draw(screen)
    if extra_players is not None:
        for player in extra_players:
            player.draw(screen)
    if effects is not None:
        effects.draw(screen)
    if debug_overlay is not None:
        debug_overlay.draw(screen, ball, player1, player2)
    pygame.display.flip()
