# IMPORTS

import time
import pygame as pg
import sys

# GLOBAL VARIABLES

NAME: str = "PONG"
PLAYERS: tuple[str, str] = ("Player A", "Player B")
SCREEN_H: int = 600
SCREEN_W: int = 800
PADDLE_W: int = 10
PADDLE_H: int = 100
BALL_SIZE: int = 15
BALL_SPEED: int = 4
PADDLE_SPEED: int = 10
BALL_MISS_TIMEOUT: int = 5
COLOR_DICTIONARY: dict[str: tuple[int, int, int]] = {
    # Primary Colors
    "White": (255, 255, 255),
    "Light Grey": (200, 200, 200),
    "Grey": (100, 100, 100),
    "Dark Grey": (50, 50, 50),
    "Black": (0, 0, 0),
    "Red": (255, 0, 0),
    "Yellow": (255, 255, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
    # Elements' colors
    "Paddle": (255, 255, 255),
    "Ball": (255, 65, 0)
}
SOUND_EFFECTS: dict[str: str | bytes] = {
    "wall_hit": "./sources/SFX/paddle-hit-2.mp3",
    "paddle_hit": "./sources/SFX/paddle-hit-1.mp3",
    "hit_miss": "./sources/SFX/miss.wav",
    "tick": "./sources/SFX/ticks.wav",
    "game_over": "./sources/SFX/game-over.wav",
    "result": "./sources/SFX/result.wav",
}

# DERIVED VARIABLES

_screen_centre: tuple[int, int] = (SCREEN_W // 2, SCREEN_H // 2)
_x_margin: int = 50


# CLASS FOR LOADING OF IMAGES AND FONTS

class FileLoader:
    def __init__(self):
        # Loads font files
        self.num_font = pg.font.Font("./sources/Fonts/RobotoCondensed-Bold.ttf", 25)
        self.text_font = pg.font.Font("./sources/Fonts/RobotoCondensed-Regular.ttf", 15)

        # Load image files
        self.icon = pg.image.load("./sources/icon.png")
        self.banner = pg.image.load("./sources/banner.png")
        self.bg = pg.image.load("./sources/bg.png")
        self.bg_rect = pg.image.load("./sources/bg_rectangle.png")
        self.winner_batch = pg.image.load("./sources/winner_batch.png")
        self.btn_replay = pg.image.load("./sources/btn_replay.png")


# CLASS FOR SOUND MANAGEMENT

class SoundManager:
    """
    Manages background music and SFXs.
    """

    def __init__(self, sfx_files: dict[str: str | bytes]) -> None:
        # Initializes the PyGame audio
        pg.mixer.init()

        # Loads sound effects from the given dictionary of sound names and paths
        self.sound_effects = {name: pg.mixer.Sound(path) for name, path in sfx_files.items()}

    def play_stop_sfx(self, name: str, play: bool = True) -> None:
        """
        Plays or stops SFX with the name provided as an argument.

        :param name: Name of the SFX as provided in the SOUND_EFFECTS global variable.
        :param play: (Optional, Default: True) If False, it stop playing the sound.
        :return: None
        """
        if name in self.sound_effects:
            self.sound_effects[name].play() if play else self.sound_effects[name].stop()


# CLASS FOR GAME STATE

class GameState:
    START = 1
    RUNNING = 2
    PAUSED = 3
    OVER = 4
    HOLD = 5


# Loads audios
sfx = SoundManager(SOUND_EFFECTS)


# CLASS FOR MAIN GAMING CONTROL

class PongGame:
    def __init__(self):
        pg.init()

        # Loading the necessary files to render later
        self.files = FileLoader()

        self.screen: pg.Surface = pg.display.set_mode((SCREEN_W, SCREEN_H))
        pg.display.set_caption(NAME)
        pg.display.set_icon(self.files.icon)

        # Sets a transparent surface for text blit
        self.background_surface: pg.Surface = pg.Surface((SCREEN_W, SCREEN_H))
        self.transparent_surface: pg.Surface = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)

        # Sets clock for frame rate
        self.clock = pg.time.Clock()

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

        # Global elements
        self._btn_replay: pg.Rect | None = None
        self._result_sfx_play: bool = False

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
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit()
            elif self.state == GameState.RUNNING:
                if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE or event.key == pg.K_SPACE):
                    self.state = GameState.HOLD
            elif self.state == GameState.HOLD:
                if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE or event.key == pg.K_SPACE):
                    self.state = GameState.RUNNING
            elif self.state == GameState.OVER:
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    self.state = GameState.START
                elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    # If replay button is pressed from the result screen
                    if self._btn_replay.collidepoint(event.pos):
                        self.state = GameState.START

    def score_cards(self):
        # Render the font with text, color
        player_a_text = self.files.text_font.render(PLAYERS[0], True, COLOR_DICTIONARY["Grey"])
        left_score_text = self.files.num_font.render(str(self.left_score), True, COLOR_DICTIONARY["Ball"])
        player_b_text = self.files.text_font.render(PLAYERS[1], True, COLOR_DICTIONARY["Grey"])
        right_score_text = self.files.num_font.render(str(self.right_score), True, COLOR_DICTIONARY["Ball"])

        # Places the texts on the screen
        self.background_surface.blit(left_score_text, (_x_margin, _x_margin))
        self.background_surface.blit(player_a_text, (_x_margin, _x_margin + left_score_text.get_height()))
        self.background_surface.blit(right_score_text, (SCREEN_W - _x_margin - right_score_text.get_width(), _x_margin))
        self.background_surface.blit(player_b_text, (SCREEN_W - _x_margin - player_b_text.get_width(),
                                                     _x_margin + right_score_text.get_height()))

    def draw_all(self):
        # Game state management
        match self.state:
            case GameState.START:
                # Resetting all the values to zeros
                self.left_score = self.right_score = self.ball_miss_times = 0
                self._result_sfx_play = False

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

            case GameState.HOLD:
                self.transparent_surface.fill((0, 0, 0, 0))
                _t1 = self.files.num_font.render("PAUSED", True, COLOR_DICTIONARY["Ball"])
                _t2 = self.files.text_font.render("Press SPACE or ESC to resume", True, COLOR_DICTIONARY["Ball"])
                self.transparent_surface.blit(_t1, (_screen_centre[0] - _t1.get_width() // 2,
                                                    _screen_centre[1] - _t1.get_height() // 2 - _t2.get_height() // 2))
                self.transparent_surface.blit(_t2, (_screen_centre[0] - _t2.get_width() // 2,
                                                    _screen_centre[1] - _t2.get_height() // 2 + _t1.get_height() // 2))
                self.screen.blit(self.transparent_surface, (0, 0))

            case GameState.PAUSED:
                self.background_surface.blit(self.files.bg_rect,
                                             (_screen_centre[0] - self.files.bg_rect.get_width() // 2,
                                              _screen_centre[1] - self.files.bg_rect.get_height() // 2))
                self.next_move_countdown()

            case GameState.OVER:
                self.results()

    def next_move_countdown(self):
        self.ball_miss_times += 1

        for i in range(3, 0, -1):
            if self.ball_miss_times != BALL_MISS_TIMEOUT and i == 3:
                sfx.play_stop_sfx("tick")

            self.transparent_surface.fill((0, 0, 0, 0))
            # Setting text and font color
            tc = (str(i), COLOR_DICTIONARY["Dark Grey"]) if self.ball_miss_times != 5 else ("GAME OVER",
                                                                                            COLOR_DICTIONARY["Red"])
            cd_text = self.files.num_font.render(tc[0], True, tc[1])
            help_text = self.files.text_font.render(f"{self.ball_miss_times} Ball Missed. "
                                                    f"({BALL_MISS_TIMEOUT - self.ball_miss_times} Left)", True,
                                                    tc[1] if self.ball_miss_times < 3 else COLOR_DICTIONARY["Ball"])
            self.transparent_surface.blit(
                cd_text, (_screen_centre[0] - cd_text.get_width() // 2,
                          _screen_centre[1] - cd_text.get_height() // 2 - help_text.get_height() // 1.5))
            self.transparent_surface.blit(
                help_text, (_screen_centre[0] - help_text.get_width() // 2,
                            _screen_centre[1] - help_text.get_height() // 2 + help_text.get_height() // 1.5))

            # First blit what it's in the background surface, then the transparent surface on top
            self.screen.blit(self.background_surface, (0, 0))
            self.screen.blit(self.transparent_surface, (0, 0))
            pg.display.update()
            time.sleep(1)

            # If the number of missing ball crosses BALL_MISS_TIMEOUT then,
            if self.ball_miss_times == BALL_MISS_TIMEOUT:
                self.state = GameState.OVER
                break
            else:
                self.state = GameState.RUNNING

    def results(self):
        if not self._result_sfx_play:
            sfx.play_stop_sfx("result")
            self._result_sfx_play = True

        self.background_surface.blit(self.files.bg, (0, 0))
        self.background_surface.blit(self.files.winner_batch,
                                     (_screen_centre[0] - self.files.winner_batch.get_width() // 2, 0))
        _b1 = self._btn_replay = self.background_surface.blit(
            self.files.btn_replay, (_screen_centre[0] - self.files.btn_replay.get_width() // 2,
                                    SCREEN_H - self.files.btn_replay.get_height() - 50))
        subtitle = self.files.text_font.render("or, Press SPACE to Start", True, COLOR_DICTIONARY["Dark Grey"])
        self.background_surface.blit(subtitle, (_screen_centre[0] - subtitle.get_width() // 2, _b1.bottom + 10))

        if self.left_score > self.right_score:
            winner = f"{PLAYERS[0]}, Congratulations!"
        elif self.right_score > self.left_score:
            winner = f"{PLAYERS[1]}, Congratulations!"
        else:
            winner = "MATCH DRAW"
        _text1 = self.files.num_font.render(winner, True, COLOR_DICTIONARY["Yellow"])
        _text2 = self.files.text_font.render("Well Played! Keep It Up!", True, COLOR_DICTIONARY["Grey"])
        _t1 = self.background_surface.blit(_text1, (_screen_centre[0] - _text1.get_width() // 2,
                                                    self.files.winner_batch.get_height() + 20))
        self.background_surface.blit(_text2, (_screen_centre[0] - _text2.get_width() // 2, _t1.bottom + 10))

    def score_update(self):
        # If the ball touches the left wall, centres the ball and add one score to the opponent
        if self.ball.ball_shape.left <= 0:
            self.ball.reset()
            sfx.play_stop_sfx("wall_hit")
            sfx.play_stop_sfx("hit_miss")
            self.right_score += 1
            self.state = GameState.PAUSED

        # If the ball touches the right wall, centres the ball and add one score to the opponent
        if self.ball.ball_shape.right >= SCREEN_W:
            self.ball.reset()
            sfx.play_stop_sfx("wall_hit")
            sfx.play_stop_sfx("hit_miss")
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


# CLASS FOR MAKING AND MOVING THE TWO PADDLES

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


# CLASS FOR MAKING AND MOVING THE BALL

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
