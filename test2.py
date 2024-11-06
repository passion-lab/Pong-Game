import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Button Example")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Define button properties
button_rect = pygame.Rect(300, 250, 200, 100)  # x, y, width, height
button_color = GREEN
button_hover_color = (0, 200, 0)

# Function to be called when the button is pressed
def button_function():
    print("Button Pressed!")

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                if button_rect.collidepoint(event.pos):  # Check if mouse is over the button
                    button_function()  # Call the function

    # Fill the screen with white
    screen.fill(WHITE)

    # Draw the button
    mouse_pos = pygame.mouse.get_pos()
    if button_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, button_hover_color, button_rect)  # Change color on hover
    else:
        pygame.draw.rect(screen, button_color, button_rect)

    # Optionally, draw button text
    font = pygame.font.Font(None, 36)
    text_surface = font.render('Click Me!', True, BLACK)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
sys.exit()
