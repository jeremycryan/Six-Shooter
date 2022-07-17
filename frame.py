from player import Player
from camera import Camera
import constants as c
import pygame
from background import Background
from primitives import Pose
import math
from particle import SparkParticle
import random
from healthbar import BossHealthBar

from enemy import Grunt, BossMan

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


class Instructions(Frame):
    def __init__(self, game):
        self.game = game
        super().__init__()
        self.age = 0

    def load(self):
        self.instructions = pygame.image.load("assets/images/Instructions.png")
        self.shade = pygame.Surface(c.WINDOW_SIZE)
        self.shade.fill((0, 0, 0))
        self.shade_alpha = 255

    def update(self, dt, events):
        self.age += dt
        if self.age < 1.5 and self.age > 1.0:
            self.shade_alpha -= 600*dt
        elif self.age > 6:
            if self.shade_alpha < 0:
                self.shade_alpha = 0
            self.shade_alpha += 1000*dt
        if self.age > 7:
            self.done = True

    def next_frame(self):
        return GameFrame(self.game)

    def draw(self, surface, offset=(0, 0)):
        surface.blit(self.instructions, (0, 0))
        self.shade.set_alpha(self.shade_alpha)
        surface.blit(self.shade, (0, 0))




class GameFrame(Frame):
    def __init__(self, game):
        super().__init__()
        self.game = game

    def load(self):
        self.player = Player(self)
        self.enemies = [Grunt((200, c.ARENA_HEIGHT*0.2), self), Grunt((c.ARENA_WIDTH*2, c.ARENA_HEIGHT*0.7), self)]
        self.boss = BossMan((c.WINDOW_WIDTH//2, -2000), self)
        self.healthbar = BossHealthBar(self.boss)
        self.particles = []
        self.projectiles = []
        self.background = Background()
        self.red_flash = pygame.Surface(c.WINDOW_SIZE)
        self.red_flash.fill((255, 0, 0))
        self.red_flash_alpha = 0
        self.shake_amp = Pose((0, 0))
        self.since_shake = 0

        self.age = 0

        self.restarting = False


        self.white_flash = pygame.Surface(c.WINDOW_SIZE)
        self.white_flash.fill((255, 255, 255))
        self.white_flash_alpha = 0

        self.damage_flash = pygame.Surface(c.WINDOW_SIZE)
        self.damage_flash.fill((255, 255, 255))
        self.damage_flash_alpha = 0

        self.boss_dead = False
        self.since_boss_dead = 0
        self.since_player_died = 0

        self.shade = pygame.Surface(c.WINDOW_SIZE)
        self.shade.fill((0, 0, 0))
        self.shade_alpha = 255

        self.thanks = pygame.image.load("assets/images/thanks.png")
        self.youdied = pygame.image.load("assets/images/youdied.png")


    def update(self, dt, events):

        Camera.update(dt, events)

        self.background.update(dt, events)
        self.player.update(dt, events)
        self.since_shake += dt

        if not self.game.tutorial:
            self.age += dt
        if self.age > 11 and not self.boss in self.enemies and not self.boss_dead:
            self.enemies.append(self.boss)
            self.healthbar.visible = True
            if not self.game.main_music_started:
                pygame.mixer.music.load("assets/sounds/Music-Main-Loop.mp3")
                pygame.mixer.music.play(loops=-1)
                pygame.mixer.music.set_volume(0.4)
                self.game.main_music_started = True
                self.game.intro_music.fadeout(800)

        if not self.restarting:
            self.shade_alpha -= 1000*dt
        else:
            if self.shade_alpha < 0:
                self.shade_alpha = 0
            self.shade_alpha += 1000*dt
        if self.shade_alpha > 255 and self.restarting:
            self.done = True

        if self.boss_dead:
            self.since_boss_dead += dt
        if self.player.dead:
            self.since_player_died += dt

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
        self.white_flash_alpha -= 5*dt
        self.white_flash_alpha *= 0.2**dt
        self.damage_flash_alpha -= 500*dt
        self.damage_flash_alpha *= 0.01**dt
        if self.player.weapon_mode == c.FIRE and self.player.firing and int(self.player.hand_sprite.get_frame_num()) == 7 and self.red_flash_alpha < 10:
            self.red_flash_alpha = 255
            self.shake(direction=None, amt=30)
            for i in range(16):
                position = self.player.hand_sprite.x, self.player.hand_sprite.y
                self.particles.append(SparkParticle(position))
            random.choice(self.player.flame_bursts).play()
            for enemy in self.enemies:
                if enemy.lethal or enemy.destroyed:
                    return
                pos_on_screen = Camera.world_to_screen(enemy.position.get_position())
                if pos_on_screen.x > 0 and pos_on_screen.x < c.WINDOW_WIDTH:
                    if pos_on_screen.y > 0 and pos_on_screen.y < c.WINDOW_HEIGHT:
                        enemy.take_damage(250)

    def flash(self, alpha=255):
        self.white_flash_alpha = alpha

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

    def restart(self):
        self.restarting = True



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

        self.healthbar.draw(surface, offset)

        if self.red_flash_alpha > 0:
            self.red_flash.fill((self.red_flash_alpha, 0.25*self.red_flash_alpha, 0))
            surface.blit(self.red_flash, (0, 0), special_flags=pygame.BLEND_ADD)

        if self.boss_dead and self.since_boss_dead > 3:
            thanks_alpha = min(((self.since_boss_dead - 3) * 255), 128)
            self.thanks.set_alpha(thanks_alpha)
            surface.blit(self.thanks, (0, 0))

        if self.since_player_died > 0:
            thanks_alpha = min(((self.since_player_died) * 255), 128)
            self.youdied.set_alpha(thanks_alpha)
            surface.blit(self.youdied, (0, 0))

        if self.white_flash_alpha > 0:
            self.white_flash.set_alpha(self.white_flash_alpha)
            surface.blit(self.white_flash, (0, 0))
            for enemy in self.enemies[:]:
                if not isinstance(enemy, BossMan):
                    self.enemies.remove(enemy)

        if self.damage_flash_alpha > 0:
            self.damage_flash.set_alpha(self.damage_flash_alpha)
            surface.blit(self.damage_flash, (0, 0))

        if self.shade_alpha > 0:
            self.shade.set_alpha(self.shade_alpha)
            surface.blit(self.shade, (0, 0))

    def shake(self, direction=None, amt=15):
        direction = direction.copy() if direction is not None else Pose((1, -1))
        direction.scale_to(amt)
        if direction.magnitude() > self.shake_amp.magnitude():
            self.shake_amp = direction
            self.since_shake = 0

    def next_frame(self):
        return GameFrame(self.game)