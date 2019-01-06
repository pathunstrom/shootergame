from random import random as rand
from random import choice

from ppb import Vector
from ppb import events as event
from ppb import flags as flag

from shooter import SpriteRoot
from shooter.controller import Controller
from shooter.events import Shoot


class Ship(SpriteRoot):
    health = 100
    speed = 3
    heading = Vector(0, 1)

    def damage(self, damage, type=None):
        if type is None:
            self.health -= damage

    def move(self, time_delta):
        self.position += self.heading * time_delta * self.speed


class Bullet(SpriteRoot):
    size = 0.25
    speed = 10
    heading = Vector(0, -1)
    target = "enemy"
    intensity = 1

    def on_update(self, update: event.Update, signal):
        self.position += self.heading * update.time_delta * self.speed
        for target in update.scene.get(tag="enemy"):
            if self.collides_with(target):
                update.scene.remove(self)
                target.damage(self.intensity)


class EnemyShip(Ship):
    health = 1
    image = "enemy/t0.png"

    def on_update(self, update: event.Update, signal):
        if self.health <= 0:
            update.scene.remove(self)
        self.move(update.time_delta)


class Player(Ship):
    position = Vector(0, 9)
    heading = Vector(0, 0)
    speed = 5
    guns = 0
    engines = 0

    def on_update(self, update: event.Update, signal):
        controller: Controller = next(update.scene.get(tag="controller"))
        self.heading = Vector(controller.get("horizontal"), controller.get("vertical")).normalize()
        self.move(update.time_delta)

    def on_shoot(self, shoot_event: Shoot, __):
        shoot_event.scene.add(Bullet(position=self.top.center, image="bullet/t0d0.png"), tags=["bullet", "friendly"])

    @property
    def image(self):
        return f"ship/g{self.guns}e{self.engines}.png"


class Level(SpriteRoot):
    image = flag.DoNotRender
    counter = 0
    spawn_at = .5
    min_increment = 1.5
    max_change = .25
    last_increment = 2.5

    def on_update(self, update: event.Update, signal):
        self.counter += update.time_delta
        if self.counter >= self.spawn_at:
            formation = choice(formations)
            self.spawn_formation(formation, update.scene)
            increment = self.last_increment + (-self.max_change + (rand() * 2* self.max_change))
            if increment <= self.min_increment:
                increment = self.min_increment
            self.spawn_at += increment
            self.last_increment = increment

    def spawn_formation(self, formation, scene):
        span, *modifiers = formation
        min_x = -span / 2
        spawn_x = min_x + (rand() * (10 - span))
        origin = Vector(spawn_x, -10)
        for modifier in modifiers:
            scene.add(EnemyShip(position = origin + modifier), tags=["enemy", "ship"])


formations = [
    (5, Vector(0, 0), Vector(-2, -1), Vector(2, -1))
]