import sys

import pygame
from pygame.locals import *


pygame.init()

fps = 60
fpsClock = pygame.time.Clock()

width, height = 640, 480
screen = pygame.display.set_mode((width, height))

with open("file.FCODE", "r") as f:
    instructions = f.read().split("\n")
    f.close()



# Game loop.
while True:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # Update.

    # Draw.

    pygame.display.flip()
    fpsClock.tick(fps)