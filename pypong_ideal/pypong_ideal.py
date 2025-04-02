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
    'BLUE': (0, 0, 255),
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
    'PADDLE_BASE': 5,
    'PADDLE_BOOST': 8,
    'BALL_BASE_X': 5,
    'BALL_BASE_Y': 3,    # Reduced base Y speed for more control
    'SLAM_X': 15,
    'LOB_Y': 12         # Increased for more pronounced arc
}
STAMINA = {'MAX': 100, 'DRAIN': 0.5, 'REGEN': 0.2, 'SLAM_COST': 50, 'LOB_COST': 30}
SPIN = {'MAX': 0.1, 'VELOCITY_FACTOR': 0.08}  # Increased for smoother arcs
TRAIL = {'LENGTH': 5}
SLAM = {'DURATION': 60, 'DECELERATION': 0.95}

# Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong with Multiple Balls and Shot Types")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Game objects
player = pygame.Rect(WIDTH - 20 - PADDLE['WIDTH'], HEIGHT // 2 - PADDLE['HEIGHT'] // 2,
                    PADDLE['WIDTH'], PADDLE['HEIGHT'])
opponent = pygame.Rect(20, HEIGHT // 2 - PADDLE['HEIGHT'] // 2,
                      PADDLE['WIDTH'], PADDLE['HEIGHT'])

# Ball class to handle multiple balls
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

# Game state
class GameState:
    def __init__(self):
        self.balls = [Ball()]
        self.player_vel = 0
        self.opponent_vel = 0
        self.player_stamina = STAMINA['MAX']
        self.opponent_stamina = STAMINA['MAX']
        self.player_score = 0
        self.opponent_score = 0
        self.spawn_timer = 0
        self.max_balls = 3
        self.ai_mode = False  # AI mode control
        self.game_started = False

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

def ai_control(state, opponent, player, balls):
    ai_difficulty = 1  # Adjust for harder/easier AI (higher = better)
    ai_reaction = 0.7  # How quickly AI reacts to the ball (lower = faster)
    
    # Find closest ball to track
    closest_ball = None
    closest_distance = float('inf')
    for ball in balls:
        if ball.dx < 0:  # Ball is moving towards AI
            distance = opponent.centery - ball.rect.centery
            if abs(distance) < closest_distance:
                closest_distance = abs(distance)
                closest_ball = ball
    
    # Default values
    opponent_vel = 0
    opponent_speed = SPEEDS['PADDLE_BASE']
    slam_opponent = False
    lob_opponent = False
    is_using_boost = False
    
    if closest_ball:
        # Calculate target position with some error based on difficulty
        target_y = closest_ball.rect.centery
        target_y += random.randint(-int((1-ai_difficulty) * 100), int((1-ai_difficulty) * 100))
        
        # Only move if ball is within reaction distance on x-axis
        if closest_ball.rect.centerx < WIDTH * ai_reaction:
            if target_y < opponent.centery - 10:
                opponent_vel = -opponent_speed
            elif target_y > opponent.centery + 10:
                opponent_vel = opponent_speed
        
        # AI special shots - more aggressive usage
        if abs(closest_ball.rect.x - opponent.right) < 20:  # Ball is very close to paddle
            if state.opponent_stamina >= STAMINA['SLAM_COST'] and random.random() < 0.7:
                slam_opponent = True
            elif state.opponent_stamina >= STAMINA['LOB_COST'] and random.random() < 0.7:
                lob_opponent = True
        
        # AI uses boost when needed
        if abs(opponent.centery - target_y) > PADDLE['HEIGHT'] and state.opponent_stamina > 20:
            opponent_speed = SPEEDS['PADDLE_BOOST']
            state.opponent_stamina -= STAMINA['DRAIN']
            is_using_boost = True
    
    # Always regenerate stamina when not boosting
    if not is_using_boost and not slam_opponent and not lob_opponent:
        state.opponent_stamina = min(state.opponent_stamina + STAMINA['REGEN'], STAMINA['MAX'])
    
    return opponent_vel, opponent_speed, slam_opponent, lob_opponent

def main():
    state = GameState()
    running = True
    menu_active = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if menu_active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    state.ai_mode = True
                    menu_active = False
                    state.game_started = True
                elif event.key == pygame.K_2:
                    state.ai_mode = False
                    menu_active = False
                    state.game_started = True
        
        if menu_active:
            # Display menu
            screen.fill(COLORS['BLACK'])
            title = font.render("PONG", True, COLORS['WHITE'])
            option1 = font.render("Press 1 for 1 Player (vs AI)", True, COLORS['WHITE'])
            option2 = font.render("Press 2 for 2 Players", True, COLORS['WHITE'])
            
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
            screen.blit(option1, (WIDTH//2 - option1.get_width()//2, HEIGHT//2))
            screen.blit(option2, (WIDTH//2 - option2.get_width()//2, HEIGHT//2 + 50))
            
            pygame.display.flip()
            clock.tick(FPS)
            continue

        # Input handling
        keys = pygame.key.get_pressed()
        
        # Player controls (Right side - IJKL cluster)
        state.player_vel = 0
        player_speed = SPEEDS['PADDLE_BASE']
        boosting_player = keys[pygame.K_o] and state.player_stamina > 0  # O (Boost)
        
        if boosting_player:
            player_speed = SPEEDS['PADDLE_BOOST']
            state.player_stamina -= STAMINA['DRAIN']
        else:
            state.player_stamina = min(state.player_stamina + STAMINA['REGEN'], STAMINA['MAX'])
            
        if keys[pygame.K_i]: state.player_vel = -player_speed  # I (Up)
        if keys[pygame.K_k]: state.player_vel = player_speed   # K (Down)
        if keys[pygame.K_j] and state.player_stamina >= STAMINA['SLAM_COST']:  # L (Slam)
            slam_player = True
        else:
            slam_player = False
        if keys[pygame.K_u] and state.player_stamina >= STAMINA['LOB_COST']:  # U (Lob)
            lob_player = True
        else:
            lob_player = False
        move_paddle(player, state.player_vel, player_speed)

        # Opponent controls - AI or Human based on mode
        state.opponent_vel = 0
        opponent_speed = SPEEDS['PADDLE_BASE']
        slam_opponent = False
        lob_opponent = False
        
        if state.ai_mode:
            # AI controls for opponent
            state.opponent_vel, opponent_speed, slam_opponent, lob_opponent = ai_control(
                state, opponent, player, state.balls
            )
        else:
            # Human controls for opponent (Left side - WASD cluster)
            boosting_opponent = keys[pygame.K_q] and state.opponent_stamina > 0  # Q (Boost)
            
            if boosting_opponent:
                opponent_speed = SPEEDS['PADDLE_BOOST']
                state.opponent_stamina -= STAMINA['DRAIN']
            else:
                state.opponent_stamina = min(state.opponent_stamina + STAMINA['REGEN'], STAMINA['MAX'])
                
            if keys[pygame.K_w]: state.opponent_vel = -opponent_speed  # W (Up)
            if keys[pygame.K_s]: state.opponent_vel = opponent_speed   # S (Down)
            if keys[pygame.K_d] and state.opponent_stamina >= STAMINA['SLAM_COST']:  # D (Slam)
                slam_opponent = True
            if keys[pygame.K_e] and state.opponent_stamina >= STAMINA['LOB_COST']:  # E (Lob)
                lob_opponent = True
                
        move_paddle(opponent, state.opponent_vel, opponent_speed)

        # Ball spawning
        state.spawn_timer += 1
        if state.spawn_timer >= 300 and len(state.balls) < state.max_balls:  # Spawn every 5 seconds
            state.balls.append(Ball())
            state.spawn_timer = 0

        # Ball updates
        for ball in state.balls[:]:
            ball.trail.append(ball.rect.center)
            ball.dy += ball.spin
            ball.rect.move_ip(ball.dx, ball.dy)

            # Slam and lob handling
            if ball.slam_timer > 0:
                ball.slam_timer -= 1
                if ball.slam_timer == 0:
                    ball.is_slam_active = False
            elif not ball.is_slam_active and abs(ball.dx) > SPEEDS['BALL_BASE_X']:
                ball.dx *= SLAM['DECELERATION']
                if abs(ball.dx) <= SPEEDS['BALL_BASE_X']:
                    ball.dx = SPEEDS['BALL_BASE_X'] * (1 if ball.dx > 0 else -1)
            
            if ball.is_lob:
                ball.dy *= 0.98  # Gradual slowdown for lob arc

            # Ball collisions
            if ball.rect.top <= 0:
                ball.dy = abs(ball.dy) * 0.9  # Slight energy loss
                ball.spin *= 0.8
            elif ball.rect.bottom >= HEIGHT:
                ball.dy = -abs(ball.dy) * 0.9  # Slight energy loss
                ball.spin *= 0.8

            # Paddle collisions
            for paddle, vel, is_player in [(player, state.player_vel, True), 
                                         (opponent, state.opponent_vel, False)]:
                if ball.rect.colliderect(paddle):
                    ball.dx = -abs(ball.dx) if is_player else abs(ball.dx)
                    ball.spin = calculate_spin(paddle, ball.rect, vel)
                    
                    # Shot types
                    if is_player:
                        if slam_player:
                            ball.dx = -SPEEDS['SLAM_X']
                            ball.slam_timer = SLAM['DURATION']
                            ball.is_slam_active = True
                            state.player_stamina -= STAMINA['SLAM_COST']
                        elif lob_player:
                            ball.dy = -SPEEDS['LOB_Y']
                            ball.is_lob = True
                            state.player_stamina -= STAMINA['LOB_COST']
                    else:
                        if slam_opponent:
                            ball.dx = SPEEDS['SLAM_X']
                            ball.slam_timer = SLAM['DURATION']
                            ball.is_slam_active = True
                            state.opponent_stamina -= STAMINA['SLAM_COST']
                        elif lob_opponent:
                            ball.dy = -SPEEDS['LOB_Y']
                            ball.is_lob = True
                            state.opponent_stamina -= STAMINA['LOB_COST']

            # Scoring
            if ball.rect.left <= 0:
                state.player_score += 1
                state.balls.remove(ball)
            elif ball.rect.right >= WIDTH:
                state.opponent_score += 1
                state.balls.remove(ball)

        # Ensure at least one ball exists
        if not state.balls:
            state.balls.append(Ball())

        # Rendering
        screen.fill(COLORS['BLACK'])
        
        for ball in state.balls:
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

        # Stamina bars
        STAMINA_BAR = {'WIDTH': 100, 'HEIGHT': 10, 'OFFSET': 50}
        for bar_x, stamina in [(WIDTH - STAMINA_BAR['WIDTH'] - STAMINA_BAR['OFFSET'], 
                              state.player_stamina),
                              (STAMINA_BAR['OFFSET'], state.opponent_stamina)]:
            pygame.draw.rect(screen, COLORS['RED'], 
                           (bar_x, HEIGHT - 30, STAMINA_BAR['WIDTH'], STAMINA_BAR['HEIGHT']))
            pygame.draw.rect(screen, COLORS['GREEN'], 
                           (bar_x, HEIGHT - 30, stamina, STAMINA_BAR['HEIGHT']))

        # Score and ball count
        screen.blit(font.render(f"Score: {state.opponent_score}", False, COLORS['WHITE']), 
                   (WIDTH // 4, 20))
        screen.blit(font.render(f"Score: {state.player_score}", False, COLORS['WHITE']), 
                   (3 * WIDTH // 4, 20))
        screen.blit(font.render(f"Balls: {len(state.balls)}", False, COLORS['WHITE']), 
                   (WIDTH // 2 - 30, 20))
        
        # Display game mode
        mode_text = "1P MODE" if state.ai_mode else "2P MODE"
        screen.blit(font.render(mode_text, False, COLORS['WHITE']), (WIDTH // 2 - 40, HEIGHT - 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()