import pygame
import sys

from config import *
from ball import Ball
from render import draw_scene
from player import Player
def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
    return True


def update_game(ball, player, dt, score_red, score_blue):
    keys = pygame.key.get_pressed()
    player.handle_input(keys, dt)
    player.update(dt)
    player.handle_wall_collision()
   # ball.apply_input(keys, dt)
    ball.update(dt)
    ball.handle_post_collision()

    player.handle_ball_collision(ball)

    if keys[pygame.K_SPACE]:
        player.kick(ball)

    goal = ball.handle_wall_collision()

    if goal == "RED_GOAL":
        score_red += 1
        ball.reset()
        # player1.reset()
        # player2.reset()

    elif goal == "BLUE_GOAL":
        score_blue += 1
        ball.reset()
        # player1.reset()
        # player2.reset()
    return score_red, score_blue

def draw_menu(screen, font):
    screen.fill((30, 30, 30))

    title = font.render("MAGICAL FOOTBALL GAME", True, (255, 255, 255))
    bot = font.render("1 - Play vs Bot", True, (200, 200, 200))
    pvp = font.render("2 - Play PvP", True, (200, 200, 200))

    screen.blit(title, (250, 100))
    screen.blit(bot, (250, 200))
    screen.blit(pvp, (250, 260))

    pygame.display.flip()
def main():
    game_state = "MENU"  # MENU / PLAY_BOT / PLAY_PVP
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Haxball Solo Environment")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 40)

    # Game state
    ball = Ball()
    player1 = Player(FIELD_WIDTH // 4, FIELD_HEIGHT // 2, COLOR_TEAM_BLUE)
    player2 = Player(FIELD_WIDTH * 3 // 4, FIELD_HEIGHT // 2, COLOR_TEAM_RED)
    score_red = 0
    score_blue = 0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        running = handle_events()
        keys = pygame.key.get_pressed()
        if game_state == "MENU":
            if keys[pygame.K_1]:
                game_state = "PLAY_BOT"
            if keys[pygame.K_2]:
                game_state = "PLAY_PVP"
        if game_state == "MENU":
            draw_menu(screen, font)
            continue
        # UPDATE
        score_red, score_blue = update_game(
            ball, player, dt, score_red, score_blue
        )

        # RENDER
        draw_scene(screen, ball, player1, player2, score_red, score_blue, font)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()