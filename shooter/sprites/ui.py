from ppb import Image
from ppb.features.animation import Animation

from shooter.events import SpawnPlayer
from shooter.sprites import SpriteRoot
from shooter.sprites.root import RunOnceAnimation

__all__ = [
    "Start"
]


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
