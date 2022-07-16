from primitives import Pose
import pygame
import math
import random
import constants as c

from pyracy.sprite_tools import Sprite, Animation
from particle import Puff


class Projectile:

    surf_cache = {}
    def __init__(self, position, velocity):
        self.position = Pose(position)
        self.velocity = Pose(velocity)
        self.destroyed = False
        self.age = 0
        self.radius = 10

    def update(self, dt, events):
        self.position += self.velocity * dt
        self.age += dt

    def draw(self, surface, offset=(0, 0)):
        pass

    @classmethod
    def load_surf(cls, path):
        if not path in cls.surf_cache:
            cls.surf_cache[path] = pygame.image.load(path)
        return cls.surf_cache[path]

    def on_impact(self):
        pass


class PistolBullet(Projectile):

    def __init__(self, position, direction):
        super().__init__(position, direction)
        if self.velocity.magnitude() == 0:
            self.velocity = Pose((1, 0))
        angle = self.velocity.get_angle_of_position()
        angle += random.random() * math.pi/15 - math.pi/30
        self.velocity = Pose((math.cos(angle), -math.sin(angle)))
        self.velocity.scale_to(4000)
        self.surf = self.load_surf("assets/images/bullet.png")
        anim = Animation(self.surf, (3, 1), 3)
        self.sprite = Sprite(12, self.position.get_position())
        self.sprite.add_animation({"Bullet": anim}, loop=True)
        self.sprite.start_animation("Bullet")
        angle = self.velocity.get_angle_of_position()*180/math.pi
        self.sprite.set_angle(angle)
        self.radius = 25

    def draw(self, surface, offset=(0, 0)):
        x = self.position.x
        y = self.position.y
        self.sprite.set_position((x, y))
        self.sprite.draw(surface, offset)

    def update(self, dt, events):
        super().update(dt, events)
        self.sprite.update(dt, events)
        if self.position.x < -2000 or self.position.x > c.WINDOW_WIDTH + 2000:
            self.destroyed = True
        if self.position.y < -2000 or self.position.y > c.WINDOW_HEIGHT + 2000:
            self.destroyed = True

class Bread(Projectile):
    def __init__(self, position, direction, frame):
        self.frame = frame
        super().__init__(position, direction)
        if self.velocity.magnitude() == 0:
            self.velocity = Pose((1, 0))
        angle = self.velocity.get_angle_of_position()
        angle += random.random() * math.pi/15 - math.pi/30
        self.velocity = Pose((math.cos(angle), -math.sin(angle)))
        self.velocity.scale_to(600)
        self.surf = self.load_surf("assets/images/bread.png")
        anim = Animation(self.surf, (7, 1), 1)
        self.sprite = Sprite(12, self.position.get_position())
        self.sprite.add_animation({"Bread": anim}, loop=True)
        self.sprite.start_animation("Bread")
        self.angle = self.velocity.get_angle_of_position()*180/math.pi
        if self.velocity.x < 0:
            self.angle += 180
        self.sprite.set_angle(angle)
        self.spin_speed = random.random()*100 + 260 * random.choice([-1, 1])
        self.zvel = -500
        self.z = 0
        self.radius = 25
        self.landed = False

    def update(self, dt, events):
        super().update(dt, events)
        self.angle -= self.spin_speed*dt
        self.sprite.set_angle(self.angle)
        self.sprite.update(dt, events)
        self.velocity *= 0.5**dt
        self.zvel += 1200*dt
        self.z += self.zvel*dt
        if self.z > 0:
            self.z = 0
            if self.velocity.magnitude() > 0:
                self.velocity = Pose((0, 0))
                for i in range(7):
                    self.frame.particles.append(Puff((self.position + Pose((0, -20))).get_position()))
                self.landed = True
            self.spin_speed = 0
            self.angle = -30

            if self.age > 20:
                self.destroyed = True


    def draw(self, surface, offset=(0, 0)):
        img = self.sprite.get_image()
        if self.age > 10:
            scale = 1 - ((self.age -10) * 5)
            if scale < 0:
                return
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))

        x = self.position.x - img.get_width()//2 - offset[0]
        y = self.position.y + self.z - img.get_height()//2 - offset[1]
        surface.blit(img, (x, y))

class Shuriken(Projectile):

    def __init__(self, position, direction, frame):
        self.frame = frame
        super().__init__(position, direction)
        if self.velocity.magnitude() == 0:
            self.velocity = Pose((1, 0))
        angle = self.velocity.get_angle_of_position()
        self.velocity = Pose((math.cos(angle), -math.sin(angle)))
        self.velocity.scale_to(2000)
        self.surf = self.load_surf("assets/images/shuriken.png")
        anim = Animation(self.surf, (1, 1), 1)
        self.sprite = Sprite(12, self.position.get_position())
        self.sprite.add_animation({"Bullet": anim}, loop=True)
        self.sprite.start_animation("Bullet")
        angle = self.velocity.get_angle_of_position()*180/math.pi
        self.sprite.set_angle(angle)
        self.radius = 20
        self.angle = angle
        self.spin_speed = 1000
        self.alpha = 255

    def draw(self, surface, offset=(0, 0)):
        x = self.position.x
        y = self.position.y
        self.sprite.set_position((x, y))
        self.sprite.draw(surface, offset)

    def update(self, dt, events):
        self.velocity *= 0.0001**dt
        super().update(dt, events)
        self.sprite.update(dt, events)
        self.angle += self.spin_speed*dt
        if self.age > 2:
            self.spin_speed *= 0.001**dt
            self.alpha -= 500*dt
        self.sprite.set_angle(self.angle)
        self.sprite.image.set_alpha(self.alpha)
        if self.alpha < 0:
            self.destroyed = True