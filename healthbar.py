import pygame
import constants as c
from primitives import Pose
import time
import math



class BossHealthBar:

    def __init__(self, boss):
        self.boss = boss
        self.background = pygame.image.load("assets/images/boss_bar.png")
        self.head_bar = pygame.image.load("assets/images/boss_hp.png")
        self.head_bar_blink = pygame.image.load("assets/images/boss_hp_blink.png")
        self.head_bar.set_colorkey((255, 0, 255))
        self.hand_bar_left = pygame.image.load("assets/images/boss_hand_hp_left.png")
        self.hand_bar_left_blink = pygame.image.load("assets/images/boss_hand_hp_left_blink.png")
        self.hand_bar_left_blink.set_colorkey((255, 0, 255))
        self.hand_bar_left.set_colorkey((255, 255, 255))
        self.hand_bar_right = pygame.transform.flip(self.hand_bar_left, 1, 0)
        self.hand_bar_right_blink = pygame.transform.flip(self.hand_bar_left_blink, 1, 0)
        self.hands = pygame.image.load("assets/images/boss bar hands.png")

        self.player_bar = pygame.image.load("assets/images/hp_bar_front.png")
        self.player_bar_back = pygame.image.load("assets/images/hp_bar_back.png")
        self.player_bar_front_low = pygame.image.load("assets/images/hp_bar_front_low.png")
        self.player_bar.set_colorkey((255, 0, 255))

        self.visible = False

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        x, y = c.WINDOW_WIDTH//2 - self.player_bar_back.get_width()//2, 20
        surface.blit(self.player_bar_back, (x, y))
        x+=55
        y += 16
        w = int(self.player_bar.get_width() *self.boss.frame.player.health/100)
        h = self.player_bar.get_height()
        if self.boss.frame.player.health > 40:
            surface.blit(self.player_bar, (x, y), (0, 0, w, h))
        elif w>0:
            surface.blit(self.player_bar_front_low, (x, y), (0, 0, w, h))

        if not self.visible:
            return

        bx = c.WINDOW_WIDTH//2 - self.background.get_width()//2
        by = self.background.get_height()//2  - self.background.get_height()//2 + c.WINDOW_HEIGHT - 175

        surface.blit(self.background, (bx, by))

        x = c.WINDOW_WIDTH//2 - self.head_bar.get_width()//2
        y = self.head_bar.get_height()//2  - self.head_bar.get_height()//2 + c.WINDOW_HEIGHT - 127
        w = int(self.head_bar.get_width() * self.boss.health/self.boss.max_health)
        h = self.head_bar.get_height()
        if w>0:
            surface.blit(self.head_bar, (x, y), (0, 0, w, h))
            if self.boss.health_recently_lost:
                sliver = self.head_bar_blink.subsurface((w, 0, self.head_bar.get_width()*self.boss.health_recently_lost/self.boss.max_health, h)).copy()
                sliver.set_colorkey((255, 0, 255))
                surface.blit(sliver, (x+w, y))

        x = c.WINDOW_WIDTH//2 - self.hand_bar_left.get_width()//2 - 213
        y = self.hand_bar_left.get_height()//2  - self.hand_bar_left.get_height()//2 + c.WINDOW_HEIGHT - 86
        w = int(self.hand_bar_left.get_width() * self.boss.hands[1].health/self.boss.hands[1].max_health)
        h = self.hand_bar_left.get_height()
        if w>0:
            surface.blit(self.hand_bar_left, (x, y), (0, 0, w, h))
            if self.boss.hands[1].health_recently_lost:
                sliver = self.hand_bar_left_blink.subsurface((w, 0, self.hand_bar_left_blink.get_width()*self.boss.hands[1].health_recently_lost/self.boss.hands[1].max_health, h)).copy()
                sliver.set_colorkey((255, 0, 255))
                surface.blit(sliver, (x+w, y))

        x = c.WINDOW_WIDTH//2 - self.hand_bar_left.get_width()//2 + 213
        y = self.hand_bar_left.get_height()//2  - self.hand_bar_left.get_height()//2 + c.WINDOW_HEIGHT - 86
        w = int(self.hand_bar_right.get_width() * self.boss.hands[0].health/self.boss.hands[0].max_health)
        h = self.hand_bar_right.get_height()
        if w>0:
            surface.blit(self.hand_bar_right, (x, y), (0, 0, w, h))
            if self.boss.hands[0].health_recently_lost:
                sliver = self.hand_bar_right_blink.subsurface((w, 0, self.hand_bar_right_blink.get_width()*self.boss.hands[0].health_recently_lost/self.boss.hands[0].max_health, h)).copy()
                sliver.set_colorkey((255, 0, 255))
                surface.blit(sliver, (x+w, y))

        surface.blit(self.hands, (bx+3, by + 3*math.sin(time.time()*10)))