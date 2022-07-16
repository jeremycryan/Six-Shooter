from player import Player
from camera import Camera
import constants as c
import pygame
from background import Background

class Frame:
    def __init__(self):
        self.done = False

    def load(self):
        pass

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        surface.fill((0, 0, 0))

    def next_frame(self):
        return Frame()


class GameFrame(Frame):
    def __init__(self):
        super().__init__()
        self.player = Player(self)
        self.particles = []
        self.projectiles = []
        self.background = Background()

    def update(self, dt, events):
        self.player.update(dt, events)

        keep_particles = []
        for particle in self.particles:
            particle.update(dt, events)
            if not particle.destroyed:
                keep_particles.append(particle)
        self.particles = keep_particles

        keep_projectiles = []
        for projectile in self.projectiles:
            projectile.update(dt, events)
            if not projectile.destroyed:
                keep_projectiles.append(projectile)
        self.projectiles = keep_projectiles

    def draw(self, surface, offset=(0, 0)):
        surface.fill((0, 0, 0))
        offset = Camera.position.get_position()
        self.background.draw(surface, offset)
        for particle in self.particles:
            if particle.layer == c.BACKGROUND:
                particle.draw(surface, offset=offset)
        for projectile in self.projectiles:
            projectile.draw(surface, offset=offset)
        self.player.draw(surface, offset=(offset))
        for particle in self.particles:
            if particle.layer == c.FOREGROUND:
                particle.draw(surface, offset=offset)

    def next_frame(self):
        return Frame()