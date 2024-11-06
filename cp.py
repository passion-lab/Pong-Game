import time

import pygame as pg
# from enum import auto
import sys

# GLOBAL VARIABLES
NAME: str = "PONG"
SCREEN_H: int = 600
SCREEN_W: int = 800
BG_COLOR: tuple[int, int, int] | str = (0, 0, 0)
TEXT_COLOR: tuple[int, int, int] | str = (100, 100, 100)
COLOR_DICTIONARY["Paddle"]: tuple[int, int, int] | str = (255, 255, 255)
COLOR_DICTIONARY["Ball"]: tuple[int, int, int] | str = (255, 65, 0)
PADDLE_W: int = 10
PADDLE_H: int = 100
BALL_SIZE: int = 15
BALL_SPEED: int = 3
PADDLE_SPEED: int = 10
BALL_MISS_TIMEOUT: int = 5
SOUND_EFFECTS: dict[str: str | bytes] = {
    "wall_hit": "./sources/SFX/paddle-hit-2.mp3",
    "paddle_hit": "./sources/SFX/paddle-hit-1.mp3"
}

_screen_centre: tuple[int, int] = (SCREEN_W // 2, SCREEN_H // 2)
_x_margin: int = 50
# Updates when ball hits the paddle(s)
_l_paddle_cord: tuple[int, int, int, int] = (0, 0, 0, 0)  # T, L, B, R
_r_paddle_cord: tuple[int, int, int, int] = (0, 0, 0, 0)  # T, L, B, R


class FileLoader:
    def __init__(self):
        # Sets fonts for displaying the scores
        self.num_font = pg.font.Font("./sources/Fonts/RobotoCondensed-Bold.ttf", 25)
        self.text_font = pg.font.Font("./sources/Fonts/RobotoCondensed-Regular.ttf", 15)

        # Load files
        self.banner = pg.image.load("./sources/banner.png")
        self.bg = pg.image.load("./sources/bg.png")
        self.bg_rect = pg.image.load("./sources/bg_rectangle.png")


# Music and Sound Manager class
class SoundManager:
    def __init__(self, sfx_files: dict[str: str | bytes]) -> None:
        # Initializes the PyGame audio
        pg.mixer.init()

        # Loads sound effects from the given dictionary of sound names and paths
        self.sound_effects = {name: pg.mixer.Sound(path) for name, path in sfx_files.items()}

    def play_stop_sfx(self, name: str, play: bool = True) -> None:
        if name in self.sound_effects:
            self.sound_effects[name].play() if play else self.sound_effects[name].stop()


class GameState:
    START = 1
    RUNNING = 2
    PAUSED = 3


# Loads audio
sfx = SoundManager(SOUND_EFFECTS)


# Gaming control class
class PongGame:
    def __init__(self):
        pg.init()

        self.screen: pg.Surface = pg.display.set_mode((SCREEN_W, SCREEN_H))
        pg.display.set_caption(NAME)

        # Sets a transparent surface for text blit
        self.background_surface: pg.Surface = pg.Surface((SCREEN_W, SCREEN_H))
        self.transparent_surface: pg.Surface = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)

        # Sets clock for frame rate
        self.clock = pg.time.Clock()

        # Loading the necessary files to render later
        self.files = FileLoader()

        # Initializing game state to start for displaying the start screen
        self.state = GameState.START

        # Creating paddles and ball_shape
        self.left_paddle = Paddle(self.background_surface, _x_margin, _screen_centre[1] - PADDLE_H // 2)
        self.right_paddle = Paddle(self.background_surface, SCREEN_W - _x_margin - PADDLE_W,
                                   _screen_centre[1] - PADDLE_H // 2)
        self.ball = Ball(self.background_surface, _screen_centre[0] - BALL_SIZE // 2,
                         _screen_centre[1] - BALL_SIZE // 2)

        # Initializing the game with both players' score 0 then update as condition
        self.left_score: int = 0
        self.right_score: int = 0

        # Number of missing ball. If it reaches BALL_MISS_TIMEOUT then,
        # the game terminates and display the winner and scores
        self.ball_miss_times: int = 0

    def run(self):
        while True:
            self.event_handler()
            self.screen.blit(self.background_surface, (0, 0))
            self.update()
            self.draw_all()
            pg.display.update()
            self.clock.tick(60)

    def event_handler(self):
        # Getting all events
        for event in pg.event.get():

            # Quiting the game
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            # Handles game state changes
            if self.state == GameState.START:
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    self.state = GameState.RUNNING

    def score_cards(self):
        # Render the font with text, color
        player_a_text = self.files.text_font.render("Player: A", True, TEXT_COLOR)
        left_score_text = self.files.num_font.render(str(self.left_score), True, COLOR_DICTIONARY["Ball"])
        player_b_text = self.files.text_font.render("Player: B", True, TEXT_COLOR)
        right_score_text = self.files.num_font.render(str(self.right_score), True, COLOR_DICTIONARY["Ball"])

        # Places the texts on the screen
        self.background_surface.blit(left_score_text, (_x_margin, _x_margin))
        self.background_surface.blit(player_a_text, (_x_margin, _x_margin + left_score_text.get_height() + 0))
        self.background_surface.blit(right_score_text, (SCREEN_W - _x_margin - right_score_text.get_width(), _x_margin))
        self.background_surface.blit(player_b_text, (SCREEN_W - _x_margin - player_b_text.get_width(),
                                                     _x_margin + right_score_text.get_height() + 0))

    def draw_all(self):
        match self.state:
            case GameState.START:
                self.background_surface.blit(self.files.bg, (0, 0))
                self.background_surface.blit(self.files.banner,
                                             (_screen_centre[0] - self.files.banner.get_width() // 2,
                                              _screen_centre[1] - self.files.banner.get_height() // 2))
                subtitle = self.files.text_font.render("Press SPACE to Start", True, COLOR_DICTIONARY["Paddle"])
                self.background_surface.blit(subtitle, (_screen_centre[0] - subtitle.get_width() // 2, SCREEN_H - 50))

            case GameState.RUNNING:
                # Fills screen background with color
                self.background_surface.blit(self.files.bg, (0, 0))

                # Draws basic elements (Paddles, Ball) on the screen
                self.left_paddle.draw()
                self.right_paddle.draw()
                self.ball.draw()

                # Places the scorecards
                self.score_cards()

            case GameState.PAUSED:
                self.background_surface.blit(self.files.bg_rect,
                                             (_screen_centre[0] - self.files.bg_rect.get_width() // 2,
                                              _screen_centre[1] - self.files.bg_rect.get_height() // 2))
                self.next_move_countdown() if self.ball_miss_times != BALL_MISS_TIMEOUT else self.results()

    def next_move_countdown(self):
        for i in range(3, 0, -1):
            self.transparent_surface.fill((0, 0, 0, 0))
            cd_text = self.files.num_font.render(str(i), True, COLOR_DICTIONARY["Paddle"])
            self.transparent_surface.blit(cd_text, (_screen_centre[0] - cd_text.get_width() // 2,
                                                    _screen_centre[1] - cd_text.get_height() // 2))
            # First blit what it's in the background surface, then the transparent surface on top
            self.screen.blit(self.background_surface, (0, 0))
            self.screen.blit(self.transparent_surface, (0, 0))
            pg.display.update()
            time.sleep(1)

        self.ball_miss_times += 1
        self.state = GameState.RUNNING

    def results(self):
        pass

    def score_update(self):
        # If the ball touches the left wall, centres the ball and add one score to the opponent
        if self.ball.ball_shape.left <= 0:
            self.ball.reset()
            sfx.play_stop_sfx("wall_hit")
            self.right_score += 1
            self.state = GameState.PAUSED

        # If the ball touches the right wall, centres the ball and add one score to the opponent
        if self.ball.ball_shape.right >= SCREEN_W:
            self.ball.reset()
            sfx.play_stop_sfx("wall_hit")
            self.left_score += 1
            self.state = GameState.PAUSED

    def update(self):
        if self.state == GameState.RUNNING:
            # Gets keys from keyboard using PyGame
            keys = pg.key.get_pressed()

            # Moves all the elements on the screen as functioned earlier
            self.left_paddle.move(keys[pg.K_w], keys[pg.K_s])
            self.right_paddle.move(keys[pg.K_UP], keys[pg.K_DOWN])
            self.ball.move(self.left_paddle.paddle_shape, self.right_paddle.paddle_shape)

            # Updates the score
            self.score_update()


# Paddle class
class Paddle:
    def __init__(self, screen: pg.Surface, x_cord, y_cord) -> None:
        self.screen = screen

        # Creates an empty shape the paddle_shape
        self.paddle_shape = pg.Rect(x_cord, y_cord, PADDLE_W, PADDLE_H)

    def draw(self) -> None:
        # Draws the empty shape on the screen with color
        pg.draw.rect(self.screen, COLOR_DICTIONARY["Paddle"], self.paddle_shape)

    def move(self, up_key: bool, down_key: bool) -> None:

        # If up key pressed, the paddle_shape moves upward
        if up_key and self.paddle_shape.top > 0:
            self.paddle_shape.y -= PADDLE_SPEED

        # The paddle_shape moves downward for the down key pressed
        if down_key and self.paddle_shape.bottom < SCREEN_H:
            self.paddle_shape.y += PADDLE_SPEED


# Ball class
class Ball:
    def __init__(self, screen: pg.Surface, x_cord, y_cord) -> None:
        self.screen = screen

        # Creates an empty shape of the ball_shape
        self.ball_shape = pg.Rect(x_cord, y_cord, BALL_SIZE, BALL_SIZE)

        # For moving the ball_shape to the reverse direction later
        self.move_x = BALL_SPEED
        self.move_y = BALL_SPEED

    def draw(self) -> None:
        # Draws the empty shape on the screen with color
        pg.draw.ellipse(self.screen, COLOR_DICTIONARY["Ball"], self.ball_shape)

    def move(self, l_paddle: pg.Rect, r_paddle: pg.Rect) -> None:
        """
        Helps to move the ball_shape over the screen (including check for Paddle collision
        and respective/proper moving direction).

        To check for collision and change moving direction accordingly, give it two parameters:
        :param l_paddle: Left Paddle (pg.Rect)
        :type l_paddle: PyGame.Rect
        :param r_paddle: Right Paddle (pg.Rect)
        :type r_paddle: PyGame.Rect
        :return: None
        """

        global _l_paddle_cord

        # Moves the ball_shape with the speed and direction
        self.ball_shape.x += self.move_x
        self.ball_shape.y += self.move_y

        # If the ball_shape touches the top and the bottom wall, then it moves vertically reverse direction
        if self.ball_shape.top <= 0 or self.ball_shape.bottom >= SCREEN_H:
            self.move_y *= -1
            sfx.play_stop_sfx("wall_hit")
        # Left and right wall collision of the ball_shape should be implemented later
        # to update the score(s) simultaneously.

        # If the ball_shape touches the left and right paddle_shape, then also it moves horizontally reverse direction
        if self.ball_shape.colliderect(l_paddle) or self.ball_shape.colliderect(r_paddle):
            self.move_x *= -1
            sfx.play_stop_sfx("paddle_hit")

    def reset(self) -> None:
        # Place the ball_shape to the centre of the screen
        self.ball_shape.x = _screen_centre[0] - BALL_SIZE // 2
        self.ball_shape.y = _screen_centre[1] - BALL_SIZE // 2

        # Change the ball_shape's moving direction to the opposite of before
        self.move_x *= -1


if __name__ == '__main__':
    game = PongGame()
    game.run()
