from pyracy.sprite_tools import Sprite, Animation
from primitives import Pose
import constants as c

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

    def get_hit_by(self, projectile):
        if projectile.damage:
            self.take_damage(projectile.damage)
        projectile.hit(self)

    def take_damage(self, amount):
        self.health -= amount

    def draw(self, surface, offset=(0, 0)):
        position_and_offset = Pose(offset)*-1 + self.position
        if position_and_offset.x < -self.radius*2 or position_and_offset.x > c.WINDOW_WIDTH + self.radius*2 :
            return
        if position_and_offset.y < -self.radius*2  or position_and_offset.y > c.WINDOW_HEIGHT + self.radius*2 :
            return
        self.sprite.set_position(self.position.get_position())
        self.sprite.draw(surface, offset=offset)

    def update(self, dt, events):
        self.sprite.update(dt, events)
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
                                        reverse_x = True)
        die_left = Animation.from_path("assets/images/bug_dying.png",
                                        sheet_size=(3, 1),
                                        frame_count=3,
                                        reverse_x = False)
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
        for key in ["DieRight", "DieLeft"]:
            self.sprite.add_callback(key, self.destroy_me_for_real)
        self.direction_lr = c.RIGHT if self.velocity.x > 0 else c.LEFT
        if self.direction_lr == c.RIGHT:
            self.sprite.start_animation("BuzzRight")
        else:
            self.sprite.start_animation("BuzzLeft")

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