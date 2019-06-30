from ppb import events
from ppb.systems import System

from shooter import values
from shooter.sprites import gameplay as game_sprites
from shooter.systems.controller import *
from shooter.systems.enemy_loader import *


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
