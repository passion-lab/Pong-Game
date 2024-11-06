# """
import pygame

pygame.init()

bg = pygame.image.load("./sources/bg.png")

# Set up display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Surface Switching')
font = pygame.font.Font(None, 74)
WHITE = (255, 255, 255)
BLACK = (0, 220, 110)
RED = (255, 0, 0)

# Create surfaces
background_surface = pygame.Surface((800, 600))  # Main background surface
text_surface = pygame.Surface((800, 600), pygame.SRCALPHA)  # Transparent text surface

# Fill the background surface with a color
background_surface.fill(BLACK)

# Main game loop
running = True
counter = 5
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the text surface (make it transparent)
    text_surface.fill((0, 0, 0, 0))  # Fill the surface with full transparency

    # Render the text onto the transparent surface
    text = font.render(str(counter), True, RED)
    text_surface.blit(text, (300, 250))

    # Blit the background surface first, then the text surface on top
    background_surface.blit(bg, (0, 0))
    screen.blit(background_surface, (0, 0))
    screen.blit(text_surface, (0, 0))

    # Update the screen
    pygame.display.update()

    pygame.time.delay(1000)
    counter -= 1
    if counter < 0:
        counter = 5

pygame.quit()

"""

import pygame

pygame.init()

# Set up display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Using Transparency Example')
font = pygame.font.Font(None, 74)
WHITE = (255, 255, 255)

# Create a transparent surface with SRCALPHA
transparent_surface = pygame.Surface((800, 600), pygame.SRCALPHA)

# Main game loop
running = True
alpha_value = 255  # Start with full opacity
fade_out = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the surface with transparency
    transparent_surface.fill((0, 0, 0, 0))  # Fully transparent

    # Blit some text on the transparent surface
    text = font.render("Hello", True, WHITE)
    transparent_surface.blit(text, (300, 250))

    # Set the alpha value for transparency
    transparent_surface.set_alpha(alpha_value)

    # Blit the transparent surface onto the main screen
    screen.fill((0, 0, 0))  # Fill the screen with black
    screen.blit(transparent_surface, (0, 0))

    pygame.display.update()

    # Adjust the alpha value to create a fade-in/fade-out effect
    if fade_out:
        alpha_value -= 5
    else:
        alpha_value += 5

    if alpha_value >= 255:
        fade_out = True
    elif alpha_value <= 0:
        fade_out = False

    pygame.time.delay(50)

pygame.quit()

"""
