from ppb import Image
from ppb.features.animation import Animation

from shooter.events import SpawnPlayer
from shooter.sprites import SpriteRoot
from shooter.sprites.root import RunOnceAnimation

__all__ = [
    "Start"
]


class Number(SpriteRoot):
    numbers = [
        Image(f"shooter/resources/font/{x}.png")
        for x in range(10)
    ]
    image = numbers[0]
    size = 0.75
    value_function = None

    def on_score_change(self, event, signal):
        self.image = self.numbers[self.value_function(event.score)]

    def __repr__(self):
        return f"Number<{self.numbers.index(self.image)}>"


class LifeSymbol(SpriteRoot):
    image = Image("shooter/resources/ship/g0e0.png")
    symbol_explodes = Animation("shooter/resources/explosions/player/sprite_{1..7}.png", 12)
    size = 0.5

    def kill(self, scene):
        scene.add(RunOnceAnimation(
            position=self.position,
            image=self.symbol_explodes,
            end_event=SpawnPlayer()
        ))
        scene.remove(self)


class Start(SpriteRoot):
    image = Image("shooter/resources/start.png")
    size = 4
