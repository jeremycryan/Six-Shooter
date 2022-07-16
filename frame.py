from player import Player
from camera import Camera
import constants as c
import pygame
from background import Background
from primitives import Pose
import math
from particle import SparkParticle

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

    def load(self):
        self.player = Player(self)
        self.particles = []
        self.projectiles = []
        self.background = Background()
        self.red_flash = pygame.Surface(c.WINDOW_SIZE)
        self.red_flash.fill((255, 0, 0))
        self.red_flash_alpha = 0
        self.shake_amp = Pose((0, 0))
        self.since_shake = 0

    def update(self, dt, events):
        self.player.update(dt, events)
        self.since_shake += dt

        self.shake_amp *= 0.1**dt
        new_mag = self.shake_amp.magnitude() - 50*dt
        if new_mag > 0:
            self.shake_amp.scale_to(new_mag)
        else:
            self.shake_amp = Pose((0, 0))


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

        self.red_flash_alpha -= 5 * dt
        self.red_flash_alpha *= 0.03**dt
        if self.player.weapon_mode == c.FIRE and self.player.firing and int(self.player.hand_sprite.get_frame_num()) == 7 and self.red_flash_alpha < 10:
            self.red_flash_alpha = 255
            self.shake(direction=None, amt=30)
            for i in range(16):
                position = self.player.hand_sprite.x, self.player.hand_sprite.y
                self.particles.append(SparkParticle(position))

    def draw(self, surface, offset=(0, 0)):
        surface.fill((0, 0, 0))
        offset = Camera.position
        screenshake = Pose((self.shake_amp.x * math.cos(self.since_shake * 35), self.shake_amp.y * math.cos(self.since_shake * 35)))
        offset = (offset + screenshake).get_position()
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

        if self.red_flash_alpha > 0:
            self.red_flash.fill((self.red_flash_alpha, 0.25*self.red_flash_alpha, 0))
            surface.blit(self.red_flash, (0, 0), special_flags=pygame.BLEND_ADD)

    def shake(self, direction=None, amt=15):
        direction = direction.copy() if direction is not None else Pose((1, -1))
        direction.scale_to(amt)
        if direction.magnitude() > self.shake_amp.magnitude():
            self.shake_amp = direction
            self.since_shake = 0

    def next_frame(self):
        return Frame()