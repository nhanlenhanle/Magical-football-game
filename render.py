import pygame
from config import *


def draw_scene(screen, ball, ball_ok, player1, player2, score_red, score_blue, font, effects=None, debug_overlay=None):

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
    player1.draw(screen)
    player2.draw(screen)
    if effects is not None:
        effects.draw(screen)
    if debug_overlay is not None:
        debug_overlay.draw(screen, ball, player1, player2)
    pygame.display.flip()
