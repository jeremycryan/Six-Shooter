from primitives import Pose
import constants as c

class Camera:
    position = None
    target = None

    @classmethod
    def init(cls, position=(0, 0)):
        cls.position = Pose(position)
        cls.target = cls.position.copy()

    @classmethod
    def update(cls, dt, events):
        d = cls.target - cls.position - Pose(c.WINDOW_SIZE) * 0.5
        speed = d*dt*4
        cls.position += speed

    @classmethod
    def screen_to_world(cls, position):
        return Pose(position) + cls.position

    @classmethod
    def world_to_screen(cls, position):
        return Pose(position) - cls.position