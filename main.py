import pygame
import sys
import asyncio
from config import *
from ball import Ball
from debug import DebugOverlay
from effect import SkillEffectManager
from render import draw_scene
from player import Player
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

def update_game(ball, player1, player2, dt, score_red, score_blue):
    keys = pygame.key.get_pressed()
    player1.handle_input(keys, dt)
    if player2.is_bot:
        player2.bot_update(player1, ball, dt)
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
    player1.handle_ball_collision(ball)
    player2.handle_ball_collision(ball)

    goal = ball.handle_wall_collision()

    if goal == "RED_GOAL":
        score_red += 1
        ball.reset()
        player1.reset(FIELD_WIDTH // 4, FIELD_HEIGHT // 2, player1.color, controls1)
        player2.reset(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2, player2.color, controls2)

    elif goal == "BLUE_GOAL":
        score_blue += 1
        ball.reset()
        player1.reset(FIELD_WIDTH // 4, FIELD_HEIGHT // 2, player1.color, controls1)
        player2.reset(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2, player2.color, controls2)
    return score_red, score_blue, ball_ok
#------------------------ Vẽ giao diện mở đầu------------------------
def draw_menu(screen, font):
    screen.fill((30, 30, 30))

    title = font.render("MAGICAL FOOTBALL GAME", True, (255, 255, 255))
    bot = font.render("1 - Play vs Bot", True, (200, 200, 200))
    pvp = font.render("2 - Play PvP", True, (200, 200, 200))

    screen.blit(title, (250, 100))
    screen.blit(bot, (250, 200))
    screen.blit(pvp, (250, 260))

    pygame.display.flip()
def draw_character_select(screen, font, player_number):
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
    
    screen.blit(text, (250, 100))
    screen.blit(isagi, (250, 200))
    screen.blit(nagi, (250, 250))
    screen.blit(bachira, (250, 300))
    screen.blit(kunigami, (250, 350))
    screen.blit(chigiri, (250, 400))

    pygame.display.flip()
async def main():
    game_state = "MENU"  # MENU / PLAY_BOT / PLAY_PVP
    pygame.init()

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
    running = True 
    while running:            
        await asyncio.sleep(0)
        dt = clock.tick(60) / 1000.0
        if game_state == "MENU":
            draw_menu(screen, font)
        elif game_state == "PLAY_PVP":
            draw_character_select(screen, font, player_number)
        elif game_state == "PLAY_BOT":
            player2.is_bot = True
            if (player_number == 1):
                draw_character_select(screen, font, player_number)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if debug_overlay.handle_event(event):
                    continue
                if game_state == "MENU":
                    if event.key == pygame.K_1:
                        game_state = "PLAY_BOT"
                    elif event.key == pygame.K_2:
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
                    continue
                elif game_state == "PLAYING" or (game_state == "PLAY_BOT" and player_number == 2):
                    if event.key == pygame.K_SPACE:
                        player1.kick(ball)
                    if event.key == pygame.K_RETURN:
                        player2.kick(ball)
                    if event.key == pygame.K_q:
                        player1.activate_skill(player2)
                    if event.key == pygame.K_RSHIFT:
                        player2.activate_skill(player1)
                    continue
        if game_state != "PLAYING" and game_state != "PLAY_BOT":
            continue
        if player_number == 1:
            continue
        # UPDATE
        score_red, score_blue, ball_ok = update_game(
            ball, player1,player2, dt, score_red, score_blue
        )
        effects.update(dt, ball, player1, player2)

        # RENDER
        draw_scene(screen, ball, ball_ok, player1, player2, score_red, score_blue, font, effects, debug_overlay)


    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
