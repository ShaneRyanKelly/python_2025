import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Paddle properties
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 90
player_speed = 5

# Ball properties
BALL_SIZE = 15
ball_speed_x = 5
ball_speed_y = 5

# Initial positions
player = pygame.Rect(WIDTH - 20 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, 
                    PADDLE_WIDTH, PADDLE_HEIGHT)
opponent = pygame.Rect(20, HEIGHT // 2 - PADDLE_HEIGHT // 2, 
                     PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2, 
                  BALL_SIZE, BALL_SIZE)

# Ball velocity
ball_dx = ball_speed_x * random.choice((1, -1))
ball_dy = ball_speed_y * random.choice((1, -1))

# Score
player_score = 0
opponent_score = 0
font = pygame.font.Font(None, 36)

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Player movement (arrow keys)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] and player.top > 0:
        player.y -= player_speed
    if keys[pygame.K_DOWN] and player.bottom < HEIGHT:
        player.y += player_speed

    # Opponent movement (W and S keys)
    if keys[pygame.K_w] and opponent.top > 0:
        opponent.y -= player_speed
    if keys[pygame.K_s] and opponent.bottom < HEIGHT:
        opponent.y += player_speed

    # Ball movement
    ball.x += ball_dx
    ball.y += ball_dy

    # Ball collision with top and bottom
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        ball_dy *= -1

    # Ball collision with paddles
    if ball.colliderect(player) or ball.colliderect(opponent):
        ball_dx *= -1

    # Scoring
    if ball.left <= 0:
        player_score += 1
        ball.center = (WIDTH // 2, HEIGHT // 2)
        ball_dx = ball_speed_x * random.choice((1, -1))
        ball_dy = ball_speed_y * random.choice((1, -1))
        
    if ball.right >= WIDTH:
        opponent_score += 1
        ball.center = (WIDTH // 2, HEIGHT // 2)
        ball_dx = ball_speed_x * random.choice((1, -1))
        ball_dy = ball_speed_y * random.choice((1, -1))

    # Drawing
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, player)
    pygame.draw.rect(screen, WHITE, opponent)
    pygame.draw.ellipse(screen, WHITE, ball)
    pygame.draw.aaline(screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))

    # Draw score
    player_text = font.render(str(player_score), False, WHITE)
    opponent_text = font.render(str(opponent_score), False, WHITE)
    screen.blit(opponent_text, (WIDTH // 4, 20))
    screen.blit(player_text, (3 * WIDTH // 4, 20))

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()