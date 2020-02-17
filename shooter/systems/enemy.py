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
    "message": Sound("shooter/resources/sound/enemy-alerted.wav")
}


class Formation(NamedTuple):
    name: str
    spread: int
    ships: Iterable[str]
    offsets: Iterable[Vector]
    difficulty_floor: int = 0
    difficulty_ceiling: int = 1000000  # Arbitrarily large.


enemy_types = {
    "patrol": game_sprites.PatrolShip,
    "cargo": game_sprites.CargoShip,
    "escort": game_sprites.EscortFrigate,
    "zero": game_sprites.Zero,
    "ace": game_sprites.Ace,
}


default_formations: Iterable[Formation] = (
    Formation(
        "cargo ship",
        1,
        ["cargo"],
        [Vector(0, 0)],
        10,
        30
    ),
    Formation(
        "scout",
        1,
        ["patrol"],
        [Vector(0, 0)],
        15,
        40,
    ),
    Formation(
        "convoy",
        1,
        ["cargo", "cargo", "cargo"],
        [Vector(0, 0), Vector(0, 3), Vector(0, 6)],
        25,
        50,
    ),
    Formation(
        "patrol group",
        5,
        ["patrol", "patrol", "patrol"],
        [Vector(0, 0), Vector(-2, 1), Vector(2, 1)],
        35,
        75,
    ),
    Formation(
        "escorted convoy",
        3,
        ["cargo", "escort", "cargo", "cargo"],
        [Vector(0, 0), Vector(3, 0), Vector(0, 3), Vector(0, 6)],
        45,
        100
    ),
    Formation(
        "escort",
        1,
        ["escort"],
        [Vector(0, 0)],
        35,
    ),
    Formation(
        "zero",
        1,
        ["zero"],
        [Vector(0, 0)],
        75,
    ),
    Formation(
        "strike team",
        3,
        ["zero", "zero"],
        [Vector(-1, 0), Vector(1, 0)],
        90,
    ),
    Formation(
        "clean up",
        4,
        ["escort", "zero", "zero"],
        [Vector(0, 0), Vector(-1.5, 0), Vector(1.5, 0)],
        125,
    ),
    Formation(
        "it's a trap!",
        6,
        ["cargo", "cargo", "cargo", "zero", "zero", "zero", "zero"],
        [Vector(0, 0), Vector(0, 2), Vector(0, 4), Vector(-2.5, 4), Vector(-2.5, 6), Vector(2.5, 4), Vector(2.5, 6)],
        150
    ),
    Formation(
        "ace",
        1,
        ["ace"],
        [Vector(0, 0)],
        125
    ),
    Formation(
        "death squad",
        5,
        ["ace", "escort", "zero", "zero"],
        [Vector(0, 5), Vector(0, 0), Vector(-2, 7), Vector(2, 7)],
        160,
    ),
)


class NoStrategy:
    paused = False

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

    def pause(self):
        """
        Strategies are paused until the screen clears.
        """
        self.paused = True

    def unpause(self):
        self.paused = False


class EndlessStrategy(NoStrategy):
    next_spawn_time = 0.5
    counter = 0
    danger = 10
    danger_counter = 0
    danger_advancement_rate = 10

    @property
    def minimum_ships(self):
        return self.danger / 10

    @property
    def maximum_ships(self):
        return int(self.danger / 9)

    def advance(self, time_delta, scene):
        if self.paused:
            return
        self.counter += time_delta
        self.danger_counter += time_delta
        enemies = list(scene.get(kind=game_sprites.EnemyShip))
        if self.counter >= self.next_spawn_time and len(enemies) < self.maximum_ships:
            self.spawn_formation(scene)
            self.calculate_next_spawn()
        if self.danger_counter >= self.danger_advancement_rate:
            self.danger += 1
            self.danger_counter = 0

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
        if self.strategy.paused:
            if not list(idle.scene.get(tag="enemy")):
                self.strategy.unpause()
                signal(s_events.EnemiesClear())

    def on_enemy_alerted(self, enemy_alerted, signal):
        self.strategy.alerted(enemy_alerted, signal)

    def on_player_died(self, died: s_events.PlayerDied, signal):
        self.strategy.pause()


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

    def on_enemy_escaped(self, escaped: s_events.EnemyEscaped, signal):
        self.on_enemy_alerted(s_events.EnemyAlerted(escaped.enemy, scene=escaped.scene), signal)
