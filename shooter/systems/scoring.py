from math import pow

from ppb import events as ppb_events
from ppb import Vector
from ppb.systemslib import System

from shooter import events as shooter_events
from shooter import scene as scenes
from shooter.sprites import ui


__all__ = ["ScoringSystem"]


def _generate_value_function(place_value):
    def _value_function(score):
        return int((score // place_value) % 10)
    return _value_function


class ScoringSystem(System):
    high_score = 0
    score = 0
    last_score = 0

    @staticmethod
    def generate_score_board(scene, start_position, score):
        last_number = None
        for x in range(6, -1, -1):
            place_value = 10**x
            value_function = _generate_value_function(place_value)
            number = ui.Number(image=ui.Number.numbers[value_function(score)],
                               value_function=value_function)
            if last_number is None:
                number.position = start_position
            else:
                number.center = last_number.center
                number.left = last_number.right
            scene.add(number)
            last_number = number

    def on_idle(self, _, signal):
        if self.last_score != self.score:
            signal(shooter_events.ScoreChange(self.score))
            self.last_score = self.score

    def on_enemy_killed(self, event: shooter_events.EnemyKilled, signal):
        self.score += event.enemy.points

    def on_scene_started(self, event: ppb_events.SceneStarted, signal):
        if isinstance(event.scene, scenes.Menu):
            # We want to put the highscore low on the screen.
            self.generate_score_board(event.scene, Vector(ui.Number.size * -3, -5), self.high_score)
        if isinstance(event.scene, scenes.Game):
            self.generate_score_board(event.scene, Vector(0, 9.5), self.score)
