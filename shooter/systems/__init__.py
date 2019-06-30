from random import choice
from random import random as rand

from ppb import Vector
from ppb import events
from ppb.systems import System

from shooter import values
from shooter.sprites import gameplay as game_sprites
from shooter.systems.controller import *

default_formations = (
    (5, Vector(0, 0), Vector(-2, 1), Vector(2, 1)),
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
        span, *modifiers = formation
        min_x = -span / 2
        spawn_x = min_x + (rand() * (10 - span))
        origin = Vector(spawn_x, 10)
        for modifier in modifiers:
            scene.add(game_sprites.EnemyShip(position=origin + modifier), tags=["enemy", "ship"])

    def calculate_next_spawn(self):
        self.next_spawn_time += 5


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
        strategy = getattr(started.scene, "spawn_strategy", None)
        if strategy == "endless":
            self.strategy = EndlessStrategy(self.formations)
        else:
            self.strategy = NoStrategy(self.formations)

    def on_idle(self, idle: events.Idle, signal):
        self.strategy.advance(idle.time_delta, idle.scene)


class LifeCounter(System):
    primed = False
    lives = values.player_starting_lives

    def on_idle(self, idle: events.Idle, signal):
        if self.primed and self.lives:
            idle.scene.add(game_sprites.Player())
            self.primed = False

    def on_player_died(self, died, signal):
        self.lives -= 1
        self.primed = True
