# =========================
# MARGINS
# =========================

SIDE_MARGIN = 60
TOP_BOTTOM_MARGIN = 40
# =========================
# FIELD & WINDOW
# =========================

FIELD_WIDTH = 800
FIELD_HEIGHT = 400


WINDOW_WIDTH = FIELD_WIDTH + SIDE_MARGIN * 2
WINDOW_HEIGHT = FIELD_HEIGHT + TOP_BOTTOM_MARGIN * 2

OFFSET_X = SIDE_MARGIN
OFFSET_Y = TOP_BOTTOM_MARGIN


# =========================
# COLORS
# =========================

COLOR_GRASS = (113, 140, 90)
COLOR_LINES = (199, 230, 189)
COLOR_BALL = (255, 255, 255)
COLOR_BALL_OUTLINE = (0, 0, 0)
COLOR_SCORE = (255, 255, 255)

COLOR_TEAM_BLUE = (0, 150, 136)
COLOR_TEAM_RED = (200, 40, 40)


# =========================
# PHYSICS
# =========================

KICKOFF_RADIUS = 70
POST_RADIUS = 4

BALL_RADIUS = 8
BALL_MASS = 2.0
BALL_DAMPING = 0.988
BALL_MAX_SPEED = 1000


RESTITUTION = 0.5
RESTITUTION_BALL_AND_PLAYER = 0.1

# =========================
# GOAL
# =========================

GOAL_HEIGHT = 146
GOAL_TOP = FIELD_HEIGHT // 2 - GOAL_HEIGHT // 2
GOAL_BOTTOM = FIELD_HEIGHT // 2 + GOAL_HEIGHT // 2
GOAL_DEPTH = 40

# =========================
# PLAYER
# =========================

PLAYER_RADIUS = 15

PLAYER_ACCELERATION = 350
PLAYER_MAX_SPEED = 170
PLAYER_DAMPING = 0.95

PLAYER_MASS = 4.0
# =========================
# KICK
# =========================
KICK_FORCE = 400
KICK_COOLDOWN = 0.1  # giây
KICK_RANGE = 6       # khoảng cách thêm ngoài radius
