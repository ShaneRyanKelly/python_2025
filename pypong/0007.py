import pygame
import random
import math
from collections import deque

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong with Spin, Stamina, Trail, and Slam")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
TRAIL_COLOR = (150, 150, 150)

# Paddle properties
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 90
BASE_SPEED = 5
BOOST_SPEED = 8
STAMINA_MAX = 100
STAMINA_DRAIN = 0.5
STAMINA_REGEN = 0.2

# Ball properties
BALL_SIZE = 15
BASE_SPEED_X = 5
BASE_SPEED_Y = 5
MAX_SPIN = 0.3
SPIN_VELOCITY_FACTOR = 0.05
TRAIL_LENGTH = 5
SLAM_SPEED_X = 15
SLAM_DURATION = 60  # Initial slam boost duration
DECELERATION_RATE = 0.95  # Slowdown factor per frame after slam

# Initial positions
player = pygame.Rect(WIDTH - 20 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, 
                    PADDLE_WIDTH, PADDLE_HEIGHT)
opponent = pygame.Rect(20, HEIGHT // 2 - PADDLE_HEIGHT // 2, 
                     PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2, 
                  BALL_SIZE, BALL_SIZE)

# Ball movement variables
ball_dx = BASE_SPEED_X * random.choice((1, -1))
ball_dy = BASE_SPEED_Y * random.choice((1, -1))
spin = 0
ball_trail = deque(maxlen=TRAIL_LENGTH)
slam_timer = 0
is_slam_active = False  # Track if we're in slam or deceleration phase

# Paddle variables
player_vel = 0
opponent_vel = 0
player_stamina = STAMINA_MAX
opponent_stamina = STAMINA_MAX

# Score
player_score = 0
opponent_score = 0
font = pygame.font.Font(None, 36)

def calculate_spin(paddle, ball, paddle_velocity):
    """Calculate spin based on hit position and paddle velocity"""
    relative_hit_pos = (ball.centery - paddle.centery) / (PADDLE_HEIGHT / 2)
    position_spin = relative_hit_pos * MAX_SPIN
    velocity_spin = paddle_velocity * SPIN_VELOCITY_FACTOR
    total_spin = position_spin + velocity_spin
    return max(min(total_spin, MAX_SPIN), -MAX_SPIN)

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Player movement (arrow keys + right shift, right ctrl to slam)
    keys = pygame.key.get_pressed()
    player_vel = 0
    player_speed = BASE_SPEED
    boosting_player = keys[pygame.K_RSHIFT] and player_stamina > 0
    slamming_player = keys[pygame.K_RCTRL] and player_stamina >= STAMINA_MAX
    
    if boosting_player:
        player_speed = BOOST_SPEED
        player_stamina -= STAMINA_DRAIN
    else:
        player_stamina = min(player_stamina + STAMINA_REGEN, STAMINA_MAX)

    if keys[pygame.K_UP] and player.top > 0:
        player.y -= player_speed
        player_vel = -player_speed
    if keys[pygame.K_DOWN] and player.bottom < HEIGHT:
        player.y += player_speed
        player_vel = player_speed

    # Opponent movement (W/S + left shift, left ctrl to slam)
    opponent_vel = 0
    opponent_speed = BASE_SPEED
    boosting_opponent = keys[pygame.K_LSHIFT] and opponent_stamina > 0
    slamming_opponent = keys[pygame.K_LCTRL] and opponent_stamina >= STAMINA_MAX
    
    if boosting_opponent:
        opponent_speed = BOOST_SPEED
        opponent_stamina -= STAMINA_DRAIN
    else:
        opponent_stamina = min(opponent_stamina + STAMINA_REGEN, STAMINA_MAX)

    if keys[pygame.K_w] and opponent.top > 0:
        opponent.y -= opponent_speed
        opponent_vel = -opponent_speed
    if keys[pygame.K_s] and opponent.bottom < HEIGHT:
        opponent.y += opponent_speed
        opponent_vel = opponent_speed

    # Ball movement with spin and trail
    ball_trail.append((ball.centerx, ball.centery))
    ball_dy += spin
    ball.x += ball_dx
    ball.y += ball_dy

    # Slam and deceleration management
    if slam_timer > 0:
        slam_timer -= 1
        if slam_timer == 0:
            is_slam_active = False  # End initial slam phase, start deceleration
    elif not is_slam_active and abs(ball_dx) > BASE_SPEED_X:
        ball_dx *= DECELERATION_RATE  # Gradually slow down
        if abs(ball_dx) <= BASE_SPEED_X:
            ball_dx = BASE_SPEED_X * (1 if ball_dx > 0 else -1)  # Clamp to base speed

    # Ball collision with top and bottom
    if ball.top <= 0:
        ball_dy = abs(ball_dy)
        spin *= 0.8
    if ball.bottom >= HEIGHT:
        ball_dy = -abs(ball_dy)
        spin *= 0.8

    # Ball collision with paddles
    if ball.colliderect(player):
        ball_dx = -abs(ball_dx)
        spin = calculate_spin(player, ball, player_vel)
        if slamming_player and slam_timer == 0:
            ball_dx = -SLAM_SPEED_X
            slam_timer = SLAM_DURATION
            is_slam_active = True
            player_stamina = 0
    elif ball.colliderect(opponent):
        ball_dx = abs(ball_dx)
        spin = calculate_spin(opponent, ball, opponent_vel)
        if slamming_opponent and slam_timer == 0:
            ball_dx = SLAM_SPEED_X
            slam_timer = SLAM_DURATION
            is_slam_active = True
            opponent_stamina = 0

    # Scoring
    if ball.left <= 0:
        player_score += 1
        ball.center = (WIDTH // 2, HEIGHT // 2)
        ball_dx = BASE_SPEED_X * random.choice((1, -1))
        ball_dy = BASE_SPEED_Y * random.choice((1, -1))
        spin = 0
        ball_trail.clear()
        slam_timer = 0
        is_slam_active = False
        
    if ball.right >= WIDTH:
        opponent_score += 1
        ball.center = (WIDTH // 2, HEIGHT // 2)
        ball_dx = BASE_SPEED_X * random.choice((1, -1))
        ball_dy = BASE_SPEED_Y * random.choice((1, -1))
        spin = 0
        ball_trail.clear()
        slam_timer = 0
        is_slam_active = False

    # Drawing
    screen.fill(BLACK)
    
    # Draw ball trail
    for i, pos in enumerate(ball_trail):
        alpha = (i + 1) / TRAIL_LENGTH
        size = BALL_SIZE * (0.8 ** (TRAIL_LENGTH - i))
        pygame.draw.ellipse(screen, TRAIL_COLOR, 
                          (pos[0] - size/2, pos[1] - size/2, size, size))

    pygame.draw.rect(screen, WHITE, player)
    pygame.draw.rect(screen, WHITE, opponent)
    pygame.draw.ellipse(screen, WHITE, ball)
    pygame.draw.aaline(screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))

    # Draw stamina bars at bottom, further from paddles
    STAMINA_BAR_WIDTH = 100
    STAMINA_BAR_HEIGHT = 10
    STAMINA_OFFSET = 50
    player_stamina_bar = pygame.Rect(WIDTH - STAMINA_BAR_WIDTH - STAMINA_OFFSET, HEIGHT - 30, 
                                   STAMINA_BAR_WIDTH, STAMINA_BAR_HEIGHT)
    opponent_stamina_bar = pygame.Rect(STAMINA_OFFSET, HEIGHT - 30, 
                                     STAMINA_BAR_WIDTH, STAMINA_BAR_HEIGHT)
    
    pygame.draw.rect(screen, RED, player_stamina_bar)
    pygame.draw.rect(screen, RED, opponent_stamina_bar)
    pygame.draw.rect(screen, GREEN, (WIDTH - STAMINA_BAR_WIDTH - STAMINA_OFFSET, HEIGHT - 30, 
                                   player_stamina, STAMINA_BAR_HEIGHT))
    pygame.draw.rect(screen, GREEN, (STAMINA_OFFSET, HEIGHT - 30, 
                                   opponent_stamina, STAMINA_BAR_HEIGHT))

    # Draw score
    player_text = font.render(str(player_score), False, WHITE)
    opponent_text = font.render(str(opponent_score), False, WHITE)
    screen.blit(opponent_text, (WIDTH // 4, 20))
    screen.blit(player_text, (3 * WIDTH // 4, 20))

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()