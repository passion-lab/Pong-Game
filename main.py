# IMPORTS

import time
import pygame as pg
import sys
from os import path
from typing import Literal



# ---
# >> IMPORTANT: PATH ISSUE FIXED
# Base path determination dynamically (required for .exe done with PyInstaller)
if getattr(sys, 'frozen', False):
    # Running as an executable where PyInstaller extract files/dirs (`_internal`)
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = path.dirname(path.abspath(__file__))
# ---



# GLOBAL VARIABLES

NAME: str = "PONG Game ○ Passion-Lab"
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
SOURCE_PATH: str = path.join(BASE_PATH, "sources")
SOUND_EFFECTS: dict[str: str | bytes] = {
    "wall_hit": f"{SOURCE_PATH}/SFX/paddle-hit-2.mp3",
    "paddle_hit": f"{SOURCE_PATH}/SFX/paddle-hit-1.mp3",
    "hit_miss": f"{SOURCE_PATH}/SFX/miss.wav",
    "tick": f"{SOURCE_PATH}/SFX/ticks.wav",
    "game_over": f"{SOURCE_PATH}/SFX/game-over.wav",
    "result": f"{SOURCE_PATH}/SFX/result.wav",
    "bg_music": f"{SOURCE_PATH}/SFX/background-music.mp3"  # Background music file path
}

# DERIVED VARIABLES

_screen_centre: tuple[int, int] = (SCREEN_W // 2, SCREEN_H // 2)
_x_margin: int = 50



# CLASS FOR LOADING OF IMAGES AND FONTS

class FileLoader:
    """
    Loads and manages all the necessary files for the game.
    """

    def __init__(self):
        # Loads font files
        self.num_font = pg.font.Font(f"{SOURCE_PATH}/Fonts/RobotoCondensed-Bold.ttf", 25)
        self.text_font = pg.font.Font(f"{SOURCE_PATH}/Fonts/RobotoCondensed-Regular.ttf", 15)

        # Load image files
        self.icon = pg.image.load(f"{SOURCE_PATH}/icon.png")
        self.banner = pg.image.load(f"{SOURCE_PATH}/banner.png")
        self.bg = pg.image.load(f"{SOURCE_PATH}/bg.png")
        self.bg_rect = pg.image.load(f"{SOURCE_PATH}/bg_rectangle.png")
        self.winner_batch = pg.image.load(f"{SOURCE_PATH}/winner_batch.png")
        self.btn_replay = pg.image.load(f"{SOURCE_PATH}/btn_replay.png")
        self.pong_ball = pg.image.load(f"{SOURCE_PATH}/pong_ball.png")


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

        # Set up background music
        if "bg_music" in self.sound_effects:
            self.sound_effects["bg_music"].set_volume(0.5)
            self.is_background_play: bool = False

    def play_stop_sfx(self, name: str, play: bool = True) -> None:
        """
        Plays or stops SFX with the name provided as an argument.

        :param name: Name of the SFX as provided in the SOUND_EFFECTS global variable.
        :param play: (Optional, Default: True) If False, it stop playing the sound.
        :return: None
        """
        if name in self.sound_effects:
            self.sound_effects[name].play() if play else self.sound_effects[name].stop()

    def play_bg_music(self, play: bool = True, volume: int | None = None) -> None:
        """
        Plays the background music in a loop if not already played.
        
        :return: None
        """

        if "bg_music" in self.sound_effects:
            if play and not self.is_background_play:
                self.sound_effects["bg_music"].play(loops=-1)
                self.is_background_play = True
            elif not play and self.is_background_play:
                self.sound_effects["bg_music"].stop()
                self.is_background_play = False

            if volume:
                self.sound_effects["bg_music"].set_volume(volume)
            

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
    """
    Main game controller class for the Pong game implementation.

    This class handles:
    - Game initialization and setup
    - Game state management (Start, Running, Paused, Over, Hold)
    - Screen rendering and display
    - Score tracking and updates
    - Event handling (keyboard/mouse inputs)
    - Game loop control
    - Collision detection and physics
    - Sound effect management
    - Player interaction and UI elements

    The class serves as the central coordinator for all game components including:
    - Paddles (left and right)
    - Ball movement and physics
    - Score display
    - Game states and transitions
    - Visual effects and animations
    """
    
    def __init__(self):
        pg.init()

        # Loading the necessary files to render later
        self.files = FileLoader()

        self.screen: pg.Surface = pg.display.set_mode((SCREEN_W, SCREEN_H))  # pg.RESIZABLE argument for resizing the window
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
        # Give pong ball image as the last parameter to render the ball from the image (if needed)
        self.ball = Ball(self.background_surface, _screen_centre[0] - BALL_SIZE // 2,
                         _screen_centre[1] - BALL_SIZE // 2)

        # Initializing the game with both players' score 0 then update as condition
        self.left_score: int = 0
        self.right_score: int = 0

        # Rotation angle for ball image (if given)
        self.ball_rotation: float = 0

        # Number of missing ball. If it reaches BALL_MISS_TIMEOUT then,
        # the game terminates and display the winner and scores
        self.ball_miss_times: int = 0

        # Global elements
        self._btn_replay: pg.Rect | None = None
        self._result_sfx_play: bool = False

    def run(self):
        """
        Main game loop that runs continuously until the game is closed.
        
        This method:
        - Handles the core game loop
        - Updates the game state and screen
        - Manages frame rate
        - Renders all game elements
        
        The loop performs the following operations each frame:
        1. Processes all game events
        2. Updates the screen with background
        3. Updates game state and object positions
        4. Draws all game elements
        5. Refreshes the display
        6. Maintains consistent 60 FPS
        
        Returns:
            None
        """

        while True:
            self.event_handler()
            self.screen.blit(self.background_surface, (0, 0))
            self.update()
            self.draw_all()
            pg.display.update()
            self.clock.tick(60)

    def event_handler(self):
        """
        Handles all game events and user inputs to manage game state transitions.

        This method processes PyGame events including:
        - Window close events (X button)
        - Keyboard inputs (Space, Escape)
        - Mouse clicks (for replay button)
        
        Game state transitions:
        - START state:
            - SPACE -> RUNNING state
            - ESC -> No effect
        - RUNNING state:
            - SPACE/ESC -> HOLD state
        - HOLD state:
            - SPACE/ESC -> RUNNING state
        - OVER state:
            - SPACE -> START state
            - ESC -> Quit game
            - Click replay button -> START state

        Returns:
            None
        """
        
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
                    pass
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
                    pg.mixer.quit()
                    pg.quit()
                    sys.exit()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    # If replay button is pressed from the result screen
                    if self._btn_replay.collidepoint(event.pos):
                        self.state = GameState.START

    def score_cards(self):
        """
        Renders and displays the score cards for both players on the game screen.

        This method:
        - Renders player names and their current scores using the game fonts
        - Positions the score elements in the top corners of the screen
        - Left player (Player A) score is shown in top-left
        - Right player (Player B) score is shown in top-right
        - Player names are displayed below their respective scores
        - Uses predefined colors from COLOR_DICTIONARY for consistent styling

        The layout is:
        Top-left:          Top-right:
        [Score A]          [Score B]
        [Player A]         [Player B]

        Returns:
            None
        """
        
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
        """
        Renders all game elements based on the current game state.

        This method handles the drawing of different game screens and elements depending
        on the current state of the game (START, RUNNING, HOLD, PAUSED, or OVER).

        For each state:
        - START: Displays the welcome screen with game banner and start instructions
        - RUNNING: Shows the active gameplay with paddles, ball, and score
        - HOLD: Overlays a pause message on the current game screen
        - PAUSED: Displays countdown or game over message between ball resets
        - OVER: Shows the final game results and winner announcement

        The method uses various surfaces to handle:
        - Background elements (self.background_surface)
        - Transparent overlays (self.transparent_surface)
        - Dynamic text rendering
        - UI elements like buttons and banners

        Returns:
            None
        """

        # Game state management
        match self.state:
            case GameState.START:
                # Start/resume background music for welcome screen
                sfx.play_bg_music()

                # Resetting all the values to zeros
                self.left_score = self.right_score = self.ball_miss_times = 0
                self._result_sfx_play = False

                # todo: Blank top space for score and other rendering
                # top = pg.Rect((0, 0, SCREEN_W, SCREEN_H))
                # t1= pg.draw.rect(self.background_surface, COLOR_DICTIONARY["White"], top)
                self.background_surface.blit(self.files.bg, (0, 0))
                self.background_surface.blit(self.files.banner,
                                             (_screen_centre[0] - self.files.banner.get_width() // 2,
                                              _screen_centre[1] - self.files.banner.get_height() // 2))
                
                subtitle = self.files.text_font.render("Press SPACE to Start", True, COLOR_DICTIONARY["Paddle"])
                self.background_surface.blit(subtitle, (_screen_centre[0] - subtitle.get_width() // 2, SCREEN_H - 50))

            case GameState.RUNNING:
                # Stop background music for gameplay
                sfx.play_bg_music(play=False)

                # Fills screen background with color
                self.background_surface.blit(self.files.bg, (0, 0))

                # Draws basic elements (Paddles, Ball) on the screen
                self.left_paddle.draw()
                self.right_paddle.draw()
                self.ball.draw()  # add rotation angle if ball image is given

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
                # Resumes the background music for result screen
                sfx.play_bg_music()

                self.results()

    def next_move_countdown(self):
        """
        Displays a countdown timer between ball resets and manages game state transitions.

        This method:
        - Increments the ball miss counter
        - Shows a 3-2-1 countdown animation between plays
        - Displays the number of balls missed and remaining
        - Plays appropriate sound effects
        - Handles the transition to GAME OVER state when max misses reached
        
        The countdown is displayed on a transparent overlay with:
        - Countdown numbers in the center
        - Ball miss status below the numbers
        - Different colors based on game state (normal vs game over)
        
        State Transitions:
        - If ball_miss_times < BALL_MISS_TIMEOUT: 
            Returns to RUNNING state after countdown
        - If ball_miss_times == BALL_MISS_TIMEOUT: 
            Transitions to OVER state
        
        Returns:
            None
        """
        
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
        """
        Displays the game results screen showing the winner and final scores.

        This method:
        - Plays the result sound effect (only once)
        - Renders the background and winner batch image
        - Displays the replay button and space bar instruction
        - Shows the winner announcement based on final scores
        - Includes congratulatory messages and visual elements

        The results screen contains:
        - Winner batch graphic at the top
        - Winner announcement with player name
        - Congratulatory message
        - Replay button
        - Alternative space bar instruction

        State Management:
        - Tracks if result sound effect has been played
        - Stores replay button rectangle for click detection

        Returns:
            None
        """
        
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
        """
        Updates the game score and manages ball reset when it hits the side walls.

        This method:
        - Checks if the ball hits either the left or right wall
        - Increments the appropriate player's score when a point is scored
        - Resets the ball position to center
        - Plays appropriate sound effects (wall hit and miss sounds)
        - Changes game state to PAUSED for the countdown sequence

        Score Updates:
        - Left wall hit: Right player (Player B) scores a point
        - Right wall hit: Left player (Player A) scores a point

        State Changes:
        - Changes game state to PAUSED after each point
        - Triggers countdown sequence before next play

        Sound Effects:
        - Plays wall hit sound
        - Plays ball miss sound

        Returns:
            None
        """
        
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
        """
        Updates the game state and object positions during active gameplay.

        This method is called each frame during the game loop when the game state 
        is RUNNING. It handles:
        - Getting current keyboard input state
        - Updating paddle positions based on player input
        - Moving the ball and handling collisions
        - Rotating the ball for visual effect
        - Updating scores when points are scored

        State Requirements:
            - Only executes when self.state == GameState.RUNNING
            - Uses pg.key.get_pressed() for keyboard input
            - Updates left paddle (W/S keys), right paddle (UP/DOWN keys)
            - Updates ball position and collisions
            - Increments ball rotation angle
            - Calls score_update() to handle scoring

        Returns:
            None
        """
        
        if self.state == GameState.RUNNING:
            # Gets keys from keyboard using PyGame
            keys = pg.key.get_pressed()

            # Moves all the elements on the screen as functioned earlier
            self.left_paddle.move(keys[pg.K_w], keys[pg.K_s])
            self.right_paddle.move(keys[pg.K_UP], keys[pg.K_DOWN])
            self.ball.move(self.left_paddle.paddle_shape, self.right_paddle.paddle_shape)

            self.ball_rotation += 5

            # Updates the score
            self.score_update()


# CLASS FOR MAKING AND MOVING THE TWO PADDLES

class Paddle:
    """
    A class representing a paddle in the Pong game.

    This class handles the creation, rendering, and movement of paddles that players
    use to hit the ball. Each paddle is a rectangular shape that can move vertically
    within the game screen boundaries.

    Attributes:
        screen (pg.Surface): The game surface where the paddle will be drawn
        paddle_shape (pg.Rect): The rectangular shape representing the paddle

    Methods:
        draw(): Renders the paddle on the screen
        move(up_key, down_key): Moves the paddle up or down based on key inputs
    """

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
    """
    A class representing the ball in the Pong game.

    This class handles the creation, rendering, movement and collision detection of the game ball.
    The ball can be rendered either as a basic circle shape or using a provided image.
    It moves across the screen and bounces off paddles and screen boundaries.

    Attributes:
        screen (pg.Surface): The game surface where the ball will be drawn
        ball_image (pg.Surface | None): Optional image surface for the ball
        ball_shape (pg.Rect): The rectangular shape representing the ball's hitbox
        move_x (int): Horizontal movement speed and direction
        move_y (int): Vertical movement speed and direction

    Methods:
        draw(angle): Renders the ball on screen, optionally with rotation
        move(l_paddle, r_paddle): Updates ball position and handles collisions
        reset(): Resets ball to center position
    """

    def __init__(self, screen: pg.Surface, x_cord, y_cord, ball_image: pg.Surface | None = None) -> None:
        self.screen = screen
        self.ball_image = ball_image

        # Gets ball image's rect if image surface is given or, Creates an empty shape of the ball_shape
        self.ball_shape = self.ball_image.get_rect() if self.ball_image else pg.Rect(x_cord, y_cord, BALL_SIZE, BALL_SIZE)

        # For moving the ball_shape to the reverse direction later
        self.move_x = BALL_SPEED
        self.move_y = BALL_SPEED

    def draw(self, angle: float | None = None) -> None:
        if self.ball_image:
            if angle:
                rotated_image = pg.transform.rotate(self.ball_image, angle=angle)
                rotation_center = rotated_image.get_rect(center=self.ball_shape.center)
                self.screen.blit(rotated_image, rotation_center)
            else:
                # Renders the ball image if given
                self.screen.blit(self.ball_image, (self.ball_shape.x, self.ball_shape.y))
        else:
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
