from pyracy.sprite_tools import Sprite, Animation
from primitives import Pose
import constants as c
import math
import pygame
from camera import Camera
import random
from sound_manager import SoundManager
from particle import Puff

class Enemy:

    def __init__(self, position, frame):
        self.frame = frame
        self.radius = 75
        self.sprite = None
        self.health = 100
        self.max_health = 100
        self.position = Pose(position)
        self.velocity = Pose((0, 0))
        self.lethal = False
        self.destroyed = False
        self.fixed = False
        self.damaging = True

        self.damage_bread_sound = SoundManager.load("assets/sounds/Bread-Hits-Object.mp3")
        self.damage_bread_sound.set_volume(0.25)

        self.health_recently_lost = 0
        self.since_take_damage = 0

        visible_radius = self.shadow_radius()
        self.shadow = pygame.Surface((visible_radius*2, visible_radius*1.4))
        self.shadow.fill((255, 255, 0))
        self.shadow.set_colorkey((255, 255, 0))
        pygame.draw.ellipse(self.shadow, (0, 0, 0), self.shadow.get_rect())
        self.shadow.set_alpha(60)
        self.damage_sound = SoundManager.load("assets/sounds/Enemy-Damage.mp3")
        self.damage_sound.set_volume(0.5)

        self.raised = False

    def shadow_radius(self):
        return self.radius

    def shadow_offset(self):
        return 20

    def get_hit_by(self, projectile):
        if self. raised:
            return
        if projectile.damage:
            self.take_damage(projectile.damage)
        projectile.hit(self)

    def take_damage(self, amount):
        self.health -= amount
        self.health_recently_lost += amount
        self.since_take_damage = 0
        if amount > 0:
            self.damage_bread_sound.play()

    def draw(self, surface, offset=(0, 0)):
        if not self.lethal:
            if self.position.x < c.ARENA_WIDTH and self.position.x > 0:
                if self.position.y < c.ARENA_HEIGHT and self.position.y > 0:
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
        self.since_take_damage += dt
        if self.since_take_damage > 1:
            self.health_recently_lost -= 1000*dt
            self.health_recently_lost *= 0.2**dt
            if self.health_recently_lost < 0:
                self.health_recently_lost = 0

    def destroy(self):
        self.destroyed = True
        self.health_recently_lost = 0


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
                                        sheet_size=(4, 1),
                                        frame_count=4,
                                        reverse_x = False)
        die_left = Animation.from_path("assets/images/bug_dying.png",
                                        sheet_size=(4, 1),
                                        frame_count=4,
                                        reverse_x = True)
        damage_left = Animation.from_path("assets/images/bug_dying.png",
                                        sheet_size=(4, 1),
                                        frame_count=2,
                                        reverse_x = False)
        damage_right = Animation.from_path("assets/images/bug_dying.png",
                                        sheet_size=(4, 1),
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
        self.damage_sound.play()

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
        idle = Animation.from_path("assets/images/boss_idle.png",frame_count=3,sheet_size=(3, 1))
        attack = Animation.from_path("assets/images/boss attack.png", frame_count=3, sheet_size=(3, 1))
        self.sprite = Sprite(12)
        self.sprite.add_animation({"Idle": idle, "Attack": attack},loop=True)
        self.sprite.start_animation("Idle")
        self.radius = 150
        self.hands = [Hand((self.position + Pose((200, 150))).get_position(), self.frame, right=True),
                      Hand((self.position + Pose((-200, 150))).get_position(), self.frame, right=False)]
        self.frame.enemies += self.hands
        self.health = 10000
        self.max_health = self.health
        self.fixed = True
        self.boss_mode = c.BOSS_IDLE

        self.death_sound = SoundManager.load("assets/sounds/Boss-Death.mp3")

        self.beam_sprite = Sprite(12)
        charging = Animation.from_path("assets/images/laser_mouth.png", sheet_size=(19, 1), frame_count=15)
        firing = Animation.from_path("assets/images/laser_mouth.png", sheet_size=(19, 1), frame_count=19, start_frame=15)
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
        beam = Animation.from_path("assets/images/laser.png", sheet_size=(2, 1), frame_count=2)
        self.beam_length_sprite.add_animation({"Beam": beam}, loop=True, fps_override=12)
        self.beam_length_sprite.start_animation("Beam")

        self.sweep_position = 0
        self.sweep_direction = c.RIGHT
        self.sweep_target_speed = 400
        self.sweep_speed = 0
        self.drift_speed = 100

        self.laser_charge_sound = SoundManager.load("assets/sounds/Laser-Charge.mp3")
        self.laser_shoot_sound = SoundManager.load("assets/sounds/Laser-Shoot.wav")
        self.laser_charge_sound.set_volume(0.3)

        #self.prepare_laser_attack()

        self.buzz_sound =  SoundManager.load("assets/sounds/Wing-Buzz.mp3")
        self.buzz_sound.set_volume(0.4)

        self.since_last_attack_finish = 0
        self.since_laser_noise = 999
        self.swoop_above_player(False)
        self.since_spawn = 0
        self.enemy_wave_ct = 0

        self.since_hand_attack = 0

    def start_spawn_attack(self):

        self.boss_mode = c.BOSS_SPAWNING
        for hand in self.hands:
            hand.sprite.start_animation("Palm")
        self.spawn_enemies()

    def spawn_enemies(self):
        poses = [(-200, -200), (-200, 500), (c.WINDOW_WIDTH//2, -200), (c.WINDOW_WIDTH + 200, -200), (c.WINDOW_WIDTH + 200, 500)]
        if self.difficulty() < 0.1:
            poses = [(-200, -200), (c.WINDOW_WIDTH//2, -200), (c.WINDOW_WIDTH + 200, -200)]
        for pos in poses:
            pos = Camera.screen_to_world(pos)
            self.frame.enemies.append(Grunt(pos.get_position(), self.frame))

    def laser_attack_start(self):
        self.beam_length_sprite.start_animation("Beam")
        self.boss_mode = c.BOSS_FIRING_LASER
        self.frame.shake(amt=40)
        self.set_damaging(True)
        self.since_laser_noise = 999
        self.laser_shoot_sound.play(-1)


    def set_damaging(self, boolean):
        self.damaging = boolean
        for hand in self.hands:
            hand.damaging = boolean

    def prepare_laser_attack(self):
        self.sweep_target = 100
        self.boss_mode = c.BOSS_PREPARING_LASER
        self.sweep_position = Camera.world_to_screen(self.position.get_position()).x
        self.beam_sprite.start_animation("Charging")
        self.sweep_direction = c.RIGHT
        self.sweep_target_speed = 500
        self.set_damaging(False)
        self.laser_charge_sound.play()

        for hand in self.hands:
            hand.sprite.start_animation("Fist")

    def move_to_idle(self):
        self.boss_mode = c.BOSS_IDLE
        self.set_damaging(True)
        for hand in self.hands:
            hand.sprite.start_animation("Idle", restart_if_active=False)


    def swoop_above_player(self, play_sound=True):
        self.boss_mode = c.BOSS_SWOOPING
        self.set_damaging(False)

        self.laser_shoot_sound.stop()

        for hand in self.hands:
            hand.sprite.start_animation("Idle")

        if play_sound:
            self.buzz_sound.play()

    def update(self, dt, events):
        super().update(dt, events)
        if self.boss_mode == c.BOSS_SPAWNING:
            self.since_spawn += dt
            if self.since_spawn > 1:
                num_waves = math.ceil(self.difficulty() * 2.2) - 1
                if self.enemy_wave_ct < num_waves and len(self.frame.enemies) < 15:
                    self.since_spawn -= 1
                    self.enemy_wave_ct += 1
                    self.spawn_enemies()
                else:
                    if self.since_spawn > 5 and len(self.frame.enemies)<8:
                        self.enemy_wave_ct = 0
                        self.swoop_above_player()

        if self.boss_mode in [c.BOSS_FIRING_LASER, c.BOSS_PREPARING_LASER]:
            self.sprite.start_animation("Attack",restart_if_active=False)
        else:
            self.sprite.start_animation("Idle", restart_if_active=False)
        if self.boss_mode == c.BOSS_SWOOPING:
            if self.since_last_attack_finish > 2 - self.difficulty()*0.75:
                self.next_attack()
            target = self.frame.player.position + Pose((0, -500))
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
            self.hands[0].target_anchor = self.position + Pose((150, 120))
            self.hands[1].target_anchor = self.position + Pose((-150, 120))
        self.beam_sprite.update(dt, events)
        self.beam_length_sprite.update(dt, events)
        if self.boss_mode == c.BOSS_FIRING_LASER or self.boss_mode == c.BOSS_PREPARING_LASER:
            self.sweep_speed += (self.sweep_target_speed - self.sweep_speed) * 4 * dt
            self.position.y += (Camera.screen_to_world((0, 100)).y - self.position.y) * 5 * dt
            if self.sweep_direction==c.RIGHT:
                self.sweep_target_speed = 500 * (1 + self.difficulty()*2.5)
                self.position.x += self.sweep_speed*dt
                if Camera.world_to_screen((self.position.x, 0)).x > c.WINDOW_WIDTH - 100:
                    self.sweep_direction = c.LEFT
            else:
                self.sweep_target_speed = -500 * (1 + self.difficulty()*2.5)
                self.position.x += self.sweep_speed*dt
                if Camera.world_to_screen((self.position.x, 0)).x < -100:
                    self.swoop_above_player()
        if self.boss_mode == c.BOSS_PREPARING_LASER:
            self.sweep_position += (self.sweep_target - self.sweep_position) * 5 * dt
            self.position.x = Camera.screen_to_world((self.sweep_position, 0)).x
        print(self.boss_mode)
        self.since_hand_attack += dt
        if self.boss_mode == c.BOSS_HAND_ATTACK and self.since_hand_attack > 6:
            self.swoop_above_player()
            for hand in self.hands:
                hand.attacking = False
                hand.target_z = 0

    def difficulty(self):
        total_health = self.health + self.hands[0].health + self.hands[1].health
        total_max_health = self.max_health + self.hands[0].max_health + self.hands[1].max_health
        return (1 - (total_health / total_max_health))

    def next_attack(self):
        self.since_last_attack_finish = 0
        options = [self.prepare_laser_attack, self.start_spawn_attack]
        if any([not hand.destroyed for hand in self.hands]):
            options.append(self.hand_attack)
        random.choice(options)()

    def hand_attack(self):
        self.boss_mode = c.BOSS_HAND_ATTACK
        for hand in self.hands:
            hand.attacking = True
        self.since_hand_attack = 0

    def shadow_radius(self):
        return self.radius

    def shadow_offset(self):
        return 100

    def take_damage(self, amount):
        super().take_damage(amount)
        min_hp = 100
        if self.health < min_hp and (self.hands[0].health > 0 or self.hands[1].health > 0):
            self.health_recently_lost -= (min_hp - self.health)
            self.health = min_hp

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

    def destroy(self):
        super().destroy()
        self.death_sound.play()
        self.frame.flash(255)
        self.frame.healthbar.visible = False
        self.frame.boss_dead = True
        self.laser_shoot_sound.stop()



class Hand(Enemy):
    def __init__(self, position, frame, right=False):
        super().__init__(position, frame)
        idle = Animation.from_path("assets/images/boss hand idle.png",sheet_size=(2, 1),frame_count=2, reverse_x=(not right))
        palm = Animation.from_path("assets/images/boss palm.png", sheet_size=(2, 1), frame_count=2, reverse_x=(not right))
        fist = Animation.from_path("assets/images/boss fist.png", sheet_size=(2, 1), frame_count=2, reverse_x=(not right))
        self.sprite = Sprite(12)
        self.sprite.add_animation({
            "Fist":fist,
            "Palm":palm,
            "Idle":idle,
        },loop=True)
        self.sprite.start_animation("Idle")
        self.health = 5000
        self.max_health = self.health
        self.fixed = True
        self.offset = Pose((0, 0))
        self.age = 0
        self.target_offset = Pose((0, 0))
        self.anchor = self.position.copy()
        self.target_anchor = self.anchor.copy()
        self.right = right
        self.radius = 60
        self.z = 0
        self.target_z = 0
        self.raised = False
        self.attacking = False

        self.slam_timer = 0

    def shadow_radius(self):
        return 40

    def raise_up(self):
        self.target_z = 250
        self.raised = True
        self.damaging = False
        self.sprite.start_animation("Fist")
        self.target_anchor = self.frame.player.position.copy() + self.frame.player.velocity.copy() * 0.5 * self.frame.boss.difficulty()

    def slam_down(self):
        self.target_z = 0

    def land(self):
        self.damaging = True
        self.raised = False
        self.frame.shake(amt=30)
        for i in range(20):
            self.frame.particles.append(Puff(self.position.get_position()))


    def shadow_offset(self):
        if not self.z:
            return 70 - self.offset.y * 0.8
        else:
            return self.offset.y*0.8 + self.z

    def draw(self, surface, offset=(0, 0)):
        super().draw(surface, offset=(offset[0], offset[1] + self.z))

    def update(self, dt, events):
        if self.attacking:
            self.slam_timer += dt
            period = 2 / (1 + 1.25*self.frame.boss.difficulty())
            modded = self.slam_timer%period
            if self.right:
                modded += period/2
                modded %= period
            if modded < period/2 and not self.raised:
                self.raise_up()
            elif modded > period/2 and self.raised:
                self.slam_down()
        else:
            self.slam_timer = 0
        super().update(dt, events)
        if self.target_z > self.z:
            self.z += (self.target_z - self.z) * 5*dt
        elif self.target_z < self.z and self.raised and self.z > 0:
            self.z -= 3000*dt
            if self.z < self.target_z:
                self.z = self.target_z
                self.land()
        if self.z > 0:
            self.damaging = False
        self.age += dt
        if not self.attacking:
            self.target_offset = Pose((0, math.sin(self.age*3 + math.pi/4*self.right) * 50))
        else:
            self.target_offset = Pose((0, 15))
        do = self.target_offset - self.offset
        da = self.target_anchor - self.anchor
        self.anchor += da*10*dt
        self.offset += do*10*dt
        self.position = self.anchor + self.offset
        self.sprite.set_angle(math.cos(self.age*3 + math.pi/4*self.right) * 20 * (-1 + 2*self.right))
