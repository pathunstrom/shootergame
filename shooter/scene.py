from ppb import BaseScene
from ppb import Vector
from ppb.buttons import Primary
from ppb.events import ButtonPressed
from ppb.events import StartScene
from ppb.events import ReplaceScene
from ppb.events import Update

from shooter.sprites import Start
from shooter.sprites import Player
from shooter.sprites import Level
from shooter.sprites import PowerUp
from shooter.values import color_dark
from shooter.values import grid_pixel_size
from shooter.values import splash_length

__all__ = [
    "Splash"
]


class BugFix(BaseScene):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_camera.pixel_ratio = grid_pixel_size


class Splash(BugFix):
    background_color = (101, 78, 163)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_time = 0

    def on_update(self, update: Update, signal):
        self.run_time += update.time_delta
        if self.run_time >= splash_length:
            signal(ReplaceScene(Menu, kwargs={"red": 1}))  # Working around a bug.


class Menu(BugFix):
    background_color = color_dark

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add(Start(), tags=["option"])

    def on_button_pressed(self, button_press: ButtonPressed, signal):
        if button_press.button != Primary:
            return
        for button in self.get(tag="option"):
            if (button.left < button_press.position.x < button.right
                    and button.top > button_press.position.y > button.bottom):
                signal(StartScene(Game, kwargs={"red": 1}))


class Game(BugFix):
    background_color = color_dark

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add(Player(), tags=["ship", "player"])
        self.add(Level(), tags=["level", "subsystem"])
