import pygame
import math
from camera import Camera
import constants as c

class Background:

    def __init__(self):
        surf = pygame.image.load("assets/images/arena.png")
        self.tile_size = (200, 200)
        tile_size = self.tile_size
        tiles_wide = math.ceil(surf.get_width()/tile_size[0])
        tiles_high = math.ceil(surf.get_height()/tile_size[1])
        self.tiles = []
        for y in range(tiles_high):
            row = []
            ypix = y * tile_size[1]
            for x in range(tiles_wide):
                xpix = x * tile_size[0]
                tile_surf = pygame.Surface(tile_size)
                tile_surf.blit(surf,(0, 0),(xpix, ypix, tile_size[0], tile_size[1]))
                row.append(tile_surf.convert())
            self.tiles.append(row)

    def draw(self, surface, offset=(0, 0)):
        for y, row in enumerate(self.tiles):
            for x, tile_surf in enumerate(row):
                xpix = x * self.tile_size[0] - offset[0]
                ypix = y * self.tile_size[1] - offset[1]
                if xpix < -self.tile_size[0] or xpix > c.WINDOW_WIDTH + self.tile_size[0]:
                    continue
                if ypix < -self.tile_size[1] or ypix > c.WINDOW_HEIGHT + self.tile_size[1]:
                    continue
                surface.blit(tile_surf, (xpix, ypix))