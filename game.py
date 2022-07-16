import constants as c
import pygame
from frame import Frame, GameFrame
import sys
from camera import Camera
from sound_manager import SoundManager


class Game:

    def __init__(self):
        pygame.init()
        if c.FULLSCREEN:
            self.screen = pygame.display.set_mode(c.WINDOW_SIZE, flags=pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(c.WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.reticle = pygame.image.load("assets/images/reticle.png")
        pygame.mouse.set_visible(False)
        Camera.init()
        SoundManager.init()

    def main(self):
        current_frame = GameFrame()
        current_frame.load()
        self.clock.tick(60)

        while True:
            dt, events = self.get_events()
            if dt > 0.05:
                dt = 0.05
            current_frame.update(dt, events)
            current_frame.draw(self.screen, (0, 0))
            self.draw_reticle(self.screen)
            pygame.display.flip()

            if current_frame.done:
                current_frame = current_frame.next_frame()
                current_frame.load()

    def draw_reticle(self, surface, offset=(0, 0)):
        x, y = pygame.mouse.get_pos()
        surface.blit(self.reticle, (x - self.reticle.get_width(), y - self.reticle.get_height()))

    def get_events(self):
        dt = self.clock.tick(c.FRAMERATE)/1000


        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        Camera.update(dt, events)

        return dt, events


if __name__=="__main__":
    game = Game()
    game.main()