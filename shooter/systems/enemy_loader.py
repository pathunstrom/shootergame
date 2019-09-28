from enum import Enum
from typing import Iterable
from typing import NamedTuple
from typing import Tuple
from random import choice
from random import random as rand

from ppb import Vector
from ppb import events
from ppb.systemslib import System

from shooter.sprites import gameplay as game_sprites

__all__ = [
    "Strategies",
    "EnemyLoader"
]


class Formation(NamedTuple):
    name: str
    spread: int
    ships: Iterable[str]
    offsets: Iterable[Vector]
    difficulty_floor: int = 0


enemy_types = {
    "patrol": game_sprites.PatrolShip,
    "cargo": game_sprites.CargoShip,
}


default_formations = (
    Formation(
        "convoy",
        1,
        ["cargo", "cargo", "cargo"],
        [Vector(0, 0), Vector(0, 3), Vector(0, 6)]
    ),
    Formation(
        "patrol group",
        5,
        ["patrol", "patrol", "patrol"],
        [Vector(0, 0), Vector(-2, 1), Vector(2, 1)]
    ),
)


class NoStrategy:

    def __init__(self, formations):
        self.formations = formations

    def advance(self, time_delta, scene):
        pass

    def spawn_formation(self, scene):
        pass

    def calculate_next_spawn(self):
        pass


class EndlessStrategy(NoStrategy):
    next_spawn_time = 1.5
    counter = 0

    def advance(self, time_delta, scene):
        self.counter += time_delta
        while self.counter >= self.next_spawn_time:
            self.spawn_formation(scene)
            self.calculate_next_spawn()

    def spawn_formation(self, scene):
        formation = choice(self.formations)
        span = formation.spread
        modifiers = formation.offsets
        ships = formation.ships
        min_x = -5 + (span/2)
        spawn_x = min_x + (rand() * (10 - span))
        origin = Vector(spawn_x, 10)
        for modifier, ship in zip(modifiers, ships):
            scene.add(enemy_types[ship](position=origin + modifier), tags=["enemy", "ship"])

    def calculate_next_spawn(self):
        self.next_spawn_time += 5


class Strategies(Enum):
    NONE = NoStrategy
    ENDLESS = EndlessStrategy


class EnemyLoader(System):
    """
    Spawns enemies based on either an input file or an algorithmic
    "endless" mode.
    """
    strategy = NoStrategy(())

    def __init__(self, *, formations=default_formations, **kwargs):
        super().__init__(formations=formations, **kwargs)
        self.formations = list(formations)

    def on_scene_started(self, started: events.SceneStarted, signal):
        self.manage_strategy(started.scene)

    def on_scene_continued(self, continued: events.SceneContinued, signal):
        self.manage_strategy(continued.scene)

    def manage_strategy(self, scene):
        strategy = getattr(scene, "spawn_strategy", Strategies.NONE).value
        self.strategy = strategy(self.formations)

    def on_idle(self, idle: events.Idle, signal):
        self.strategy.advance(idle.time_delta, idle.scene)
