from random import choice
from random import randint

from ppb.systemslib import System

from shooter.sprites import gameplay

__all__ = [
    "PowerUp"
]


class PowerUp(System):
    max_time_between_powerups = 40
    minimum_time_between_powerups = 10
    max_change_between_powerups = 6
    next_powerup = 10
    choice_function = choice
    randint_function = randint
    count = 0

    def on_enemy_killed(self, killed, signal):
        self.count += killed.enemy.upgrade_points

        if self.count >= self.next_powerup:
            power_up = self.choice_function(list(gameplay.PowerUps))
            killed.scene.add(gameplay.PowerUp(
                position=killed.enemy.position,
                kind=power_up
            ))
            self.count = 0
            self.next_powerup += self.randint_function(-self.max_change_between_powerups,
                                                       self.max_change_between_powerups)
            if self.next_powerup > self.max_time_between_powerups:
                self.next_powerup = self.max_time_between_powerups
            elif self.next_powerup < self.minimum_time_between_powerups:
                self.next_powerup = self.minimum_time_between_powerups
