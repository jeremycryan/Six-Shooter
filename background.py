import pygame
import math
from camera import Camera
import constants as c
from primitives import Pose
import random


class Cloud:

    def __init__(self, surf, position=(0, 0)):
        self.surf = surf
        self.position = Pose(position)
        self.velocity = Pose((-20, 0))

    def update(self, dt, events):
        self.position += self.velocity*dt

    def draw(self, surface, offset=(0, 0)):
        w = self.surf.get_width()
        h = self.surf.get_height()
        x = self.position.x - offset[0] - w//2
        y = self.position.y - offset[1] - h//2

        if x < -w or x > c.WINDOW_WIDTH:
            return
        if y < -h or y > c.WINDOW_HEIGHT:
            return

        in_world = Camera.screen_to_world(self.position.get_position())
        if w//2 < in_world.x < c.ARENA_WIDTH - w//2:
            if h//2 < in_world.y < c.ARENA_HEIGHT - h//2:
                return

        surface.blit(self.surf, (x, y))

class Background:

    def __init__(self):
        surf = pygame.image.load("assets/images/background.png")
        self.background_background = pygame.image.load("assets/images/distant_background.png")
        self.tile_size = (200, 200)
        self.cloud_images = [
            pygame.image.load(f"assets/images/cloud {num}.png") for num in range(1,10)
        ]
        self.clouds = []

        self.since_cloud = 0
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
                tile_surf.fill((255, 0, 255))
                tile_surf.blit(surf,(0, 0),(xpix, ypix, tile_size[0], tile_size[1]))
                row.append(tile_surf)
                tile_surf.set_colorkey((255, 0, 255))
            self.tiles.append(row)
        for i in range(120):
            self.update(1, [])

    def draw(self, surface, offset=(0, 0)):
        surface.blit(self.background_background, (0, 0))
        for cloud in self.clouds:
            cloud.draw(surface, (0, 0))
        for y, row in enumerate(self.tiles):
            for x, tile_surf in enumerate(row):
                xpix = x * self.tile_size[0] - offset[0] - 400
                ypix = y * self.tile_size[1] - offset[1] - 300
                if xpix < -self.tile_size[0] or xpix > c.WINDOW_WIDTH + self.tile_size[0]:
                    continue
                if ypix < -self.tile_size[1] or ypix > c.WINDOW_HEIGHT + self.tile_size[1]:
                    continue
                surface.blit(tile_surf, (xpix, ypix))

    def update(self, dt, events):
        self.since_cloud += dt
        while self.since_cloud > 5:
            self.since_cloud -= 5
            image = random.choice(self.cloud_images)
            image = pygame.transform.scale(image, (image.get_width()*0.5, image.get_height()*0.5))
            image.set_colorkey((255, 0, 195))
            image.set_alpha(100)
            self.clouds.append(Cloud(image, (c.WINDOW_WIDTH, random.random() * c.WINDOW_HEIGHT)))
        for cloud in self.clouds[:]:
            cloud.update(dt, events)
            if cloud.position.x < -500:
                self.clouds.remove(cloud)