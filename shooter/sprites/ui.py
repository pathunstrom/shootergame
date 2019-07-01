from shooter.events import SpawnPlayer
from shooter.sprites import SpriteRoot

__all__ = [
    "Start"
]


class LifeSymbol(SpriteRoot):
    image = "../resources/ship/g0e0.png"
    size = 0.5

    def kill(self, scene):
        scene.add(LifeSymbolExplodes(position=self.position))
        scene.remove(self)


class LifeSymbolExplodes(SpriteRoot):

    def on_update(self, update, signal):
        update.scene.remove(self)
        signal(SpawnPlayer())


class Start(SpriteRoot):
    image = "../resources/start.png"
    size = 4
