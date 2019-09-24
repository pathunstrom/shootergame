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
    place = 0

    def on_score_change(self, event, signal):
        self.update_image(event.score)

    def __repr__(self):
        return f"<Number image={self.image}, place={self.place}>"

    def update_image(self, score):
        self.image = self.numbers[((score // 10 ** self.place) % 10)]


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
