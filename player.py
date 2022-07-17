from pyracy.sprite_tools import Sprite, Animation
from primitives import Pose
import pygame
import constants as c
import math
from camera import Camera
from particle import Puff,MuzzleFlash,SparkParticle
from projectile import PistolBullet, Bread, Shuriken
import random
from sound_manager import SoundManager
from enemy import Grunt, BossMan, Hand

class Player:

    def __init__(self, frame):

        self.frame = frame
        self.position = Pose(c.ARENA_SIZE) * 0.5
        Camera.position = self.position.copy() - Pose(c.WINDOW_SIZE)*0.5
        self.velocity = Pose((0, 0))
        self.sprite = Sprite(12, (0, 0))
        self.hand_sprite = Sprite(12, (0, 0))
        self.populate_hand_sprite(self.hand_sprite)

        self.since_damage = 999
        self.dead = False

        self.health = 100
        self.max_health = 100

        walk_right = Animation.from_path(
            "assets/images/walk_right.png",
            sheet_size=(8, 1),
            frame_count=8,
        )
        walk_left = Animation.from_path(
            "assets/images/walk_right.png",
            sheet_size=(8, 1),
            frame_count=8,
            reverse_x=True,
        )
        idle_right = Animation.from_path(
            "assets/images/forward_idle.png",
            sheet_size=(8, 1),
            frame_count=8,
        )
        idle_left = Animation.from_path(
            "assets/images/forward_idle.png",
            sheet_size=(8, 1),
            frame_count=8,
            scale=1.0,
            reverse_x=True,
        )
        walk_back_right = Animation.from_path(
            "assets/images/walk_right_back.png",
            sheet_size=(8, 1),
            frame_count=8,

        )
        walk_back_left = Animation.from_path(
            "assets/images/walk_right_back.png",
            sheet_size=(8, 1),
            frame_count=8,
            reverse_x=True,
        )
        rolling = Animation.from_path(
            "assets/images/roll.png",
            sheet_size=(6, 1),
            frame_count=6,
        )
        dead = Animation.from_path(
            "assets/images/player_dead.png",
            sheet_size=(1, 1),
            frame_count=1,
        )
        take_damage_right = Animation.from_path(
            "assets/images/player_take_damage.png",
            sheet_size=(6, 1),
            frame_count=3,
        )
        take_damage_left = Animation.from_path(
            "assets/images/player_take_damage.png",
            sheet_size=(6, 1),
            frame_count=3,
            reverse_x=True,
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
        self.sprite.add_animation(
            {
                "Dead": dead,
                "TakeDamageRight": take_damage_right,
                "TakeDamageLeft": take_damage_left,
            },
            loop=False
        )

        self.number_surfs = {
            mode: pygame.image.load(f"assets/images/{mode}.png") for mode in c.VALID_MODES
        }

        self.since_roll_finish = 99

        self.sprite.add_animation({"Rolling": rolling})
        self.sprite.add_callback("Rolling", self.stop_rolling)
        self.sprite.add_callback("TakeDamageRight", self.stop_taking_damage)
        self.sprite.add_callback("TakeDamageLeft", self.stop_taking_damage)
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
        self.radius = 40

        self.death_sound = SoundManager.load("assets/sounds/Player-Death.mp3")

        self.shadow = pygame.Surface((self.radius*2, self.radius*2))
        self.shadow.fill((255, 255, 0))
        self.shadow.set_colorkey((255, 255, 0))
        pygame.draw.circle(self.shadow, (0, 0, 0), (self.radius, self.radius), self.radius)
        self.shadow.set_alpha(60)

        self.take_damage = SoundManager.load("assets/sounds/Taking-Damage.ogg")

        self.since_kick = 0
        self.roll_sound = SoundManager.load("assets/sounds/die_roll.mp3")
        self.footsteps = [SoundManager.load(f"assets/sounds/Footstep-{rel+1}.mp3") for rel in range(3)]
        for step in self.footsteps:
            step.set_volume(0.1)
        self.shots = [SoundManager.load(f"assets/sounds/Gatling-Gun-{rel+1}.mp3") for rel in range(3)]
        for shot in self.shots:
            shot.set_volume(0.3)
        self.shurikens = [SoundManager.load(f"assets/sounds/Shuriken-{rel+1}.mp3") for rel in range(3)]
        for shuriken in self.shurikens:
            shuriken.set_volume(0.3)
        self.pistols = [SoundManager.load(f"assets/sounds/Pistol_v2.mp3") for rel in range(3)]
        for shot in self.pistols:
            shot.set_volume(0.5)
        self.flame_bursts = [SoundManager.load(f"assets/sounds/Flame-Burst_v2.ogg") for rel in range(3)]
        for shot in self.flame_bursts:
            shot.set_volume(1)
        self.breads = [SoundManager.load(f"assets/sounds/Bread-{rel+1}.mp3") for rel in range(3)]
        for shot in self.breads:
            shot.set_volume(0.2)

        self.stamina_sprite = Sprite(16)
        stamina = Animation.from_path("assets/images/stam wheel.png", sheet_size=(16, 1), frame_count=15)
        stamina_idle = Animation.from_path("assets/images/stam wheel.png", sheet_size=(16, 1), frame_count=1)
        self.stamina_sprite.add_animation({"Stamina": stamina, "StaminaIdle": stamina_idle})
        self.stamina_sprite.start_animation("StaminaIdle")
        self.stamina_sprite.add_callback("Stamina", self.hide_stamina)

        # pygame.mixer.music.load("assets/sounds/Music-Intro.mp3")
        # pygame.mixer.music.play()

        self.stamina_visible = False

    def hide_stamina(self):
        self.stamina_visible = False

    def reset_stamina(self):
        self.stamina_visible = True
        self.stamina_sprite.start_animation("Stamina")


    def stop_taking_damage(self):
        self.animation_state = c.IDLE

    def get_hurt(self, direction=None):
        if self.since_damage < 1.25:
            return
        for enemy in self.frame.enemies[:]:
            if not isinstance(enemy, BossMan) and not isinstance(enemy, Hand) and not enemy.lethal and not enemy.destroyed and not self.rolling:
                enemy.lethal = True
                enemy.destroy()
        if direction:
            if not direction.magnitude():
                direction = Pose((1, 0))
            direction.scale_to(1600)
            self.velocity += direction
        self.take_damage.play()
        self.frame.damage_flash_alpha = 255
        self.frame.shake(direction, amt=30)
        self.since_damage = 0
        self.health -= 40
        self.animation_state = c.TAKING_DAMAGE
        if self.last_lr_direction == c.RIGHT:
            self.sprite.start_animation("TakeDamageRight")
        else:
            self.sprite.start_animation("TakeDamageLeft")

    def update(self, dt, events):
        self.stamina_sprite.update(dt, events)
        self.since_damage += dt
        self.health += 2*dt
        if self.health > self.max_health:
            self.health = self.max_health

        if self.rolling:
            if self.since_roll_finish != 0:
                self.since_roll_finish = 0
        else:
            self.since_roll_finish += dt
        self.last_fire += dt
        self.process_inputs(dt, events)
        self.sprite.set_position(self.position.get_position())
        was_firing = self.firing
        was_rolling = self.rolling
        self.sprite.update(dt, events)
        self.hand_sprite.update(dt, events)
        self.update_hand(dt, events)
        if not self.firing and was_firing:
            self.hand_sprite.update(0, events)
        elif not self.rolling and was_rolling:
            self.hand_sprite.update(0, events)
        mpos = Camera.screen_to_world(pygame.mouse.get_pos())
        Camera.target = self.position.copy() * 0.8 + mpos * 0.2
        if self.animation_state == c.WALKING:
            self.since_kick += dt
        if self.since_kick > 1/3 and self.velocity.magnitude() > 0:
            self.since_kick -= 1 / 3
            for i in range(3):
                start_position = self.position + self.velocity * (1/self.velocity.magnitude()) * 30
                start_position += Pose((random.random() * 10 - 5, random.random() * 10 - 5))
                start_velocity = self.velocity * -0.3
                start_velocity.rotate_position(20 * (i-1))
                self.frame.particles.append(Puff(start_position.get_position(), start_velocity.get_position()))
                random.choice(self.footsteps).play()
        if self.position.x - self.radius < 0:
            self.position.x = self.radius
        if self.position.x + self.radius > c.ARENA_WIDTH:
            self.position.x = c.ARENA_WIDTH - self.radius
        if self.position.y - self.radius < 0:
            self.position.y = self.radius
        if self.position.y + self.radius > c.ARENA_HEIGHT:
            self.position.y = c.ARENA_HEIGHT - self.radius

        hurt = False
        for enemy in self.frame.enemies:
            if self.rolling or self.dead:
                continue
            if not enemy.damaging or enemy.lethal or enemy.destroyed:
                continue
            if (enemy.position - self.position).magnitude() < enemy.radius + self.radius:
                self.get_hurt(self.position - enemy.position)
                hurt = True
                break
            if isinstance(enemy, BossMan):
                if enemy.boss_mode == c.BOSS_FIRING_LASER and abs(enemy.position.x - self.position.x) < 40:
                    self.get_hurt(Pose(((self.position - enemy.position).x, 0)))
                    enemy.swoop_above_player()

                    break
        if self.health < 0:
            if not self.dead:
                self.die()

    def die(self):
        self.dead = True
        self.death_sound.play()

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

        if (self.firing and self.weapon_mode == c.FIRE) or self.dead:
            direction = Pose((0, 0))

        old_state = self.animation_state

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not self.rolling and not self.dead and not self.stamina_visible:
                        self.roll(direction)
                if event.key == pygame.K_r and self.dead:
                    self.frame.restart()
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            if not self.rolling and not self.firing and not self.dead:
                self.fire()

        if self.rolling or self.animation_state == c.TAKING_DAMAGE:
            pass
        else:
            if direction.magnitude() > 0:
                direction.scale_to(1)
                self.velocity += direction * dt * 7500
                self.animation_state = c.WALKING
            elif not self.frame.damage_flash_alpha > 0:
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
            if direction.y >= 0:
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
            if self.dead:
                self.sprite.start_animation("Dead", restart_if_active=False)
            elif self.last_lr_direction == c.RIGHT:
                self.sprite.start_animation("IdleRight", restart_if_active=False, clear_time=False)
            else:
                self.sprite.start_animation("IdleLeft", restart_if_active=False, clear_time=False)
        elif self.animation_state == c.TAKING_DAMAGE:
            if self.last_lr_direction == c.RIGHT:
                self.sprite.start_animation("TakeDamageRight", restart_if_active=False)
            else:
                self.sprite.start_animation("TakeDamageLeft", restart_if_active=False)

        if self.velocity.magnitude() > 550 and not self.rolling and not self.frame.damage_flash_alpha > 0:
            self.velocity.scale_to(550)

        self.position += self.velocity * dt

    def roll(self, direction):
        self.last_fire = 999
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

        self.reset_stamina()
        self.animation_state = c.IDLE
        self.sprite.start_animation("IdleRight")
        for i in range(20):
            self.frame.particles.append(Puff(self.position.get_position()))
        modes_to_roll = [mode for mode in c.VALID_MODES if mode is not self.weapon_mode]
        if not len(modes_to_roll):
            modes_to_roll = c.VALID_MODES
        self.weapon_mode = random.choice(modes_to_roll)
        self.frame.shake(self.velocity,15)

    def draw(self, surface, offset=(0, 0)):

        if self.since_roll_finish < 0.5 and not self.rolling:
            if self.weapon_mode in self.number_surfs:
                num = self.number_surfs[self.weapon_mode]
                num.set_colorkey((255, 0, 255))
                scale = 1
                alpha = 1
                if self.since_roll_finish < 0.1:
                    scale = 1.5 - self.since_roll_finish*5
                    alpha = self.since_roll_finish*10
                elif self.since_roll_finish > 0.4:
                    scale = 1 - (self.since_roll_finish - 0.4) * 5
                    alpha = 1 - (self.since_roll_finish - 0.4) * 10
                w = int(num.get_width() * scale)
                h = int(num.get_height() * scale)
                num = pygame.transform.scale(num, (w, h))
                x = self.position.x - offset[0] - w//2
                y = self.position.y - offset[1] - h//2 - 90
                num.set_alpha(alpha*255)
                surface.blit(num, (x, y))

        surface.blit(self.shadow, (self.position.x - offset[0] - self.shadow.get_width()//2,
                                   self.position.y - offset[1] - self.shadow.get_height()//2 + 20))
        self.draw_hand(surface, offset, up=True)
        self.sprite.draw(surface, offset)
        self.draw_hand(surface, offset, up=False)

        if self.stamina_visible:
            stamina_offset = Pose((-50, -40))
            self.stamina_sprite.set_position((self.position + stamina_offset).get_position())
            self.stamina_sprite.draw(surface, offset)

    def populate_hand_sprite(self, hand_sprite):
        gun_idle_right = Animation.from_path(
            "assets/images/gun.png",
            sheet_size=(4, 1),
            frame_count=1,
        )
        gun_idle_left = Animation.from_path(
            "assets/images/gun.png",
            sheet_size=(4, 1),
            frame_count=1,
            reverse_x=True,
        )
        gun_fire_left = Animation.from_path(
            "assets/images/gun.png",
            sheet_size=(4, 1),
            frame_count=4,
            reverse_x=True,

            start_frame=1,
        )
        gun_fire_right = Animation.from_path(
            "assets/images/gun.png",
            sheet_size=(4,1),
            frame_count=4,

            start_frame=1,
        )
        gatling_idle_right = Animation.from_path(
            "assets/images/gatling_arm.png",
            sheet_size=(2, 1),
            frame_count=1,
        )
        gatling_idle_left = Animation.from_path(
            "assets/images/gatling_arm.png",
            sheet_size=(2, 1),
            frame_count=1,
            reverse_x=True,
        )
        gatling_fire_left = Animation.from_path(
            "assets/images/gatling_arm.png",
            sheet_size=(2, 1),
            frame_count=2,
            reverse_x=True,

        )
        gatling_fire_right = Animation.from_path(
            "assets/images/gatling_arm.png",
            sheet_size=(2,1),
            frame_count=2,
        )
        bread_fire_right = Animation.from_path(
            "assets/images/bread_arm.png",
            sheet_size=(4, 1),
            frame_count=4,

            start_frame=1,
        )
        bread_fire_left = Animation.from_path(
            "assets/images/bread_arm.png",
            sheet_size=(4, 1),
            frame_count=4,
            reverse_x=True,

            start_frame=1,
        )
        bread_idle_right = Animation.from_path(
            "assets/images/bread_arm.png",
            sheet_size=(4, 1),
            frame_count=1,
        )
        bread_idle_left = Animation.from_path(
            "assets/images/bread_arm.png",
            sheet_size=(4, 1),
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
        fire_idle_right = Animation.from_path(
            "assets/images/fire_arm.png",
            sheet_size=(14, 1),
            frame_count=2,
        )
        fire_idle_left = Animation.from_path(
            "assets/images/fire_arm.png",
            sheet_size=(14, 1),
            frame_count=2,
            reverse_x=True,
        )
        fire_fire_right = Animation.from_path(
            "assets/images/fire_arm.png",
            sheet_size=(14, 1),
            frame_count=10,
            start_frame=0,
        )
        fire_fire_left = Animation.from_path(
            "assets/images/fire_arm.png",
            sheet_size=(14, 1),
            frame_count=10,
            reverse_x=True,

            start_frame=0,
        )
        hand_sprite.add_animation(
            {
                "GunIdleLeft": gun_idle_left,
                "GunIdleRight": gun_idle_right,
                "BreadIdleRight": bread_idle_right,
                "BreadIdleLeft": bread_idle_left,
                "ShurikenIdleRight": shuriken_idle_right,
                "ShurikenIdleLeft": shuriken_idle_left,
                "FireIdleLeft": fire_idle_left,
                "FireIdleRight": fire_idle_right,
                "GatlingIdleRight": gatling_idle_right,
                "GatlingIdleLeft": gatling_idle_left,
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
                "FireFireRight": fire_fire_right,
                "FireFireLeft": fire_fire_left
            },
            loop=False
        )
        hand_sprite.add_animation(
            {
                "GatlingFireRight": gatling_fire_right,
                "GatlingFireLeft": gatling_fire_left,
            },
            fps_override=24,
            loop=True
        )
        hand_sprite.add_callback("GunFireRight",self.finish_firing)
        hand_sprite.add_callback("GunFireLeft", self.finish_firing)
        hand_sprite.add_callback("BreadFireRight",self.finish_firing)
        hand_sprite.add_callback("BreadFireLeft", self.finish_firing)
        hand_sprite.add_callback("ShurikenFireRight",self.finish_firing)
        hand_sprite.add_callback("ShurikenFireLeft", self.finish_firing)
        hand_sprite.add_callback("FireFireRight", self.finish_firing)
        hand_sprite.add_callback("FireFireLeft", self.finish_firing)
        hand_sprite.add_callback("GatlingFireRight", self.finish_firing)
        hand_sprite.add_callback("GatlingFireLeft", self.finish_firing)
        hand_sprite.start_animation("GunIdleRight")

        self.fire_sprite = Sprite(12)
        fire = Animation.from_path("assets/images/flame.png",sheet_size=(14, 1),frame_count=4)
        fire_vanish = Animation.from_path("assets/images/flame.png", sheet_size=(14, 1), frame_count=14, start_frame=2)
        self.fire_sprite.add_animation({
            "Idle": fire,
            "Vanish": fire_vanish,
        }, loop=False)
        self.fire_sprite.chain_animation("Idle", "Idle")
        self.fire_sprite.start_animation("Idle", restart_if_active=True)

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

        if self.weapon_mode == c.FIRE:
            self.fire_sprite.update(dt, events)

        if self.weapon_mode == c.GATLING and not self.rolling:
            if self.velocity.magnitude() > 160:
                self.velocity.scale_to(160)

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
            self.frame.projectiles.append(PistolBullet(offset.get_position(), relative.get_position(), self.frame))
            random.choice(self.pistols).play()
            knockback = relative * -1
            knockback.scale_to(500)
            self.frame.shake(direction=relative, amt=15)
            for i in range(8):
                self.frame.particles.append(SparkParticle(position=(self.hand_sprite.x, self.hand_sprite.y), velocity=relative.get_position(), duration=0.4, scale=20, color=(255, 180, 0)))
        elif self.weapon_mode == c.BREAD:
            self.knockback_velocity = 0
            if relative.x < 0:
                self.hand_sprite.start_animation("BreadFireLeft")
            else:
                self.hand_sprite.start_animation("BreadFireRight")
            self.frame.projectiles.append(Bread(offset.get_position(), relative.get_position(), self.frame))
        elif self.weapon_mode == c.GATLING:
            self.knockback_velocity = 200
            if relative.x < 0:
                self.hand_sprite.start_animation("GatlingFireLeft")
            else:
                self.hand_sprite.start_animation("GatlingFireRight")
            if self.velocity.magnitude() > 200:
                self.velocity.scale_to(200)
            muzzle_offset = self.position + Pose((math.cos(self.arm_angle*math.pi/180), -math.sin(self.arm_angle*math.pi/180))) * (self.aim_distance + 155) + Pose((0, 25))
            particle_offset = self.position + Pose(
                (math.cos(self.arm_angle * math.pi / 180), -math.sin(self.arm_angle * math.pi / 180))) * (
                                        self.aim_distance + 125) + Pose((0, 25))
            spark_offset = self.position + Pose(
                (math.cos(self.arm_angle * math.pi / 180), -math.sin(self.arm_angle * math.pi / 180))) * (
                                        self.aim_distance + 5) + Pose((0, 25))
            bullet_offset = self.position + Pose(
                (math.cos(self.arm_angle * math.pi / 180), -math.sin(self.arm_angle * math.pi / 180))) * (
                                        self.aim_distance + 125) + Pose((0, 25)) *0.5
            self.frame.particles.append(MuzzleFlash(muzzle_offset.get_position(), self.arm_angle, duration=0.03))
            bullet = PistolBullet(bullet_offset.get_position(), relative.get_position(), self.frame)
            random.choice(self.shots).play()
            bullet.damage = 40
            self.frame.projectiles.append(bullet)
            knockback = relative * -1
            knockback.scale_to(350)
            self.frame.shake(direction=relative, amt=10)
            for i in range(5):
                pass
                self.frame.particles.append(
                    SparkParticle(position=(particle_offset ).get_position(), velocity=relative.get_position(),
                                  duration=0.3, scale=25, color=(255, 180, 0)))
                self.frame.particles.append(
                    SparkParticle(position=(spark_offset).get_position(), velocity=relative.get_position(),
                                  duration=0.15, velocity_scale=0.6, scale=20, color=(255, 180, 0)))
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
            random.choice(self.shurikens).play()
        elif self.weapon_mode == c.FIRE:
            self.knockback_velocity = 0
            if relative.x < 0:
                self.hand_sprite.start_animation("FireFireLeft")
            else:
                self.hand_sprite.start_animation("FireFireRight")
            self.fire_sprite.start_animation("Vanish")

        self.velocity += knockback

    def finish_firing(self):
        self.firing = False

    def draw_hand(self, surface, offset=(0, 0), up=False):
        if self.rolling or self.dead:
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
        if self.weapon_mode == c.GATLING and not self.firing:
            if relative.x < 0:
                self.hand_sprite.start_animation("GatlingIdleLeft", restart_if_active=False)
            else:
                self.hand_sprite.start_animation("GatlingIdleRight", restart_if_active=False)
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
        if self.weapon_mode == c.FIRE and not self.firing:
            if relative.x < 0:
                self.hand_sprite.start_animation("FireIdleLeft", restart_if_active=False)
            else:
                self.hand_sprite.start_animation("FireIdleRight", restart_if_active=False)
            self.fire_sprite.start_animation("Idle", restart_if_active=False)


        self.hand_sprite.set_position((self.position + relative).get_position())
        if self.weapon_mode == c.GATLING:
            self.hand_sprite.y += 30

        self.hand_sprite.set_angle(sprite_angle)
        self.hand_sprite.update_image()
        self.hand_sprite.draw(surface, offset)
        if self.weapon_mode == c.FIRE and not (self.last_fire < c.COOLDOWNS[c.FIRE] and not self.firing):
            pos = self.position + relative
            self.fire_sprite.set_position(pos.get_position())
            self.fire_sprite.draw(surface, offset)