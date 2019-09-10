from random import randint

from ppb.systemslib import System

from shooter.sprites import gameplay

__all__ = [
    "PowerUp"
]


class PowerUp(System):
    next_powerup = 15
    count = 0

    def on_enemy_killed(self, killed, signal):
        self.count += 1
        if self.count >= self.next_powerup:
            killed.scene.add(gameplay.PowerUp(position=killed.enemy.position))
            self.count = 0
            self.next_powerup += randint(-3, +3)
