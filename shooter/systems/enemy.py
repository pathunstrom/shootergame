from enum import Enum
from typing import Iterable
from typing import NamedTuple
from random import choice
from random import random as rand

from ppb import Sound
from ppb import Vector
from ppb import events as ppb_events
from ppb.systemslib import System

from shooter import events as s_events
from shooter.sprites import gameplay as game_sprites


__all__ = [
    "Strategies",
    "EnemyComms",
    "EnemyLoader",
]


sounds = {
    "message": Sound("shooter/resources/sound/message.wav")
}


class Formation(NamedTuple):
    name: str
    spread: int
    ships: Iterable[str]
    offsets: Iterable[Vector]
    difficulty_floor: int = 0
    difficulty_ceiling: int = 1000000 # Arbitrarily large.


enemy_types = {
    "patrol": game_sprites.PatrolShip,
    "cargo": game_sprites.CargoShip,
    "escort": game_sprites.EscortFrigate,
}


default_formations: Iterable[Formation] = (
    Formation(
        "cargo ship",
        1,
        ["cargo"],
        [Vector(0, 0)],
        0,
        3
    ),
    Formation(
        "scout",
        1,
        ["patrol"],
        [Vector(0, 0)],
        0,
        5
    ),
    Formation(
        "convoy",
        1,
        ["cargo", "cargo", "cargo"],
        [Vector(0, 0), Vector(0, 3), Vector(0, 6)],
        3,
        10,
    ),
    Formation(
        "patrol group",
        5,
        ["patrol", "patrol", "patrol"],
        [Vector(0, 0), Vector(-2, 1), Vector(2, 1)],
        5,
        15,
    ),
    Formation(
        "escorted convoy",
        3,
        ["cargo", "escort", "cargo", "cargo"],
        [Vector(0, 0), Vector(3, 0), Vector(0, 3), Vector(0, 6)],
        10,
        20
    ),
    Formation(
        "escort",
        1,
        ["escort"],
        [Vector(0, 0)],
        15,
    ),
)


class NoStrategy:

    def __init__(self, formations):
        self.formations: Iterable[Formation] = formations

    def advance(self, time_delta, scene):
        pass

    def spawn_formation(self, scene):
        pass

    def calculate_next_spawn(self):
        pass

    def alerted(self, event, signal):
        pass


class EndlessStrategy(NoStrategy):
    next_spawn_time = 0.5
    counter = 0
    danger = 1

    @property
    def minimum_ships(self):
        return self.danger

    @property
    def maximum_ships(self):
        return int(self.danger + (self.danger * 0.25) + 1)

    def advance(self, time_delta, scene):
        self.counter += time_delta
        enemies = list(scene.get(kind=game_sprites.EnemyShip))
        if self.counter >= self.next_spawn_time and len(enemies) < self.maximum_ships:
            self.spawn_formation(scene)
            self.calculate_next_spawn()

    def spawn_formation(self, scene):
        formations = [f for f in self.formations if f.difficulty_floor <= self.danger <= f.difficulty_ceiling]
        if not formations:
            return
        formation = choice(formations)
        span = formation.spread
        modifiers = formation.offsets
        ships = formation.ships
        min_x = -5 + (span/2)
        spawn_x = min_x + (rand() * (10 - span))
        origin = Vector(spawn_x, 10)
        for modifier, ship in zip(modifiers, ships):
            scene.add(enemy_types[ship](position=origin + modifier), tags=["enemy", "ship"])

    def calculate_next_spawn(self):
        self.next_spawn_time += 0.75

    def alerted(self, event, signal):
        self.danger += 1


class Strategies(Enum):
    NONE = NoStrategy
    ENDLESS = EndlessStrategy


class EnemyLoader(System):
    """
    Spawns enemies based on either an input file or an algorithmic
    "endless" mode.
    """
    strategy = NoStrategy(())

    def __init__(self, *, formations=None, **kwargs):
        if formations is None:
            formations = default_formations
        super().__init__(formations=formations, **kwargs)
        self.formations = list(formations)

    def on_scene_started(self, started: ppb_events.SceneStarted, signal):
        self.manage_strategy(started.scene)

    def on_scene_continued(self, continued: ppb_events.SceneContinued, signal):
        self.manage_strategy(continued.scene)

    def manage_strategy(self, scene):
        strategy = getattr(scene, "spawn_strategy", Strategies.NONE).value
        self.strategy = strategy(self.formations)

    def on_idle(self, idle: ppb_events.Idle, signal):
        self.strategy.advance(idle.time_delta, idle.scene)

    def on_enemy_alerted(self, enemy_alerted, signal):
        self.strategy.alerted(enemy_alerted, signal)


class EnemyComms(System):

    def on_enemy_killed(self, killed: s_events.EnemyKilled, signal):
        if isinstance(killed.enemy, game_sprites.CargoShip):
            killed.scene.add(game_sprites.Beacon(position=killed.enemy.position))

    def on_enemy_alerted(self, alert: s_events.EnemyAlerted, signal):
        """
        Emit a radio signal on death. This is mostly for a visual
        cue for the player.
        """
        alert.scene.add(game_sprites.Alert(position=alert.source.position))
        signal(ppb_events.PlaySound(sounds["message"]))
