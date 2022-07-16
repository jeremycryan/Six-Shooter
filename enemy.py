from pyracy.sprite_tools import Sprite, Animation
from primitives import Pose
import constants as c
import math
import pygame
from camera import Camera
import random

class Enemy:

    def __init__(self, position, frame):
        self.frame = frame
        self.radius = 75
        self.sprite = None
        self.health = 100
        self.position = Pose(position)
        self.velocity = Pose((0, 0))
        self.lethal = False
        self.destroyed = False
        self.fixed = False

        visible_radius = self.shadow_radius()
        self.shadow = pygame.Surface((visible_radius*2, visible_radius*2))
        self.shadow.fill((255, 255, 0))
        self.shadow.set_colorkey((255, 255, 0))
        pygame.draw.circle(self.shadow, (0, 0, 0), (visible_radius, visible_radius), visible_radius)
        self.shadow.set_alpha(60)

    def shadow_radius(self):
        return self.radius

    def shadow_offset(self):
        return 20

    def get_hit_by(self, projectile):
        if projectile.damage:
            self.take_damage(projectile.damage)
        projectile.hit(self)

    def take_damage(self, amount):
        self.health -= amount

    def draw(self, surface, offset=(0, 0)):
        if not self.lethal:
            surface.blit(self.shadow, (self.position.x - offset[0] - self.shadow.get_width()//2,
                                       self.position.y - offset[1] - self.shadow.get_height()//2 + self.shadow_offset()))
        position_and_offset = Pose(offset)*-1 + self.position
        if position_and_offset.x < -self.radius*2 or position_and_offset.x > c.WINDOW_WIDTH + self.radius*2 :
            return
        if position_and_offset.y < -self.radius*2  or position_and_offset.y > c.WINDOW_HEIGHT + self.radius*2 :
            return
        self.sprite.set_position(self.position.get_position())
        self.sprite.draw(surface, offset=offset)

    def update(self, dt, events):
        self.sprite.update(dt, events)
        if not self.fixed:
            self.position += self.velocity*dt
        if self.health < 0 and not self.lethal:
            self.lethal = True
            self.destroy()

    def destroy(self):
        self.destroyed = True


class Grunt(Enemy):

    def __init__(self, position, frame):
        super().__init__(position, frame)
        buzz_right = Animation.from_path("assets/images/bug.png",
                                         sheet_size=(5, 1),
                                         frame_count=5,
                                         reverse_x=True)
        buzz_left = Animation.from_path("assets/images/bug.png",
                                         sheet_size=(5, 1),
                                         frame_count=5,
                                         reverse_x=False)
        die_right = Animation.from_path("assets/images/bug_dying.png",
                                        sheet_size=(3, 1),
                                        frame_count=3,
                                        reverse_x = False)
        die_left = Animation.from_path("assets/images/bug_dying.png",
                                        sheet_size=(3, 1),
                                        frame_count=3,
                                        reverse_x = True)
        damage_left = Animation.from_path("assets/images/bug_damage.png",
                                        sheet_size=(2, 1),
                                        frame_count=2,
                                        reverse_x = False)
        damage_right = Animation.from_path("assets/images/bug_damage.png",
                                        sheet_size=(2, 1),
                                        frame_count=2,
                                        reverse_x = True)
        self.sprite = Sprite(12)
        self.sprite.add_animation({
            "BuzzRight": buzz_right,
            "BuzzLeft": buzz_left,

        }, loop=True,
        )
        self.sprite.add_animation({
            "DieRight": die_right,
            "DieLeft": die_left,
        }, loop=False)
        self.sprite.add_animation({
            "DamageLeft": damage_left,
            "DamageRight": damage_right,
        })
        for key in ["DieRight", "DieLeft"]:
            self.sprite.add_callback(key, self.destroy_me_for_real)
        self.sprite.chain_animation("DamageLeft", "BuzzLeft")
        self.sprite.chain_animation("DamageRight", "BuzzRight")
        self.direction_lr = c.RIGHT if self.velocity.x > 0 else c.LEFT
        if self.direction_lr == c.RIGHT:
            self.sprite.start_animation("BuzzRight")
        else:
            self.sprite.start_animation("BuzzLeft")

    def shadow_radius(self):
        return self.radius*0.6

    def shadow_offset(self):
        return 50

    def update(self, dt, events):
        super().update(dt, events)
        self.face_player(dt, events)

    def get_hit_by(self, projectile):
        if self.lethal:
            return
        super().get_hit_by(projectile)
        self.velocity *= projectile.slowdown

    def destroy_me_for_real(self):
        self.destroyed = True

    def face_player(self, dt, events):
        player = self.frame.player
        dp = player.position - self.position
        if dp.magnitude() > 0:
            dp.scale_to(1200)

        if not self.lethal:
            self.velocity += dp * dt
            if self.velocity.magnitude() > 500:
                self.velocity.scale_to(500)

            if not self.sprite.active_animation_key in ["DamageRight", "DamageLeft"]:
                if dp.x > 0:
                    self.sprite.start_animation("BuzzRight", restart_if_active=False)
                else:
                    self.sprite.start_animation("BuzzLeft", restart_if_active=False)

        self.velocity *= 0.5 ** dt

    def destroy(self):
        player = self.frame.player
        dp = player.position - self.position
        if dp.magnitude() > 0:
            dp.scale_to(1200)
        if dp.x < 0:
            self.sprite.start_animation("DieRight")
        else:
            self.sprite.start_animation("DieLeft")

    def take_damage(self, amount):
        super().take_damage(amount)
        player = self.frame.player
        dp = player.position - self.position
        if dp.x > 0:
            self.sprite.start_animation("DamageRight")
        else:
            self.sprite.start_animation("DamageLeft")


class BossMan(Enemy):
    def __init__(self, position, frame):
        super().__init__(position, frame)
        idle = Animation.from_path("assets/images/boss_idle.png",frame_count=2,sheet_size=(2, 1))
        self.sprite = Sprite(12)
        self.sprite.add_animation({"Idle": idle},loop=True)
        self.sprite.start_animation("Idle")
        self.radius = 150
        self.hands = [Hand((self.position + Pose((200, 150))).get_position(), self.frame, right=True),
                      Hand((self.position + Pose((-200, 150))).get_position(), self.frame, right=False)]
        self.frame.enemies += self.hands
        self.health = 10000
        self.fixed = True
        self.boss_mode = c.BOSS_IDLE

        self.beam_sprite = Sprite(12)
        charging = Animation.from_path("assets/images/laser_mouth.png", sheet_size=(18, 1), frame_count=15)
        firing = Animation.from_path("assets/images/laser_mouth.png", sheet_size=(18, 1), frame_count=18, start_frame=15)
        self.beam_sprite.add_animation({
            "Charging": charging,
        })
        self.beam_sprite.add_animation({
            "Firing": firing,
        }, loop=True)
        self.beam_sprite.chain_animation("Charging", "Firing")
        self.beam_sprite.start_animation("Firing")
        self.beam_sprite.add_callback("Charging", self.laser_attack_start)
        self.beam_length_sprite = Sprite(12)
        beam = Animation.from_path("assets/images/laser.png", sheet_size=(1, 1), frame_count=1)
        self.beam_length_sprite.add_animation({"Beam": beam}, loop=True)
        self.beam_length_sprite.start_animation("Beam")

        self.sweep_position = 0
        self.sweep_direction = c.RIGHT
        self.sweep_target_speed = 400
        self.sweep_speed = 0
        self.drift_speed = 100

        #self.prepare_laser_attack()

        self.since_last_attack_finish = 0

    def laser_attack_start(self):
        self.beam_length_sprite.start_animation("Beam")
        self.boss_mode = c.BOSS_FIRING_LASER
        self.frame.shake(amt=40)

    def prepare_laser_attack(self):
        self.sweep_target = 100
        self.boss_mode = c.BOSS_PREPARING_LASER
        self.sweep_position = Camera.world_to_screen(self.position.get_position()).x
        self.beam_sprite.start_animation("Charging")
        self.sweep_direction = c.RIGHT
        self.sweep_target_speed = 500

    def move_to_idle(self):
        self.boss_mode = c.BOSS_IDLE

    def swoop_above_player(self):
        self.boss_mode = c.BOSS_SWOOPING

    def update(self, dt, events):
        super().update(dt, events)
        if self.boss_mode == c.BOSS_SWOOPING:
            if self.since_last_attack_finish > 2:
                self.next_attack()
            target = self.frame.player.position + Pose((0, -400))
            speed = (target - self.position) * 5
            self.position += speed*dt
            if (target - self.position).magnitude() < 100:
                self.move_to_idle()
        if self.boss_mode == c.BOSS_IDLE:
            self.since_last_attack_finish += dt
            if self.since_last_attack_finish > 2:
                self.next_attack()
            target = self.frame.player.position
            speed = (target - self.position)
            if speed.magnitude() > self.drift_speed:
                speed.scale_to(self.drift_speed)
            self.position += speed*dt
        if self.boss_mode == c.BOSS_IDLE or self.boss_mode == c.BOSS_SWOOPING or self.boss_mode == c.BOSS_FIRING_LASER or self.boss_mode == c.BOSS_PREPARING_LASER:
            self.hands[0].target_anchor = self.position + Pose((200, 150))
            self.hands[1].target_anchor = self.position + Pose((-200, 150))
        self.beam_sprite.update(dt, events)
        self.beam_length_sprite.update(dt, events)
        if self.boss_mode == c.BOSS_FIRING_LASER or self.boss_mode == c.BOSS_PREPARING_LASER:
            self.sweep_speed += (self.sweep_target_speed - self.sweep_speed) * 4 * dt
            self.position.y += (Camera.screen_to_world((0, 100)).y - self.position.y) * 5 * dt
            if self.sweep_direction==c.RIGHT:
                self.position.x += self.sweep_speed*dt
                if Camera.world_to_screen((self.position.x, 0)).x > c.WINDOW_WIDTH - 100:
                    self.sweep_direction = c.LEFT
            else:
                self.sweep_target_speed = -500
                self.position.x += self.sweep_speed*dt
                if Camera.world_to_screen((self.position.x, 0)).x < 50:
                    self.swoop_above_player()
        if self.boss_mode == c.BOSS_PREPARING_LASER:
            self.sweep_position += (self.sweep_target - self.sweep_position) * 5 * dt
            self.position.x = Camera.screen_to_world((self.sweep_position, 0)).x

    def next_attack(self):
        self.since_last_attack_finish = 0
        options = [self.prepare_laser_attack]
        random.choice(options)()

    def shadow_radius(self):
        return self.radius

    def shadow_offset(self):
        return 100

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset)
        self.beam_sprite.set_position((self.position + Pose((0, 100))).get_position())
        if self.boss_mode == c.BOSS_FIRING_LASER or self.boss_mode == c.BOSS_PREPARING_LASER:
            self.beam_sprite.draw(surface, offset)
        if self.boss_mode == c.BOSS_FIRING_LASER:
            for off in range(1, 3):
                pose = self.position + Pose((0, 100)) + Pose((0, 512))*off
                self.beam_length_sprite.set_position(pose.get_position())
                self.beam_length_sprite.draw(surface, offset=offset)


class Hand(Enemy):
    def __init__(self, position, frame, right=False):
        super().__init__(position, frame)
        fist = Animation.from_path("assets/images/big_hands.png",sheet_size=(3, 1),frame_count=3, start_frame=2, reverse_x=(not right))
        palm = Animation.from_path("assets/images/big_hands.png", sheet_size=(3, 1), frame_count=2, start_frame=1, reverse_x=(not right))
        idle = Animation.from_path("assets/images/big_hands.png", sheet_size=(3, 1), frame_count=1, reverse_x=(not right))
        self.sprite = Sprite(12)
        self.sprite.add_animation({
            "Fist":fist,
            "Palm":palm,
            "Idle":idle,
        })
        self.sprite.start_animation("Idle")
        self.health = 6000
        self.fixed = True
        self.offset = Pose((0, 0))
        self.age = 0
        self.target_offset = Pose((0, 0))
        self.anchor = self.position.copy()
        self.target_anchor = self.anchor.copy()
        self.right = right
        self.radius = 60

    def shadow_radius(self):
        return 40

    def shadow_offset(self):
        return 30 - self.offset.y*0.8

    def update(self, dt, events):
        super().update(dt, events)
        self.age += dt
        self.target_offset = Pose((0, math.sin(self.age*3 + math.pi/4*self.right) * 50))
        do = self.target_offset - self.offset
        da = self.target_anchor - self.anchor
        self.anchor += da*10*dt
        self.offset += do*10*dt
        self.position = self.anchor + self.offset
        self.sprite.set_angle(math.cos(self.age*3 + math.pi/4*self.right) * 20 * (-1 + 2*self.right))

