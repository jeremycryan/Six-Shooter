from player import Player
from camera import Camera
import constants as c
import pygame
from background import Background
from primitives import Pose
import math
from particle import SparkParticle
import random

from enemy import Grunt

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
        self.enemies = [Grunt((1000, 1000), self)]
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

        for enemy in self.enemies[:]:
            enemy.update(dt, events)
            if enemy.destroyed:
                self.enemies.remove(enemy)
        self.enemies.sort(key=lambda x:x.position.y)

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

        self.check_enemy_and_projectile_collisions()
        self.check_enemy_and_enemy_collisions(dt, events)

        self.red_flash_alpha -= 5 * dt
        self.red_flash_alpha *= 0.03**dt
        if self.player.weapon_mode == c.FIRE and self.player.firing and int(self.player.hand_sprite.get_frame_num()) == 7 and self.red_flash_alpha < 10:
            self.red_flash_alpha = 255
            self.shake(direction=None, amt=30)
            for i in range(16):
                position = self.player.hand_sprite.x, self.player.hand_sprite.y
                self.particles.append(SparkParticle(position))
            random.choice(self.player.flame_bursts).play()

    def check_enemy_and_projectile_collisions(self):
        for enemy in self.enemies:
            for projectile in self.projectiles:
                projectile_position = projectile.position + Pose((0, projectile.z))
                if (enemy.position - projectile_position).magnitude() < enemy.radius + projectile.radius:
                    enemy.get_hit_by(projectile)

    def check_enemy_and_enemy_collisions(self, dt, events):
        for i, enemy in enumerate(self.enemies):
            for j, enemy2 in enumerate(self.enemies):
                if j <= i:
                    continue
                diff = enemy.position - enemy2.position
                dist = (diff).magnitude()
                if dist < enemy.radius + enemy2.radius:
                    overlap_amt = enemy.radius + enemy2.radius - dist
                    overlap_vec = diff.copy()
                    overlap_vec.scale_to(overlap_amt * 10)
                    enemy.velocity += overlap_vec*dt
                    enemy2.velocity += overlap_vec*-dt



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
            if hasattr(projectile, "landed") and projectile.landed:
                projectile.draw(surface, offset=offset)
        for enemy in self.enemies:
            enemy.draw(surface, offset=offset)
        for projectile in self.projectiles:
            if not hasattr(projectile, "landed") or not projectile.landed:
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