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
    'YELLOW': (255, 255, 0),
}

NEON_COLORS = [
    (0, 255, 255),    # Cyan - slow
    (0, 255, 0),      # Green - medium slow
    (255, 255, 0),    # Yellow - medium
    (255, 165, 0),    # Orange - medium fast
    (255, 0, 255),    # Magenta - fast
    (255, 0, 0),      # Red - very fast
]

# Game object properties
PADDLE = {'WIDTH': 15, 'HEIGHT': 90}
BALL = {'SIZE': 15}
SPEEDS = {
    'PADDLE_BASE': 6,
    'PADDLE_BOOST': 10,
    'BALL_BASE_X': 5,
    'BALL_BASE_Y': 3,
    'SLAM_X': 15,
    'LOB_Y': 12
}
STAMINA = {'MAX': 100, 'DRAIN': 0.5, 'REGEN': 0.3, 'SLAM_COST': 50, 'LOB_COST': 30}
SPIN = {'MAX': 0.1, 'VELOCITY_FACTOR': 0.08}
TRAIL = {'LENGTH': 5}
SLAM = {'DURATION': 60, 'DECELERATION': 0.95}
EXPLOSION = {'DURATION': 20, 'MAX_SIZE': 50}

# Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong with Smooth AI")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Game objects
player = pygame.Rect(WIDTH - 20 - PADDLE['WIDTH'], HEIGHT // 2 - PADDLE['HEIGHT'] // 2,
                    PADDLE['WIDTH'], PADDLE['HEIGHT'])
opponent = pygame.Rect(20, HEIGHT // 2 - PADDLE['HEIGHT'] // 2,
                      PADDLE['WIDTH'], PADDLE['HEIGHT'])

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - BALL['SIZE'] // 2, HEIGHT // 2 - BALL['SIZE'] // 2,
                              BALL['SIZE'], BALL['SIZE'])
        self.dx = SPEEDS['BALL_BASE_X'] * random.choice((1, -1))
        self.dy = SPEEDS['BALL_BASE_Y'] * random.choice((1, -1))
        self.spin = 0
        self.trail = deque(maxlen=TRAIL['LENGTH'])
        self.slam_timer = 0
        self.is_slam_active = False
        self.is_lob = False
        self.explosion_timer = 0
        self.explosion_pos = None

class GameState:
    def __init__(self, two_players):
        self.balls = [Ball()]
        self.player_vel = 0
        self.opponent_vel = 0
        self.player_stamina = STAMINA['MAX']
        self.opponent_stamina = STAMINA['MAX']
        self.player_score = 0
        self.opponent_score = 0
        self.spawn_timer = 0
        self.max_balls = 3
        self.two_players = two_players
        self.ai_target_y = HEIGHT // 2

def calculate_spin(paddle, ball_rect, paddle_velocity):
    relative_hit_pos = (ball_rect.centery - paddle.centery) / (PADDLE['HEIGHT'] / 2)
    position_spin = relative_hit_pos * SPIN['MAX']
    velocity_spin = paddle_velocity * SPIN['VELOCITY_FACTOR']
    return max(min(position_spin + velocity_spin, SPIN['MAX']), -SPIN['MAX'])

def move_paddle(paddle, vel, speed):
    paddle.y += vel
    paddle.clamp_ip((0, 0), (WIDTH, HEIGHT))

def reset_ball(ball):
    ball.rect.center = (WIDTH // 2, HEIGHT // 2)
    ball.dx = SPEEDS['BALL_BASE_X'] * random.choice((1, -1))
    ball.dy = SPEEDS['BALL_BASE_Y'] * random.choice((1, -1))
    ball.spin = 0
    ball.trail.clear()
    ball.slam_timer = 0
    ball.is_slam_active = False
    ball.is_lob = False
    ball.explosion_timer = 0
    ball.explosion_pos = None

def interpolate_color(color1, color2, factor):
    return tuple(int(c1 + (c2 - c1) * factor) for c1, c2 in zip(color1, color2))

def get_ball_color(ball_dx, ball_dy):
    speed = (ball_dx ** 2 + ball_dy ** 2) ** 0.5
    max_speed = (SPEEDS['SLAM_X'] ** 2 + (SPEEDS['LOB_Y']) ** 2) ** 0.5
    speed_factor = min(speed / max_speed, 1.0) * (len(NEON_COLORS) - 1)
    index = int(speed_factor)
    fraction = speed_factor - index
    if index >= len(NEON_COLORS) - 1:
        return NEON_COLORS[-1]
    return interpolate_color(NEON_COLORS[index], NEON_COLORS[index + 1], fraction)

def ai_move(state, opponent):
    threatening_ball = None
    min_time_to_reach = float('inf')
    
    for ball in state.balls:
        if ball.dx > 0:
            time_to_reach = (opponent.right - ball.rect.left) / ball.dx
            if time_to_reach > 0 and time_to_reach < min_time_to_reach:
                min_time_to_reach = time_to_reach
                threatening_ball = ball
    
    if threatening_ball:
        predicted_y = threatening_ball.rect.centery + threatening_ball.dy * min_time_to_reach
        while predicted_y < 0 or predicted_y > HEIGHT:
            if predicted_y < 0:
                predicted_y = -predicted_y
            elif predicted_y > HEIGHT:
                predicted_y = HEIGHT - (predicted_y - HEIGHT)
        
        state.ai_target_y += (predicted_y - state.ai_target_y) * 0.2
        dist_to_target = abs(opponent.centery - state.ai_target_y)
        speed = SPEEDS['PADDLE_BASE']
        if dist_to_target > PADDLE['HEIGHT'] * 1.5 and state.opponent_stamina > STAMINA['DRAIN'] * 15:
            speed = SPEEDS['PADDLE_BOOST']
            state.opponent_stamina -= STAMINA['DRAIN']
        else:
            state.opponent_stamina = min(state.opponent_stamina + STAMINA['REGEN'], STAMINA['MAX'])

        dead_zone = 15
        if opponent.centery < state.ai_target_y - dead_zone:
            state.opponent_vel = speed
        elif opponent.centery > state.ai_target_y + dead_zone:
            state.opponent_vel = -speed
        else:
            state.opponent_vel = 0
    else:
        target_center = HEIGHT // 2 + random.uniform(-20, 20)
        state.ai_target_y += (target_center - state.ai_target_y) * 0.1
        
        speed = SPEEDS['PADDLE_BASE']
        dead_zone = 20
        if opponent.centery < state.ai_target_y - dead_zone:
            state.opponent_vel = speed
        elif opponent.centery > state.ai_target_y + dead_zone:
            state.opponent_vel = -speed
        else:
            state.opponent_vel = 0
    
    move_paddle(opponent, state.opponent_vel, speed)

def get_player_count():
    selection = None
    while selection not in ['1', '2']:
        screen.fill(COLORS['BLACK'])
        text = font.render("Select number of players (1 or 2):", True, COLORS['WHITE'])
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selection = '1'
                elif event.key == pygame.K_2:
                    selection = '2'
    return selection == '2'

def main():
    two_players = get_player_count()
    state = GameState(two_players)
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Input handling
        keys = pygame.key.get_pressed()
        
        # Player controls
        state.player_vel = 0
        player_speed = SPEEDS['PADDLE_BASE']
        boosting_player = keys[pygame.K_o] and state.player_stamina > 0
        
        if boosting_player:
            player_speed = SPEEDS['PADDLE_BOOST']
            state.player_stamina -= STAMINA['DRAIN']
        else:
            state.player_stamina = min(state.player_stamina + STAMINA['REGEN'], STAMINA['MAX'])
            
        if keys[pygame.K_i]: state.player_vel = -player_speed
        if keys[pygame.K_k]: state.player_vel = player_speed
        slam_player = keys[pygame.K_j] and state.player_stamina >= STAMINA['SLAM_COST']
        lob_player = keys[pygame.K_u] and state.player_stamina >= STAMINA['LOB_COST']
        move_paddle(player, state.player_vel, player_speed)

        # Opponent controls
        state.opponent_vel = 0
        if state.two_players:
            opponent_speed = SPEEDS['PADDLE_BASE']
            boosting_opponent = keys[pygame.K_q] and state.opponent_stamina > 0
            
            if boosting_opponent:
                opponent_speed = SPEEDS['PADDLE_BOOST']
                state.opponent_stamina -= STAMINA['DRAIN']
            else:
                state.opponent_stamina = min(state.opponent_stamina + STAMINA['REGEN'], STAMINA['MAX'])
                
            if keys[pygame.K_w]: state.opponent_vel = -opponent_speed
            if keys[pygame.K_s]: state.opponent_vel = opponent_speed
            slam_opponent = keys[pygame.K_d] and state.opponent_stamina >= STAMINA['SLAM_COST']
            lob_opponent = keys[pygame.K_e] and state.opponent_stamina >= STAMINA['LOB_COST']
            move_paddle(opponent, state.opponent_vel, opponent_speed)
        else:
            ai_move(state, opponent)
            slam_opponent = random.random() < 0.03 and state.opponent_stamina >= STAMINA['SLAM_COST']
            lob_opponent = random.random() < 0.03 and state.opponent_stamina >= STAMINA['LOB_COST']

        # Ball spawning
        state.spawn_timer += 1
        if state.spawn_timer >= 300 and len(state.balls) < state.max_balls:
            state.balls.append(Ball())
            state.spawn_timer = 0

        # Ball updates
        balls_to_process = state.balls[:]
        for i, ball in enumerate(balls_to_process):
            ball.trail.append(ball.rect.center)
            ball.dy += ball.spin
            
            new_rect = ball.rect.move(ball.dx, ball.dy)
            if new_rect.top <= 0:
                ball.rect.top = 0
                if ball.explosion_timer == 0:
                    ball.explosion_timer = EXPLOSION['DURATION']
                    ball.explosion_pos = ball.rect.center
                ball.dy = max(abs(ball.dy) * 0.9, SPEEDS['BALL_BASE_Y'])
                ball.spin *= 0.8
            elif new_rect.bottom >= HEIGHT:
                ball.rect.bottom = HEIGHT
                if ball.explosion_timer == 0:
                    ball.explosion_timer = EXPLOSION['DURATION']
                    ball.explosion_pos = ball.rect.center
                ball.dy = -max(abs(ball.dy) * 0.9, SPEEDS['BALL_BASE_Y'])
                ball.spin *= 0.8
            else:
                ball.rect = new_rect

            if ball.explosion_timer > 0:
                ball.explosion_timer -= 1

            if ball.slam_timer > 0:
                ball.slam_timer -= 1
                if ball.slam_timer == 0:
                    ball.is_slam_active = False
            elif not ball.is_slam_active and abs(ball.dx) > SPEEDS['BALL_BASE_X']:
                ball.dx *= SLAM['DECELERATION']
                if abs(ball.dx) <= SPEEDS['BALL_BASE_X']:
                    ball.dx = SPEEDS['BALL_BASE_X'] * (1 if ball.dx > 0 else -1)
            
            if ball.is_lob:
                ball.dy *= 0.98

            for other_ball in balls_to_process[i+1:]:
                if ball.rect.colliderect(other_ball.rect):
                    if ball.explosion_timer == 0:
                        ball.explosion_timer = EXPLOSION['DURATION']
                        ball.explosion_pos = ball.rect.center
                    if other_ball.explosion_timer == 0:
                        other_ball.explosion_timer = EXPLOSION['DURATION']
                        other_ball.explosion_pos = other_ball.rect.center
                    ball.dx, other_ball.dx = other_ball.dx, ball.dx
                    ball.dy, other_ball.dy = other_ball.dy, ball.dy

            for paddle, vel, is_player in [(player, state.player_vel, True), 
                                         (opponent, state.opponent_vel, False)]:
                if ball.rect.colliderect(paddle):
                    if ball.explosion_timer == 0:
                        ball.explosion_timer = EXPLOSION['DURATION']
                        ball.explosion_pos = ball.rect.center
                    ball.dx = -abs(ball.dx) if is_player else abs(ball.dx)
                    ball.spin = calculate_spin(paddle, ball.rect, vel)
                    
                    if is_player and slam_player:
                        ball.dx = -SPEEDS['SLAM_X']
                        ball.slam_timer = SLAM['DURATION']
                        ball.is_slam_active = True
                        state.player_stamina -= STAMINA['SLAM_COST']
                    elif is_player and lob_player:
                        ball.dy = -SPEEDS['LOB_Y']
                        ball.is_lob = True
                        state.player_stamina -= STAMINA['LOB_COST']
                    elif not is_player and slam_opponent:
                        ball.dx = SPEEDS['SLAM_X']
                        ball.slam_timer = SLAM['DURATION']
                        ball.is_slam_active = True
                        state.opponent_stamina -= STAMINA['SLAM_COST']
                    elif not is_player and lob_opponent:
                        ball.dy = -SPEEDS['LOB_Y']
                        ball.is_lob = True
                        state.opponent_stamina -= STAMINA['LOB_COST']

            if ball.rect.left <= 0:
                state.player_score += 1
                state.balls.remove(ball)
            elif ball.rect.right >= WIDTH:
                state.opponent_score += 1
                state.balls.remove(ball)

        if not state.balls:
            state.balls.append(Ball())

        # Rendering
        screen.fill(COLORS['BLACK'])
        
        for ball in state.balls:
            if ball.explosion_timer > 0 and ball.explosion_pos:
                size = EXPLOSION['MAX_SIZE'] * (1 - ball.explosion_timer / EXPLOSION['DURATION'])
                alpha = int(255 * (ball.explosion_timer / EXPLOSION['DURATION']))
                explosion_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(explosion_surface, (*COLORS['YELLOW'], alpha), 
                                 (size/2, size/2), size/2)
                screen.blit(explosion_surface, 
                          (ball.explosion_pos[0] - size/2, ball.explosion_pos[1] - size/2))

            ball_color = get_ball_color(ball.dx, ball.dy)
            for i, pos in enumerate(ball.trail):
                alpha = (i + 1) / TRAIL['LENGTH']
                size = BALL['SIZE'] * (0.8 ** (TRAIL['LENGTH'] - i))
                trail_color = tuple(int(c * alpha) for c in ball_color)
                pygame.draw.ellipse(screen, trail_color, 
                                  (pos[0] - size/2, pos[1] - size/2, size, size))
            pygame.draw.ellipse(screen, ball_color, ball.rect)

        pygame.draw.rect(screen, COLORS['WHITE'], player)
        pygame.draw.rect(screen, COLORS['WHITE'], opponent)
        pygame.draw.aaline(screen, COLORS['WHITE'], (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))

        STAMINA_BAR = {'WIDTH': 100, 'HEIGHT': 10, 'OFFSET': 50}
        for bar_x, stamina in [(WIDTH - STAMINA_BAR['WIDTH'] - STAMINA_BAR['OFFSET'], 
                              state.player_stamina),
                              (STAMINA_BAR['OFFSET'], state.opponent_stamina)]:
            pygame.draw.rect(screen, COLORS['RED'], 
                           (bar_x, HEIGHT - 30, STAMINA_BAR['WIDTH'], STAMINA_BAR['HEIGHT']))
            pygame.draw.rect(screen, COLORS['GREEN'], 
                           (bar_x, HEIGHT - 30, stamina, STAMINA_BAR['HEIGHT']))

        screen.blit(font.render(f"Score: {state.opponent_score}", False, COLORS['WHITE']), 
                   (WIDTH // 4, 20))
        screen.blit(font.render(f"Score: {state.player_score}", False, COLORS['WHITE']), 
                   (3 * WIDTH // 4, 20))
        screen.blit(font.render(f"Balls: {len(state.balls)}", False, COLORS['WHITE']), 
                   (WIDTH // 2 - 30, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()