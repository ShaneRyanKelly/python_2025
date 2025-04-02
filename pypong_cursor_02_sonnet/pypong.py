import pygame
import random
import math
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
    'GOLD': (255, 215, 0),
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

# Tennis scoring
TENNIS_POINTS = ['0', '15', '30', '40', 'ADV']

# Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong with Multiple Balls and Shot Types")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

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
        self.max_balls = 1  # One ball for tennis mode
        self.ai_mode = False
        self.game_started = False
        self.gambling_mode = False
        
        # Tennis scoring
        self.left_points = 0
        self.right_points = 0
        self.left_games = 0
        self.right_games = 0
        self.left_sets = 0
        self.right_sets = 0
        self.deuce = False
        
        # Gambling properties
        self.player1_coins = 1000
        self.player2_coins = 1000
        self.player1_bet = 0
        self.player2_bet = 0
        self.player1_bet_on = None  # "left" or "right"
        self.player2_bet_on = None
        self.left_odds = 1.5
        self.right_odds = 2.5  # Higher odds for right (weaker) side
        self.point_scored = False
        self.point_delay = 60  # frames to wait after point
        self.multiball_timer = 0
        self.multiball_active = False
        self.bet_keys_released = True  # Track if bet keys have been released

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

def ai_control(paddle, is_left, balls, difficulty=1.0):
    # Find closest ball to track
    closest_ball = None
    closest_distance = float('inf')
    for ball in balls:
        if (is_left and ball.dx < 0) or (not is_left and ball.dx > 0):  # Ball is moving towards AI
            distance = paddle.centery - ball.rect.centery
            if abs(distance) < closest_distance:
                closest_distance = abs(distance)
                closest_ball = ball
    
    # Default values
    paddle_vel = 0
    paddle_speed = SPEEDS['PADDLE_BASE'] * difficulty
    slam = False
    lob = False
    
    if closest_ball:
        # Calculate target position with some error based on difficulty
        target_y = closest_ball.rect.centery
        # Add oscillation to create more movement and spin
        target_y += random.randint(-30, 30) + (20 * math.sin(pygame.time.get_ticks() / 500))
        
        # Add error based on inverse of difficulty
        error_factor = (2.0 - difficulty) * 80
        target_y += random.randint(int(-error_factor), int(error_factor))
        
        # Only move if ball is within reaction distance
        react_distance = WIDTH * (0.8 if is_left else 0.2)  # Adjust reaction distance based on side
        react_condition = closest_ball.rect.centerx < react_distance if is_left else closest_ball.rect.centerx > react_distance
        
        if react_condition:
            if target_y < paddle.centery - 5:  # Smaller threshold to increase movement
                paddle_vel = -paddle_speed
            elif target_y > paddle.centery + 5:
                paddle_vel = paddle_speed
            # Move randomly sometimes to create more dynamic play
            elif random.random() < 0.2:
                paddle_vel = random.choice([-1, 1]) * paddle_speed
        else:
            # Move slightly when not tracking to avoid being static
            if random.random() < 0.4:
                paddle_vel = random.choice([-1, 1]) * paddle_speed * 0.7
        
        # Special shots
        if (is_left and abs(closest_ball.rect.left - paddle.right) < 30) or \
           (not is_left and abs(closest_ball.rect.right - paddle.left) < 30):
            if random.random() < 0.5 * difficulty:
                slam = True
            elif random.random() < 0.4 * difficulty:
                lob = True
    
    return paddle_vel, paddle_speed, slam, lob

def update_tennis_score(state, left_scored):
    state.point_scored = True
    
    # Update odds based on current game state
    if left_scored:
        # Left side is winning more, decrease its odds, increase right's odds
        state.left_odds = max(1.2, state.left_odds - 0.1)
        state.right_odds = min(3.5, state.right_odds + 0.1)
    else:
        # Right side scored, adjust odds
        state.right_odds = max(1.5, state.right_odds - 0.1)
        state.left_odds = min(2.5, state.left_odds + 0.1)
    
    # Process scores
    if left_scored:
        if state.deuce:
            if state.left_points == 4:  # Advantage
                state.left_points = 0
                state.right_points = 0
                state.deuce = False
                state.left_games += 1
            elif state.right_points == 4:  # Was advantage to the other side
                state.right_points = 3
                state.left_points = 3
            else:
                state.left_points = 4  # Advantage
        else:
            state.left_points += 1
            if state.left_points == 3 and state.right_points == 3:
                state.deuce = True
            elif state.left_points >= 4:
                state.left_points = 0
                state.right_points = 0
                state.left_games += 1
    else:
        if state.deuce:
            if state.right_points == 4:  # Advantage
                state.left_points = 0
                state.right_points = 0
                state.deuce = False
                state.right_games += 1
            elif state.left_points == 4:  # Was advantage to the other side
                state.right_points = 3
                state.left_points = 3
            else:
                state.right_points = 4  # Advantage
        else:
            state.right_points += 1
            if state.left_points == 3 and state.right_points == 3:
                state.deuce = True
            elif state.right_points >= 4:
                state.left_points = 0
                state.right_points = 0
                state.right_games += 1
    
    # Process bets after score update
    if state.gambling_mode:
        # Player 1 bet
        if state.player1_bet_on == "left" and left_scored:
            state.player1_coins += int(state.player1_bet * state.left_odds)
        elif state.player1_bet_on == "right" and not left_scored:
            state.player1_coins += int(state.player1_bet * state.right_odds)
        
        # Player 2 bet
        if state.player2_bet_on == "left" and left_scored:
            state.player2_coins += int(state.player2_bet * state.left_odds)
        elif state.player2_bet_on == "right" and not left_scored:
            state.player2_coins += int(state.player2_bet * state.right_odds)
        
        # Reset bets
        state.player1_bet = 0
        state.player2_bet = 0
        state.player1_bet_on = None
        state.player2_bet_on = None
        
        # Check if it's time for multiball (every few points)
        if (state.left_games + state.right_games) % 3 == 0:
            state.multiball_active = True
            
        # Reset bet keys state
        state.bet_keys_released = True

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
                elif event.key == pygame.K_0 or event.key == pygame.K_3:  # Combined gambling mode and no-play mode
                    state.ai_mode = True
                    state.gambling_mode = True
                    menu_active = False
                    state.game_started = True
        
        if menu_active:
            # Display menu
            screen.fill(COLORS['BLACK'])
            title = font.render("PONG", True, COLORS['WHITE'])
            option1 = font.render("Press 1 for 1 Player (vs AI)", True, COLORS['WHITE'])
            option2 = font.render("Press 2 for 2 Players", True, COLORS['WHITE'])
            option3 = font.render("Press 0 or 3 for Tennis Gambling Mode", True, COLORS['GOLD'])
            
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
            screen.blit(option1, (WIDTH//2 - option1.get_width()//2, HEIGHT//2))
            screen.blit(option2, (WIDTH//2 - option2.get_width()//2, HEIGHT//2 + 50))
            screen.blit(option3, (WIDTH//2 - option3.get_width()//2, HEIGHT//2 + 100))
            
            pygame.display.flip()
            clock.tick(FPS)
            continue

        # Input handling
        keys = pygame.key.get_pressed()
        
        if state.gambling_mode:
            # Handle betting input
            if not state.point_scored and len(state.balls) > 0:
                # Handle toggle for bet keys to prevent continuous deduction
                bet_keys_pressed = keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_j] or keys[pygame.K_l]
                
                if not bet_keys_pressed:
                    state.bet_keys_released = True
            
                # Player 1 controls (WASD)
                if keys[pygame.K_w] and pygame.time.get_ticks() % 5 == 0:
                    state.player1_bet = min(state.player1_bet + 10, state.player1_coins)
                if keys[pygame.K_s] and pygame.time.get_ticks() % 5 == 0:
                    state.player1_bet = max(state.player1_bet - 10, 0)
                    
                if state.bet_keys_released:  # Only process if keys were released
                    if keys[pygame.K_a] and state.player1_bet > 0 and state.player1_bet <= state.player1_coins and not state.player1_bet_on:
                        state.player1_bet_on = "left"
                        state.player1_coins -= state.player1_bet
                        state.bet_keys_released = False
                    if keys[pygame.K_d] and state.player1_bet > 0 and state.player1_bet <= state.player1_coins and not state.player1_bet_on:
                        state.player1_bet_on = "right"
                        state.player1_coins -= state.player1_bet
                        state.bet_keys_released = False
                    
                # Player 2 controls (IJKL)
                if keys[pygame.K_i] and pygame.time.get_ticks() % 5 == 0:
                    state.player2_bet = min(state.player2_bet + 10, state.player2_coins)
                if keys[pygame.K_k] and pygame.time.get_ticks() % 5 == 0:
                    state.player2_bet = max(state.player2_bet - 10, 0)
                    
                if state.bet_keys_released:  # Only process if keys were released
                    if keys[pygame.K_j] and state.player2_bet > 0 and state.player2_bet <= state.player2_coins and not state.player2_bet_on:
                        state.player2_bet_on = "left"
                        state.player2_coins -= state.player2_bet
                        state.bet_keys_released = False
                    if keys[pygame.K_l] and state.player2_bet > 0 and state.player2_bet <= state.player2_coins and not state.player2_bet_on:
                        state.player2_bet_on = "right"
                        state.player2_coins -= state.player2_bet
                        state.bet_keys_released = False
            
            # AI controls for both paddles with very different skill levels
            left_vel, left_speed, slam_left, lob_left = ai_control(opponent, True, state.balls, 1.5)  # Left AI is much better
            right_vel, right_speed, slam_right, lob_right = ai_control(player, False, state.balls, 0.6)  # Right AI is much weaker
            
            # Move paddles
            move_paddle(opponent, left_vel, left_speed * 1.3)  # Left paddle moves faster
            move_paddle(player, right_vel, right_speed * 0.7)  # Right paddle is slower
            
            # Update stamina
            state.opponent_stamina = min(state.opponent_stamina + STAMINA['REGEN'], STAMINA['MAX'])
            state.player_stamina = min(state.player_stamina + STAMINA['REGEN'], STAMINA['MAX'])
            
            if slam_left and state.opponent_stamina >= STAMINA['SLAM_COST']:
                state.opponent_stamina -= STAMINA['SLAM_COST']
            if lob_left and state.opponent_stamina >= STAMINA['LOB_COST']:
                state.opponent_stamina -= STAMINA['LOB_COST']
            if slam_right and state.player_stamina >= STAMINA['SLAM_COST']:
                state.player_stamina -= STAMINA['SLAM_COST'] 
            if lob_right and state.player_stamina >= STAMINA['LOB_COST']:
                state.player_stamina -= STAMINA['LOB_COST']
        else:
            # Regular game controls
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
            if keys[pygame.K_j] and state.player_stamina >= STAMINA['SLAM_COST']:  # J (Slam)
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
                    opponent, True, state.balls
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

        # Point delay after scoring
        if state.point_scored:
            state.point_delay -= 1
            if state.point_delay <= 0:
                state.point_scored = False
                state.point_delay = 60
                # Ensure there's a ball
                if len(state.balls) == 0 or (state.gambling_mode and state.multiball_active):
                    # Add base ball
                    if len(state.balls) == 0:
                        state.balls.append(Ball())
                        reset_ball(state.balls[0])
                    
                    # Add extra balls in multiball mode
                    if state.gambling_mode and state.multiball_active:
                        for _ in range(random.randint(1, 2)):  # Add 1-2 extra balls
                            new_ball = Ball()
                            # Give random speeds to make it more chaotic
                            new_ball.dx *= random.uniform(0.8, 1.2)
                            new_ball.dy *= random.uniform(0.8, 1.2)
                            state.balls.append(new_ball)
                        state.multiball_active = False
        
        # Ball updates
        for ball in state.balls[:]:
            if state.point_scored:
                continue  # Don't update the ball during point delay
                
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
            for paddle, vel, is_player, slam, lob in [
                (player, state.player_vel, True, slam_right if state.gambling_mode else slam_player, lob_right if state.gambling_mode else lob_player), 
                (opponent, state.opponent_vel, False, slam_left if state.gambling_mode else slam_opponent, lob_left if state.gambling_mode else lob_opponent)
            ]:
                if ball.rect.colliderect(paddle):
                    ball.dx = -abs(ball.dx) if is_player else abs(ball.dx)
                    ball.spin = calculate_spin(paddle, ball.rect, vel)
                    
                    # Shot types
                    stamina_ref = state.player_stamina if is_player else state.opponent_stamina
                    if slam and stamina_ref >= STAMINA['SLAM_COST']:
                        ball.dx = -SPEEDS['SLAM_X'] if is_player else SPEEDS['SLAM_X']
                        ball.slam_timer = SLAM['DURATION']
                        ball.is_slam_active = True
                        if is_player:
                            state.player_stamina -= STAMINA['SLAM_COST']
                        else:
                            state.opponent_stamina -= STAMINA['SLAM_COST']
                    elif lob and stamina_ref >= STAMINA['LOB_COST']:
                        ball.dy = -SPEEDS['LOB_Y']
                        ball.is_lob = True
                        if is_player:
                            state.player_stamina -= STAMINA['LOB_COST']
                        else:
                            state.opponent_stamina -= STAMINA['LOB_COST']

            # Scoring
            if ball.rect.left <= 0:
                if state.gambling_mode:
                    update_tennis_score(state, False)  # Right player scored
                else:
                    state.player_score += 1
                state.balls.remove(ball)
            elif ball.rect.right >= WIDTH:
                if state.gambling_mode:
                    update_tennis_score(state, True)  # Left player scored
                else:
                    state.opponent_score += 1
                state.balls.remove(ball)

        # Ensure at least one ball exists in non-gambling mode
        if not state.gambling_mode and not state.balls:
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

        # Score display
        if state.gambling_mode:
            # Tennis scoring
            left_point = TENNIS_POINTS[min(state.left_points, 4)]
            right_point = TENNIS_POINTS[min(state.right_points, 4)]
            score_text = f"{left_point} - {right_point}"
            games_text = f"Games: {state.left_games} - {state.right_games}"
            
            screen.blit(font.render(score_text, True, COLORS['WHITE']), (WIDTH // 2 - 40, 20))
            screen.blit(font.render(games_text, True, COLORS['WHITE']), (WIDTH // 2 - 80, 60))
            
            # Gambling info
            pygame.draw.rect(screen, COLORS['GOLD'], (10, 100, 200, 120), 2)
            pygame.draw.rect(screen, COLORS['GOLD'], (WIDTH - 210, 100, 200, 120), 2)
            
            # Player 1 info
            screen.blit(font.render("Player 1", True, COLORS['GOLD']), (20, 110))
            screen.blit(font.render(f"Coins: {state.player1_coins}", True, COLORS['GOLD']), (20, 150))
            screen.blit(font.render(f"Bet: {state.player1_bet}", True, COLORS['GOLD']), (20, 190))
            if state.player1_bet_on:
                bet_text = f"On: {state.player1_bet_on.upper()}"
                screen.blit(font.render(bet_text, True, COLORS['GOLD']), (120, 190))
            
            # Player 2 info
            screen.blit(font.render("Player 2", True, COLORS['GOLD']), (WIDTH - 200, 110))
            screen.blit(font.render(f"Coins: {state.player2_coins}", True, COLORS['GOLD']), (WIDTH - 200, 150))
            screen.blit(font.render(f"Bet: {state.player2_bet}", True, COLORS['GOLD']), (WIDTH - 200, 190))
            if state.player2_bet_on:
                bet_text = f"On: {state.player2_bet_on.upper()}"
                screen.blit(font.render(bet_text, True, COLORS['GOLD']), (WIDTH - 100, 190))
            
            # Odds display - highlight the unbalanced odds
            screen.blit(font.render(f"Odds: {state.left_odds:.1f} | {state.right_odds:.1f}", True, COLORS['GOLD']), 
                       (WIDTH // 2 - 80, 100))
            
            # Multiball indicator
            if len(state.balls) > 1:
                multiball_text = "MULTIBALL ACTIVE!"
                screen.blit(font.render(multiball_text, True, COLORS['RED']), (WIDTH // 2 - 80, 130))
            
            # Betting instructions
            if not state.point_scored:
                instructions = small_font.render("P1: W/S to change bet, A/D to bet on left/right", True, COLORS['WHITE'])
                instructions2 = small_font.render("P2: I/K to change bet, J/L to bet on left/right", True, COLORS['WHITE'])
                screen.blit(instructions, (WIDTH // 2 - 150, HEIGHT - 60))
                screen.blit(instructions2, (WIDTH // 2 - 150, HEIGHT - 40))
        else:
            # Regular score
            screen.blit(font.render(f"Score: {state.opponent_score}", False, COLORS['WHITE']), 
                      (WIDTH // 4, 20))
            screen.blit(font.render(f"Score: {state.player_score}", False, COLORS['WHITE']), 
                      (3 * WIDTH // 4, 20))
            screen.blit(font.render(f"Balls: {len(state.balls)}", False, COLORS['WHITE']), 
                      (WIDTH // 2 - 30, 20))
        
        # Display game mode
        mode_text = "TENNIS GAMBLING" if state.gambling_mode else "1P MODE" if state.ai_mode else "2P MODE"
        screen.blit(font.render(mode_text, False, COLORS['WHITE']), (WIDTH // 2 - 80, HEIGHT - 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()