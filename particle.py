from primitives import Pose
import random
import math
import pygame
import constants as c
from pyracy.sprite_tools import Sprite, Animation


class Particle:

    def __init__(self, position=(0, 0), velocity=(0, 0), duration=1):
        self.position = Pose(position)
        self.velocity = Pose(velocity)
        self.destroyed = False
        self.duration = duration
        self.age = 0
        self.layer = c.BACKGROUND

    def update(self, dt, events):
        if self.destroyed:
            return
        self.position += self.velocity * dt
        if self.age > self.duration:
            self.destroy()
        self.age += dt

    def draw(self, surf, offset=(0, 0)):
        if self.destroyed:
            return

    def through(self):
        return min(0.999, self.age/self.duration)

    def destroy(self):
        self.destroyed = True


class Puff(Particle):
    surfs = []
    def __init__(self, position=(0, 0), velocity=None):
        angle = random.random() * math.pi * 2
        if not velocity:
            amt = random.random() * 500
            vx = math.cos(angle) * amt
            vy = -math.sin(angle) * amt * 0.5
            velocity = (vx, vy)
        super().__init__((position[0], position[1] + 30), duration=0.5, velocity=velocity)
        self.position += self.velocity*(1/self.velocity.magnitude()) * 30
        self.age += random.random() * self.duration * 0.5
        if not Puff.surfs:
            Puff.surfs = []
            sheet = pygame.image.load("assets/images/puff.png")
            width = sheet.get_width()//3
            for i in range(3):
                new_surf = pygame.Surface((width, sheet.get_height()))
                new_surf.blit(sheet, (i*-width, 0))
                new_surf.set_colorkey((255, 0, 255))
                Puff.surfs.append(new_surf)
        self.surf = random.choice(Puff.surfs)

    def update(self, dt, events):
        super().update(dt, events)
        self.velocity *= 0.01**dt


    def draw(self, surf, offset=(0, 0)):
        w = self.surf.get_width() * (1 - 0.8*self.through()) * 0.7
        h = self.surf.get_height() * (1 - 0.8*self.through()) * 0.7
        if w < 0 or h < 0:
            pass
        my_surf = pygame.transform.scale(self.surf, (w, h))
        x = -offset[0] - w//2 + self.position.x
        y = -offset[1] - h//2 + self.position.y
        my_surf.set_alpha(180 * (1-self.through()**2))
        surf.blit(my_surf, (x, y))


class MuzzleFlash(Particle):
    surf = None

    def __init__(self, position, angle, duration=0.08):
        if not MuzzleFlash.surf:
            MuzzleFlash.surf = pygame.image.load("assets/images/muzzle_flash.png")

        super().__init__(position, duration=duration)
        self.surf = pygame.transform.rotate(MuzzleFlash.surf, angle)
        self.surf.set_colorkey((255, 0, 255))
        self.layer = c.FOREGROUND

    def draw(self, surf, offset=(0, 0)):
        w = self.surf.get_width() * 1.4 #* (1 - self.through()**2)
        h = self.surf.get_height() * 1.4#* (1 - self.through()**2)
        if w < 0 or h < 0:
            pass
        my_surf = pygame.transform.scale(self.surf, (w, h))
        x = -offset[0] - w//2 + self.position.x
        y = -offset[1] - h//2 + self.position.y
        my_surf.set_alpha(255 * (1-self.through()**2))
        surf.blit(my_surf, (x, y))


class Casing(Particle):
    surf = None

    def __init__(self, position, duration=20):

        x_velocity = (random.random() * 80 + 30) * random.choice((-1, 1))
        self.z_velocity = -750
        velocity = Pose((x_velocity, 0))
        self.z = -0
        super().__init__(position, velocity=velocity.get_position(), duration=duration)
        self.landed = False
        if not Casing.surf:
            Casing.surf = pygame.image.load("assets/images/casing.png")
        self.surf = pygame.transform.scale(Casing.surf.copy(), (10, 20))
        self.random_angle = random.random()*360

    def update(self, dt, events):
        super().update(dt, events)
        if not self.landed:
            self.z += self.z_velocity*dt
            self.z_velocity += 4000*dt
            if self.z > 40:
                self.landed = True
                self.z_velocity = 0
                self.velocity = Pose((0, 0))

    def draw(self, surf, offset=(0, 0)):
        angle = self.through() * 200 * (self.velocity.x) + self.random_angle
        casing = pygame.transform.rotate(self.surf, angle)
        x = self.position.x - offset[0] - casing.get_width()
        y = self.position.y - offset[1] - casing.get_height() + self.z
        surf.blit(casing, (x, y))



class SparkParticle(Particle):

    def __init__(self, position, velocity=None, duration=0.5, color=(255, 0, 0), scale=40, velocity_scale=1.0):
        self.color = color
        self.scale = scale
        velocity_mag = (random.random()**2 * 1600 + 800) * velocity_scale
        if not velocity:
            velocity_angle = random.random() * 2 * math.pi
        else:
            velocity_angle = math.atan2(velocity[0], velocity[1]) + random.choice((-1, 1))*random.random()**4*math.pi/2
        velocity_x = math.sin(velocity_angle) * velocity_mag
        velocity_y = math.cos(velocity_angle) * velocity_mag
        velocity = velocity_x, velocity_y
        super().__init__(position=position, velocity=velocity, duration=duration)
        self.age += random.random() * 0.3
        self.layer = c.FOREGROUND

    def update(self, dt, events):
        super().update(dt, events)
        self.velocity *= 0.005**dt


    def draw(self, surf, offset=(0, 0)):
        if self.destroyed:
            return
        corners = [[3, 0], [0, -0.25], [-2, 0], [0, 0.25]]

        angle = math.atan2(self.velocity.y, self.velocity.x)

        scale = self.scale * (1 - self.through())
        for corner in corners:
            original_angle = math.atan2(corner[1], corner[0])
            new_angle = angle - original_angle
            mag = math.sqrt(corner[0]**2 + corner[1]**2)
            mag *= scale
            corner[0] = math.cos(new_angle) * mag
            corner[1] = math.sin(new_angle) * mag
            corner[0] += self.position.x - offset[0]
            corner[1] += self.position.y - offset[1]

        color = tuple([self.color[i] * self.through() + 255 * (1 - self.through()) for i in range(3)])
        pygame.draw.polygon(surf, color, corners)
