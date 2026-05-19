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
from render import draw_character_select, draw_home, draw_menu, draw_result, draw_scene, draw_settings, draw_upgrade
from player import Player
from profile import PlayerProfile
from team_bot import AttackBot, DefBot, NormalBot
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


def choose_character(player, player_number, character_index):
    """Gán nhân vật cho cầu thủ dựa trên index đã chọn."""
    name, color = CHARACTERS[character_index]
    player.information(name, color=color)
    return player_number + 1


def reset_match(ball, player1, player2, effects, player3=None):
    """Đặt lại trạng thái bóng, cầu thủ và hiệu ứng để bắt đầu hiệp mới hoặc trận mới."""
    global game_mode

    game_mode = ""
    replay_buffer.clear()
    effects.reset()
    ball.reset()
    player1.reset(FIELD_WIDTH // 4, FIELD_HEIGHT // 2, player1.color, controls1)
    player2.reset(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2, player2.color, controls2)
    if player3 is not None:
        player3.reset(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2 - 80, player3.color, controls2)


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


def game_snapshot(ball, player1, player2, effects, ball_ok, score_red, score_blue, match_time_left, player3=None):
    """Chụp toàn bộ trạng thái trận đấu cho kỹ năng quay ngược của Itachi."""
    snapshot = {
        "ball_pos": ball.pos.copy(),
        "ball_vel": ball.vel.copy(),
        "p1": player_state(player1),
        "p2": player_state(player2),
        "effects": effects.get_state(),
        "ball_ok": ball_ok,
        "score_red": score_red,
        "score_blue": score_blue,
        "match_time_left": match_time_left,
        "goal_log": [entry.copy() for entry in goal_log],
        "last_toucher": last_toucher,
    }
    if player3 is not None:
        snapshot["p3"] = player_state(player3)
    return snapshot


def restore_game_snapshot(snapshot, ball, player1, player2, effects, player3=None):
    """Khôi phục bóng, cầu thủ, hiệu ứng và trạng thái hiển thị bóng từ snapshot."""
    global last_toucher

    ball.pos = snapshot["ball_pos"].copy()
    ball.vel = snapshot["ball_vel"].copy()
    restore_player_state(player1, snapshot["p1"])
    restore_player_state(player2, snapshot["p2"])
    if player3 is not None and "p3" in snapshot:
        restore_player_state(player3, snapshot["p3"])
    effects.set_state(snapshot["effects"])
    goal_log[:] = [entry.copy() for entry in snapshot.get("goal_log", [])]
    last_toucher = snapshot.get("last_toucher")
    return (
        snapshot["ball_ok"],
        snapshot.get("score_red", 0),
        snapshot.get("score_blue", 0),
        snapshot.get("match_time_left", 0),
    )


def finish_itachi_rewind(caster):
    """Kết thúc rewind của Itachi và đặt hồi chiêu cho người dùng kỹ năng."""
    caster.skill_active = False
    caster.skill_timer = 0
    caster.skill_cooldown = 15.0
    caster.time_rewind = False
    caster.rewind_timer = 0


def update_game(ball, player1, player2, dt, score_red, score_blue, match_time_left, extra_players=None):
    """Cập nhật một frame gameplay thật và trả về điểm số cùng trạng thái bóng."""
    global game_mode, last_toucher
    extra_players = extra_players or []
    active_players = [player1, player2] + extra_players
    keys = pygame.key.get_pressed()
    player1.handle_input(keys, dt)
    if player2.is_bot:
        if player2.bot_update(player1, ball, dt):
            _play_kick_sound()
    else:
        player2.handle_input(keys, dt)
    for bot in extra_players:
        if bot.is_bot and bot.bot_update(player1, ball, dt):
            _play_kick_sound()

    player1.update(player2, dt, ball)
    for player in active_players[1:]:
        player.update(player1, dt, ball)

    ball_ok = all(player.ball_ok for player in active_players)
    for i, player in enumerate(active_players):
        for other in active_players[i + 1:]:
            player.handle_player_collision(other)
    for player in active_players:
        player.handle_wall_collision()
   # ball.apply_input(keys, dt)
    ball.update(active_players, dt)
    ball.handle_post_collision()
    for index, player in enumerate(active_players):
        if player.handle_ball_collision(ball):
            last_toucher = 1 if index == 0 else 2

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
async def main():
    """Chạy vòng lặp pygame gồm menu, gameplay, replay và rewind."""
    global game_mode, upgrade_tab, last_match_reward, last_toucher
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
    player3 = Player(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2 - 80, COLOR_TEAM_BLUE, controls2)
    bot_team = {"attack": None, "def": None}

    def configure_bot_system():
        """Cấu hình hệ thống bot dựa trên level của người chơi (1 bot hoặc 2 bot)."""
        if profile.level >= 10:
            bot_team["attack"] = AttackBot(player3)
            bot_team["def"] = DefBot(player2, bot_team["attack"])
            player3.bot_ai = bot_team["attack"]
            player2.bot_ai = bot_team["def"]
            player2.is_bot = True
            player3.is_bot = True
        else:
            bot_team["attack"] = None
            bot_team["def"] = None
            player2.bot_ai = NormalBot(player2)
            player3.bot_ai = None
            player3.is_bot = False

    def disable_bot_system():
        """Tắt hoàn toàn hệ thống AI cho các cầu thủ bot."""
        bot_team["attack"] = None
        bot_team["def"] = None
        player2.bot_ai = None
        player3.bot_ai = None
        player3.is_bot = False

    def extra_bot_players():
        """Trả về danh sách cầu thủ bot bổ sung nếu đang ở chế độ đấu với bot level cao."""
        if game_state in ("PLAY_BOT", "PLAYING") and player2.is_bot and profile.level >= 10:
            return [player3]
        return []

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
            draw_home(screen, font, ui_buttons)
        elif game_state == "MENU":
            draw_menu(screen, font, ui_buttons, BACK_BUTTON_RECT)
        elif game_state == "SETTINGS":
            draw_settings(screen, font, ui_buttons, settings, action_keys, waiting_for_key, BACK_BUTTON_RECT)
        elif game_state == "UPGRADE":
            draw_upgrade(screen, font, ui_buttons, profile, upgrade_tab, BACK_BUTTON_RECT)
        elif game_state == "RESULT":
            draw_result(screen, font, ui_buttons, score_red, score_blue, goal_log, last_match_reward, profile)
        elif game_state == "PLAY_PVP":
            draw_character_select(screen, font, ui_buttons, player_number, CHARACTERS, BACK_BUTTON_RECT)
        elif game_state == "PLAY_BOT":
            player2.is_bot = True
            if (player_number == 1):
                draw_character_select(screen, font, ui_buttons, player_number, CHARACTERS, BACK_BUTTON_RECT)

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
                            reset_match(ball, player1, player2, effects, player3)
                            player_number = 1
                            player2.is_bot = False
                            disable_bot_system()
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
                        disable_bot_system()
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
                    reset_match(ball, player1, player2, effects, player3)
                    player_number = 1
                    player2.is_bot = False
                    disable_bot_system()
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
                    reset_match(ball, player1, player2, effects, player3)
                    score_red = 0
                    score_blue = 0
                    match_time_left = settings["match_minutes"] * 60
                    goal_log.clear()
                    last_toucher = None
                    player_number = 1
                    player2.is_bot = True
                    configure_bot_system()
                    game_state = "PLAY_BOT"
                    _apply_volume()
                    continue
                if clicked == "mode_pvp":
                    reset_match(ball, player1, player2, effects, player3)
                    score_red = 0
                    score_blue = 0
                    match_time_left = settings["match_minutes"] * 60
                    goal_log.clear()
                    last_toucher = None
                    player_number = 1
                    player2.is_bot = False
                    disable_bot_system()
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
                        disable_bot_system()
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
                        reset_match(ball, player1, player2, effects, player3)
                        score_red = 0
                        score_blue = 0
                        match_time_left = settings["match_minutes"] * 60
                        player_number = 1
                        player2.is_bot = True
                        configure_bot_system()
                        game_state = "PLAY_BOT"
                    elif event.key == pygame.K_2:
                        reset_match(ball, player1, player2, effects, player3)
                        score_red = 0
                        score_blue = 0
                        match_time_left = settings["match_minutes"] * 60
                        player_number = 1
                        player2.is_bot = False
                        disable_bot_system()
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
        active_extra_players = extra_bot_players()
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
            elif active_extra_players and player3.time_rewind:
                rewind_caster = player3
            else:
                rewind_caster = None

            if rewind_caster is not None:
                rewind_frames = list(rewind_history)
                if not rewind_frames:
                    rewind_frames = [
                        game_snapshot(
                            ball, player1, player2, effects, ball_ok,
                            score_red, score_blue, match_time_left,
                            player3 if active_extra_players else None
                        )
                    ]
                rewind_index = len(rewind_frames) - 1
                rewind_active = True
                _play_itachi_sound()

        if rewind_active:
            if rewind_index >= 0:
                ball_ok, score_red, score_blue, match_time_left = restore_game_snapshot(
                    rewind_frames[rewind_index], ball, player1, player2, effects, player3 if active_extra_players else None
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
                rewind_history.append(
                    game_snapshot(
                        ball, player1, player2, effects, ball_ok,
                        score_red, score_blue, match_time_left,
                        player3 if active_extra_players else None
                    )
                )
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
                if active_extra_players and "p3_pos" in frame:
                    player3.pos = frame["p3_pos"].copy()
                    player3.vel = frame["p3_vel"].copy()
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
                if active_extra_players:
                    player3.reset(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2 - 80, player3.color, controls2)
                    configure_bot_system()
                ball_ok = True
                _stop_goal_sound()
        else:
            # UPDATE
            score_red, score_blue, ball_ok = update_game(
                ball, player1, player2, dt, score_red, score_blue, match_time_left, active_extra_players
            )
            effects.update(dt, ball, player1, player2, *active_extra_players)
            replay_buffer.save(ball, player1, player2, effects, player3 if active_extra_players else None)
            rewind_history.append(
                game_snapshot(
                    ball, player1, player2, effects, ball_ok,
                    score_red, score_blue, match_time_left,
                    player3 if active_extra_players else None
                )
            )
        # RENDER
        draw_scene(screen, ball, ball_ok, player1, player2, score_red, score_blue, font, effects, debug_overlay, match_time_left, active_extra_players)


    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
