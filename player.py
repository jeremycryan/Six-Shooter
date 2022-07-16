from pyracy.sprite_tools import Sprite, Animation
from primitives import Pose
import pygame
import constants as c
import math
from camera import Camera
from particle import Puff,MuzzleFlash
from projectile import PistolBullet, Bread, Shuriken
import random
from sound_manager import SoundManager

class Player:

    def __init__(self, frame):
        self.frame = frame
        self.position = Pose(c.ARENA_SIZE) * 0.5
        Camera.position = self.position.copy() - Pose(c.WINDOW_SIZE)*0.5
        self.velocity = Pose((0, 0))
        self.sprite = Sprite(12, (0, 0))
        self.hand_sprite = Sprite(12, (0, 0))
        self.populate_hand_sprite(self.hand_sprite)
        walk_right = Animation.from_path(
            "assets/images/walk_right.png",
            sheet_size=(8, 1),
            frame_count=8,
            scale=0.25,
        )
        walk_left = Animation.from_path(
            "assets/images/walk_right.png",
            sheet_size=(8, 1),
            frame_count=8,
            reverse_x=True,
            scale=0.25,
        )
        idle_right = Animation.from_path(
            "assets/images/idle.png",
            sheet_size=(8, 1),
            frame_count=2,
            scale=0.25,
        )
        idle_left = Animation.from_path(
            "assets/images/idle.png",
            sheet_size=(8, 1),
            frame_count=2,
            scale=0.25,
            reverse_x=True,
        )
        walk_back_right = Animation.from_path(
            "assets/images/walk_right_back.png",
            sheet_size=(8, 1),
            frame_count=8,
            scale=0.25,
        )
        walk_back_left = Animation.from_path(
            "assets/images/walk_right_back.png",
            sheet_size=(8, 1),
            frame_count=8,
            scale=0.25,
            reverse_x=True,
        )
        rolling = Animation.from_path(
            "assets/images/roll.png",
            sheet_size=(6, 1),
            frame_count=6,
        )
        self.sprite.add_animation(
            {
                "WalkRight": walk_right,
                "WalkLeft": walk_left,
                "IdleRight": idle_right,
                "IdleLeft": idle_left,
                "WalkBackRight": walk_back_right,
                "WalkBackLeft": walk_back_left,
            },
            loop=True
        )
        self.sprite.add_animation({"Rolling": rolling})
        self.sprite.add_callback("Rolling", self.stop_rolling)
        self.sprite.start_animation("WalkRight")

        self.animation_state = c.IDLE
        self.last_lr_direction = c.RIGHT
        self.rolling = False
        self.firing = False
        self.last_fire = 999
        self.weapon_mode = c.GUN
        self.aim_angle = 0
        self.arm_angle = 0
        self.aim_distance = 75
        self.aim_knockback = 0
        self.knockback_velocity = 0
        self.radius = 50

        self.since_kick = 0
        self.roll_sound = SoundManager.load("assets/sounds/die_roll.wav")

    def update(self, dt, events):
        self.last_fire += dt
        self.process_inputs(dt, events)
        self.sprite.set_position(self.position.get_position())
        was_firing = self.firing
        self.sprite.update(dt, events)
        self.hand_sprite.update(dt, events)
        if not self.firing and was_firing:
            self.hand_sprite.update(0, events)
        mpos = Camera.screen_to_world(pygame.mouse.get_pos())
        Camera.target = self.position.copy() * 0.7 + mpos * 0.3
        self.update_hand(dt, events)
        if self.animation_state == c.WALKING:
            self.since_kick += dt
        if self.since_kick > 1/6 and self.velocity.magnitude() > 0:
            for i in range(3):
                start_position = self.position + self.velocity * (1/self.velocity.magnitude()) * 30
                start_position += Pose((random.random() * 10 - 5, random.random() * 10 - 5))
                start_velocity = self.velocity * -0.3
                start_velocity.rotate_position(20 * (i-1))
                self.frame.particles.append(Puff(start_position.get_position(), start_velocity.get_position()))
                self.since_kick -= 1/6
        if self.position.x - self.radius < 0:
            self.position.x = self.radius
        if self.position.x + self.radius > c.ARENA_WIDTH:
            self.position.x = c.ARENA_WIDTH - self.radius
        if self.position.y - self.radius < 0:
            self.position.y = self.radius
        if self.position.y + self.radius > c.ARENA_HEIGHT:
            self.position.y = c.ARENA_HEIGHT - self.radius

    def process_inputs(self, dt, events):
        direction = Pose((0, 0))
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_w]:
            direction += Pose((0, -1))
        if pressed[pygame.K_s]:
            direction += Pose((0, 1))
        if pressed[pygame.K_a]:
            direction += Pose((-1, 0))
        if pressed[pygame.K_d]:
            direction += Pose((1, 0))

        old_state = self.animation_state

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not self.rolling:
                        self.roll(direction)
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            if not self.rolling and not self.firing:
                self.fire()

        if self.rolling:
            pass
        else:
            if direction.magnitude() > 0:
                direction.scale_to(1)
                self.velocity += direction * dt * 7500
                self.animation_state = c.WALKING
            else:
                self.velocity *= 0.0001**dt
            if direction.magnitude() == 0:
                self.animation_state = c.IDLE

            if direction.x > 0:
                self.last_lr_direction = c.RIGHT
            elif direction.x < 0:
                self.last_lr_direction = c.LEFT

        if self.animation_state == c.WALKING:
            clear_time = old_state != c.WALKING
            if clear_time:
                self.since_kick = 0
            if self.velocity.y >= -5:
                if self.last_lr_direction == c.RIGHT:
                    self.sprite.start_animation("WalkRight", restart_if_active=False, clear_time=clear_time)
                else:
                    self.sprite.start_animation("WalkLeft", restart_if_active=False, clear_time=clear_time)
            else:
                if self.last_lr_direction == c.RIGHT:
                    self.sprite.start_animation("WalkBackRight", restart_if_active=False, clear_time=clear_time)
                else:
                    self.sprite.start_animation("WalkBackLeft", restart_if_active=False, clear_time=clear_time)
        elif self.animation_state == c.IDLE:
            if self.last_lr_direction == c.RIGHT:
                self.sprite.start_animation("IdleRight", restart_if_active=False, clear_time=False)
            else:
                self.sprite.start_animation("IdleLeft", restart_if_active=False, clear_time=False)

        if self.velocity.magnitude() > 550 and not self.rolling:
            self.velocity.scale_to(550)

        self.position += self.velocity * dt

    def roll(self, direction):
        self.rolling = True
        self.animation_state = c.ROLLING
        animation = "Rolling"
        self.sprite.start_animation(animation, True, clear_time=True)
        if direction.magnitude() == 0:
            direction.y = 0
            direction.x = 1 if self.last_lr_direction == c.RIGHT else -1
        self.velocity = direction * 750
        self.firing = False
        self.roll_sound.play()

    def stop_rolling(self):
        self.rolling = False
        self.animation_state = c.IDLE
        self.sprite.start_animation("IdleRight")
        for i in range(20):
            self.frame.particles.append(Puff(self.position.get_position()))
        modes_to_roll = [mode for mode in c.VALID_MODES if mode is not self.weapon_mode]
        if not len(modes_to_roll):
            modes_to_roll = c.VALID_MODES
        self.weapon_mode = random.choice(modes_to_roll)
        self.hand_sprite.update(0, [])

    def draw(self, surface, offset=(0, 0)):
        self.draw_hand(surface, offset, up=True)
        self.sprite.draw(surface, offset)
        self.draw_hand(surface, offset, up=False)

    def populate_hand_sprite(self, hand_sprite):
        gun_idle_right = Animation.from_path(
            "assets/images/gun.png",
            sheet_size=(3, 1),
            frame_count=1,
        )
        gun_idle_left = Animation.from_path(
            "assets/images/gun.png",
            sheet_size=(3, 1),
            frame_count=1,
            reverse_x=True,
        )
        gun_fire_left = Animation.from_path(
            "assets/images/gun.png",
            sheet_size=(3, 1),
            frame_count=3,
            reverse_x=True,

            start_frame=1,
        )
        gun_fire_right = Animation.from_path(
            "assets/images/gun.png",
            sheet_size=(3,1),
            frame_count=3,

            start_frame=1,
        )
        bread_fire_right = Animation.from_path(
            "assets/images/bread_arm.png",
            sheet_size=(7, 1),
            frame_count=4,

            start_frame=1,
        )
        bread_fire_left = Animation.from_path(
            "assets/images/bread_arm.png",
            sheet_size=(7, 1),
            frame_count=4,
            reverse_x=True,

            start_frame=1,
        )
        bread_idle_right = Animation.from_path(
            "assets/images/bread_arm.png",
            sheet_size=(7, 1),
            frame_count=1,
        )
        bread_idle_left = Animation.from_path(
            "assets/images/bread_arm.png",
            sheet_size=(7, 1),
            frame_count=1,
            reverse_x=True,
        )
        shuriken_fire_right = Animation.from_path(
            "assets/images/shuriken_arm.png",
            sheet_size=(5, 1),
            frame_count=4,
            start_frame=1,
        )
        shuriken_fire_left = Animation.from_path(
            "assets/images/shuriken_arm.png",
            sheet_size=(5, 1),
            frame_count=4,
            reverse_x=True,

            start_frame=1,
        )
        shuriken_idle_right = Animation.from_path(
            "assets/images/shuriken_arm.png",
            sheet_size=(5, 1),
            frame_count=1,
        )
        shuriken_idle_left = Animation.from_path(
            "assets/images/shuriken_arm.png",
            sheet_size=(5, 1),
            frame_count=1,
            reverse_x=True,
        )
        hand_sprite.add_animation(
            {
                 "GunIdleLeft": gun_idle_left,
                 "GunIdleRight": gun_idle_right,
                 "BreadIdleRight": bread_idle_right,
                 "BreadIdleLeft": bread_idle_left,
                 "ShurikenIdleRight": shuriken_idle_right,
                 "ShurikenIdleLeft": shuriken_idle_left,
             },
            loop=True
        )
        hand_sprite.add_animation(
            {
                "GunFireLeft": gun_fire_left,
                "GunFireRight": gun_fire_right,
                "BreadFireRight": bread_fire_right,
                "BreadFireLeft": bread_fire_left,
                "ShurikenFireRight": shuriken_fire_right,
                "ShurikenFireLeft": shuriken_fire_left,
            },
            loop=False
        )
        hand_sprite.add_callback("GunFireRight",self.finish_firing)
        hand_sprite.add_callback("GunFireLeft", self.finish_firing)
        hand_sprite.add_callback("BreadFireRight",self.finish_firing)
        hand_sprite.add_callback("BreadFireLeft", self.finish_firing)
        hand_sprite.add_callback("ShurikenFireRight",self.finish_firing)
        hand_sprite.add_callback("ShurikenFireLeft", self.finish_firing)
        hand_sprite.start_animation("GunIdleRight")

    def update_hand(self, dt, events):
        mpos = pygame.mouse.get_pos()
        aim_position = Camera.screen_to_world(mpos)
        relative = aim_position - self.position
        relative.scale_to(70)
        da = self.aim_angle - relative.get_angle_of_position()*180/math.pi
        da2 = self.aim_angle + 360 - relative.get_angle_of_position()*180/math.pi
        da3 = self.aim_angle - 360 - relative.get_angle_of_position()*180/math.pi
        target = (sorted([da, da2, da3], key=lambda x: abs(x)))[0]
        max_change = abs(target)
        change = target * 25 * dt
        if abs(change) > abs(max_change) and target != 0:
            change *= abs(max_change)/abs(change)
        self.aim_angle -= change

        da = self.arm_angle - relative.get_angle_of_position()*180/math.pi
        da2 = self.arm_angle + 360 - relative.get_angle_of_position()*180/math.pi
        da3 = self.arm_angle - 360 - relative.get_angle_of_position()*180/math.pi
        target = (sorted([da, da2, da3], key=lambda x: abs(x)))[0]
        amt = target * 100
        if abs(amt) > 1000:
            amt *= 1000/abs(amt)
        amt *= dt
        if abs(amt) > abs(target) and target != 0:
            amt *= abs(target)/abs(amt)
        self.arm_angle -= amt

        self.arm_angle %= 360
        self.aim_angle %= 360

        #self.aim_knockback *= 0.000001**dt
        self.aim_knockback += self.knockback_velocity*dt
        if self.knockback_velocity > -500:
            self.knockback_velocity -= 50000*dt
        if self.aim_knockback < 0:
            self.aim_knockback = 0


    def fire(self):
        if self.last_fire < c.COOLDOWNS[self.weapon_mode]:
            return

        self.last_fire = 0
        self.firing = True
        mpos = pygame.mouse.get_pos()
        relative = Camera.screen_to_world(mpos) - self.position

        self.aim_angle = relative.get_angle_of_position()*180/math.pi
        self.aim_knockback = 0
        self.arm_angle = self.aim_angle
        offset = self.position + Pose((math.cos(self.arm_angle*math.pi/180), -math.sin(self.arm_angle*math.pi/180))) * (self.aim_distance + 28)
        knockback = Pose((0, 0))

        if self.weapon_mode == c.GUN:
            self.knockback_velocity = 1500
            if relative.x < 0:
                self.hand_sprite.start_animation("GunFireLeft")
            else:
                self.hand_sprite.start_animation("GunFireRight")
            self.frame.particles.append(MuzzleFlash(offset.get_position(), self.arm_angle))
            self.frame.projectiles.append(PistolBullet(offset.get_position(), relative.get_position()))
            knockback = relative * -1
            knockback.scale_to(500)
        elif self.weapon_mode == c.BREAD:
            self.knockback_velocity = 0
            if relative.x < 0:
                self.hand_sprite.start_animation("BreadFireLeft")
            else:
                self.hand_sprite.start_animation("BreadFireRight")
            self.frame.projectiles.append(Bread(offset.get_position(), relative.get_position(), self.frame))
        elif self.weapon_mode == c.SHURIKEN:
            self.knockback_velocity = 1500
            if relative.x < 0:
                self.hand_sprite.start_animation("ShurikenFireLeft")
            else:
                self.hand_sprite.start_animation("ShurikenFireRight")
            angle = relative.get_angle_of_position()
            for angle_offset in [-1.0, -0.5, 0, 0.5, 1.0]:
                new_angle = angle + angle_offset
                new_relative = Pose((math.cos(new_angle), -math.sin(new_angle)))
                self.frame.projectiles.append(Shuriken(offset.get_position(), new_relative.get_position(), self.frame))
            knockback = relative * -1
            knockback.scale_to(500)

        self.velocity += knockback

    def finish_firing(self):
        self.firing = False

    def draw_hand(self, surface, offset=(0, 0), up=False):
        if self.rolling:
            return
        dist = self.aim_distance - self.aim_knockback
        relative = Pose((math.cos(self.arm_angle*math.pi/180), -math.sin(self.arm_angle * math.pi/180))) * dist
        sprite_angle = self.aim_angle
        if up and relative.y > 0:
            return
        if not up and relative.y <= 0:
            return
        if relative.x < 0:
            sprite_angle += 180
            sprite_angle %= 360
        if self.weapon_mode == c.GUN and not self.firing:
            if relative.x < 0:
                self.hand_sprite.start_animation("GunIdleLeft", restart_if_active=False)
            else:
                self.hand_sprite.start_animation("GunIdleRight", restart_if_active=False)
        if self.weapon_mode == c.BREAD and not self.firing:
            if relative.x < 0:
                self.hand_sprite.start_animation("BreadIdleLeft", restart_if_active=False)
            else:
                self.hand_sprite.start_animation("BreadIdleRight", restart_if_active=False)
        if self.weapon_mode == c.SHURIKEN and not self.firing:
            if relative.x < 0:
                self.hand_sprite.start_animation("ShurikenIdleLeft", restart_if_active=False)
            else:
                self.hand_sprite.start_animation("ShurikenIdleRight", restart_if_active=False)

        self.hand_sprite.set_position((self.position + relative).get_position())
        self.hand_sprite.set_angle(sprite_angle)
        self.hand_sprite.draw(surface, offset)
