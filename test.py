import pygame
import time

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT_SIZE = 80

# Game State Enumeration
class GameState:
    START = 1
    RUNNING = 2
    PAUSED = 3

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Pong Game')

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.state = GameState.START  # Initial state is 'START'

        # Create ball and paddles (use classes for better structure)
        self.ball = Ball(self.screen)
        self.left_paddle = Paddle(self.screen, 30, SCREEN_HEIGHT // 2 - 50)
        self.right_paddle = Paddle(self.screen, SCREEN_WIDTH - 50, SCREEN_HEIGHT // 2 - 50)

    def run_game(self):
        running = True
        while running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.update()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # Handle game state changes
            if self.state == GameState.START:
                # Waiting for 'Space' key to start the game
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.state = GameState.RUNNING

            elif self.state == GameState.PAUSED:
                # Press space to resume after the 3-second countdown
                # if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.start_countdown()  # Start the 3-second countdown

    def start_countdown(self):
        """
        Countdown of 3 seconds after a player misses the ball, displayed on screen.
        """
        for i in range(3, 0, -1):  # Countdown 3, 2, 1
            self.screen.fill(BLACK)
            countdown_text = self.font.render(str(i), True, WHITE)
            self.screen.blit(countdown_text, (SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 - 40))
            pygame.display.update()
            time.sleep(1)  # Pause for 1 second for each countdown

        self.state = GameState.RUNNING  # Resume the game

    def update(self):
        if self.state == GameState.RUNNING:
            self.ball.update()
            self.left_paddle.update()
            self.right_paddle.update()

            # Ball collision logic (missed hit)
            if self.ball.rect.left <= 0 or self.ball.rect.right >= SCREEN_WIDTH:
                self.ball.reset_position()  # Reset the ball to the center
                self.state = GameState.PAUSED  # Pause the game after a missed hit

    def draw(self):
        if self.state == GameState.START:
            self.screen.fill(BLACK)
            start_text = self.font.render("Press SPACE to Start", True, WHITE)
            self.screen.blit(start_text, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 40))

        elif self.state == GameState.RUNNING:
            self.screen.fill(BLACK)
            self.ball.draw()
            self.left_paddle.draw()
            self.right_paddle.draw()

        elif self.state == GameState.PAUSED:
            pause_text = self.font.render("Game Paused", True, WHITE)
            self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 40))

class Ball:
    def __init__(self, screen):
        self.screen = screen
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 - 15, 30, 30)
        self.color = WHITE
        self.speed_x = 7
        self.speed_y = 7

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Ball bounces off top and bottom
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.speed_y = -self.speed_y

    def reset_position(self):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def draw(self):
        pygame.draw.ellipse(self.screen, self.color, self.rect)

class Paddle:
    def __init__(self, screen, x, y):
        self.screen = screen
        self.rect = pygame.Rect(x, y, 20, 100)
        self.color = WHITE
        self.speed = 10

    def update(self):
        keys = pygame.key.get_pressed()
        if self.rect.left < SCREEN_WIDTH // 2:
            if keys[pygame.K_w] and self.rect.top > 0:
                self.rect.y -= self.speed
            if keys[pygame.K_s] and self.rect.bottom < SCREEN_HEIGHT:
                self.rect.y += self.speed
        else:
            if keys[pygame.K_UP] and self.rect.top > 0:
                self.rect.y -= self.speed
            if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
                self.rect.y += self.speed

    def draw(self):
        pygame.draw.rect(self.screen, self.color, self.rect)

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run_game()
