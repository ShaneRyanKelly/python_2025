import pygame
import random
from collections import deque

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'TRAIL': (150, 150, 150)
}

# Game object properties
PADDLE = {'WIDTH': 15, 'HEIGHT': 90}
BALL = {'SIZE': 15}
SPEEDS = {
    'PADDLE_BASE': 5,
    'PADDLE_BOOST': 8,
    'BALL_BASE_X': 5,
    'BALL_BASE_Y': 5,
    'SLAM_X': 15
}
STAMINA = {'MAX': 100, 'DRAIN': 0.5, 'REGEN': 0.2}
SPIN = {'MAX': 0.3, 'VELOCITY_FACTOR': 0.05}
TRAIL = {'LENGTH': 5}
SLAM = {'DURATION': 60, 'DECELERATION': 0.95}

# Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong with Spin, Stamina, Trail, and Slam")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Game objects
player = pygame.Rect(WIDTH - 20 - PADDLE['WIDTH'], HEIGHT // 2 - PADDLE['HEIGHT'] // 2,
                    PADDLE['WIDTH'], PADDLE['HEIGHT'])
opponent = pygame.Rect(20, HEIGHT // 2 - PADDLE['HEIGHT'] // 2,
                      PADDLE['WIDTH'], PADDLE['HEIGHT'])
ball = pygame.Rect(WIDTH // 2 - BALL['SIZE'] // 2, HEIGHT // 2 - BALL['SIZE'] // 2,
                  BALL['SIZE'], BALL['SIZE'])

# Game state
class GameState:
    def __init__(self):
        self.ball_dx = SPEEDS['BALL_BASE_X'] * random.choice((1, -1))
        self.ball_dy = SPEEDS['BALL_BASE_Y'] * random.choice((1, -1))
        self.spin = 0
        self.ball_trail = deque(maxlen=TRAIL['LENGTH'])
        self.slam_timer = 0
        self.is_slam_active = False
        self.player_vel = 0
        self.opponent_vel = 0
        self.player_stamina = STAMINA['MAX']
        self.opponent_stamina = STAMINA['MAX']
        self.player_score = 0
        self.opponent_score = 0

def calculate_spin(paddle, ball, paddle_velocity):
    """Calculate spin based on hit position and paddle velocity"""
    relative_hit_pos = (ball.centery - paddle.centery) / (PADDLE['HEIGHT'] / 2)
    position_spin = relative_hit_pos * SPIN['MAX']
    velocity_spin = paddle_velocity * SPIN['VELOCITY_FACTOR']
    return max(min(position_spin + velocity_spin, SPIN['MAX']), -SPIN['MAX'])

def move_paddle(paddle, vel, speed, top_limit=0, bottom_limit=HEIGHT):
    """Move paddle with boundary checking"""
    paddle.y += vel
    paddle.clamp_ip((0, top_limit), (WIDTH, bottom_limit))

def reset_ball(state):
    """Reset ball to center with random direction"""
    ball.center = (WIDTH // 2, HEIGHT // 2)
    state.ball_dx = SPEEDS['BALL_BASE_X'] * random.choice((1, -1))
    state.ball_dy = SPEEDS['BALL_BASE_Y'] * random.choice((1, -1))
    state.spin = 0
    state.ball_trail.clear()
    state.slam_timer = 0
    state.is_slam_active = False

def main():
    state = GameState()
    running = True
    
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Input handling
        keys = pygame.key.get_pressed()
        
        # Player controls
        state.player_vel = 0
        player_speed = SPEEDS['PADDLE_BASE']
        boosting_player = keys[pygame.K_RSHIFT] and state.player_stamina > 0
        slamming_player = keys[pygame.K_RCTRL] and state.player_stamina >= STAMINA['MAX']
        
        if boosting_player:
            player_speed = SPEEDS['PADDLE_BOOST']
            state.player_stamina -= STAMINA['DRAIN']
        else:
            state.player_stamina = min(state.player_stamina + STAMINA['REGEN'], STAMINA['MAX'])
            
        if keys[pygame.K_UP]: state.player_vel = -player_speed
        if keys[pygame.K_DOWN]: state.player_vel = player_speed
        move_paddle(player, state.player_vel, player_speed)

        # Opponent controls
        state.opponent_vel = 0
        opponent_speed = SPEEDS['PADDLE_BASE']
        boosting_opponent = keys[pygame.K_LSHIFT] and state.opponent_stamina > 0
        slamming_opponent = keys[pygame.K_LCTRL] and state.opponent_stamina >= STAMINA['MAX']
        
        if boosting_opponent:
            opponent_speed = SPEEDS['PADDLE_BOOST']
            state.opponent_stamina -= STAMINA['DRAIN']
        else:
            state.opponent_stamina = min(state.opponent_stamina + STAMINA['REGEN'], STAMINA['MAX'])
            
        if keys[pygame.K_w]: state.opponent_vel = -opponent_speed
        if keys[pygame.K_s]: state.opponent_vel = opponent_speed
        move_paddle(opponent, state.opponent_vel, opponent_speed)

        # Ball movement
        state.ball_trail.append(ball.center)
        state.ball_dy += state.spin
        ball.move_ip(state.ball_dx, state.ball_dy)

        # Slam and deceleration
        if state.slam_timer > 0:
            state.slam_timer -= 1
            if state.slam_timer == 0:
                state.is_slam_active = False
        elif not state.is_slam_active and abs(state.ball_dx) > SPEEDS['BALL_BASE_X']:
            state.ball_dx *= SLAM['DECELERATION']
            if abs(state.ball_dx) <= SPEEDS['BALL_BASE_X']:
                state.ball_dx = SPEEDS['BALL_BASE_X'] * (1 if state.ball_dx > 0 else -1)

        # Ball collisions
        if ball.top <= 0:
            state.ball_dy = abs(state.ball_dy)
            state.spin *= 0.8
        elif ball.bottom >= HEIGHT:
            state.ball_dy = -abs(state.ball_dy)
            state.spin *= 0.8

        # Paddle collisions
        for paddle, vel, is_player in [(player, state.player_vel, True), 
                                     (opponent, state.opponent_vel, False)]:
            if ball.colliderect(paddle):
                state.ball_dx = -abs(state.ball_dx) if is_player else abs(state.ball_dx)
                state.spin = calculate_spin(paddle, ball, vel)
                slamming = slamming_player if is_player else slamming_opponent
                if slamming and state.slam_timer == 0:
                    state.ball_dx = (-SPEEDS['SLAM_X'] if is_player else SPEEDS['SLAM_X'])
                    state.slam_timer = SLAM['DURATION']
                    state.is_slam_active = True
                    if is_player:
                        state.player_stamina = 0
                    else:
                        state.opponent_stamina = 0

        # Scoring
        if ball.left <= 0:
            state.player_score += 1
            reset_ball(state)
        elif ball.right >= WIDTH:
            state.opponent_score += 1
            reset_ball(state)

        # Rendering
        screen.fill(COLORS['BLACK'])
        
        # Trail
        for i, pos in enumerate(state.ball_trail):
            alpha = (i + 1) / TRAIL['LENGTH']
            size = BALL['SIZE'] * (0.8 ** (TRAIL['LENGTH'] - i))
            pygame.draw.ellipse(screen, COLORS['TRAIL'], 
                              (pos[0] - size/2, pos[1] - size/2, size, size))

        # Game objects
        pygame.draw.rect(screen, COLORS['WHITE'], player)
        pygame.draw.rect(screen, COLORS['WHITE'], opponent)
        pygame.draw.ellipse(screen, COLORS['WHITE'], ball)
        pygame.draw.aaline(screen, COLORS['WHITE'], (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))

        # Stamina bars
        STAMINA_BAR = {'WIDTH': 100, 'HEIGHT': 10, 'OFFSET': 50}
        for bar_x, stamina in [(WIDTH - STAMINA_BAR['WIDTH'] - STAMINA_BAR['OFFSET'], 
                              state.player_stamina),
                              (STAMINA_BAR['OFFSET'], state.opponent_stamina)]:
            pygame.draw.rect(screen, COLORS['RED'], 
                           (bar_x, HEIGHT - 30, STAMINA_BAR['WIDTH'], STAMINA_BAR['HEIGHT']))
            pygame.draw.rect(screen, COLORS['GREEN'], 
                           (bar_x, HEIGHT - 30, stamina, STAMINA_BAR['HEIGHT']))

        # Score
        screen.blit(font.render(str(state.opponent_score), False, COLORS['WHITE']), 
                   (WIDTH // 4, 20))
        screen.blit(font.render(str(state.player_score), False, COLORS['WHITE']), 
                   (3 * WIDTH // 4, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()