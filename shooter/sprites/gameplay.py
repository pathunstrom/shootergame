from enum import Enum
from random import random as rand
from random import choice

from ppb import Vector
from ppb import events as event
from ppb import flags as flag
from ppb.features.animation import Animation

from shooter import values
from shooter.sprites import SpriteRoot
from shooter.events import PowerUp as PowerUpEvent
from shooter.events import Shoot


__all__ = [
    "Bullet",
    "Player",
    "EnemyShip",
    "Level",
    "PowerUp"
]


class PowerUps(Enum):
    GUN = "gun"


class MoveMixin(SpriteRoot):
    speed = 3
    heading = Vector(0, -1)

    def move(self, time_delta):
        self.position += self.heading * time_delta * self.speed


class Ship(MoveMixin):
    health = 100

    def damage(self, damage, type=None):
        if type is None:
            self.health -= damage


class Bullet(MoveMixin):
    size = 0.25
    speed = 10
    heading = Vector(0, 1)
    target = "enemy"
    intensity = 1
    image = "../resources/bullet.png"

    def on_update(self, update: event.Update, signal):
        self.move(update.time_delta)
        for target in update.scene.get(tag=self.target):
            if self.collides_with(target):
                update.scene.remove(self)
                target.damage(self.intensity)


class EnemyShip(Ship):
    health = 1
    image = "../resources/enemy/t0.png"

    def on_update(self, update: event.Update, signal):
        if self.health <= 0:
            update.scene.remove(self)
        self.move(update.time_delta)


class Player(Ship):
    position = Vector(0, -9)
    heading = Vector(0, 0)
    speed = 5
    guns = 0
    engines = 0

    def on_update(self, update: event.Update, signal):
        controller = update.controls
        self.heading = Vector(controller.get("horizontal"), controller.get("vertical"))
        if self.heading:
            self.heading = self.heading.normalize()
        self.move(update.time_delta)

    def on_shoot(self, shoot_event: Shoot, __):
        scene = shoot_event.scene
        tags = ["bullet", "friendly"]
        scene.add(Bullet(position=self.top.center), tags=tags)
        if self.guns > 0:
            scene.add(Bullet(position=self.top.left), tags=tags)
            scene.add(Bullet(position=self.top.right), tags=tags)

    def on_power_up(self, power_up_event: PowerUpEvent, signal):
        if (power_up_event.kind == PowerUps.GUN
                and self.guns < values.player_gun_max):
            self.guns += 1

    @property
    def image(self):
        return f"../resources/ship/g{self.guns}e{self.engines}.png"


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
        origin = Vector(spawn_x, 10)
        for modifier in modifiers:
            scene.add(EnemyShip(position = origin + modifier), tags=["enemy", "ship"])


class PowerUp(MoveMixin):
    image = Animation("../resources/powerup/gun/{0..7}.png", 6)
    speed = 1
    kind = PowerUps.GUN

    def on_update(self, update_event: event.Update, signal):
        self.move(update_event.time_delta)
        for p in update_event.scene.get(kind=Player):
            if (p.position - self.position).length * 2 < p.size + self.size:
                signal(PowerUpEvent(self.kind))
                update_event.scene.remove(self)


formations = [
    (5, Vector(0, 0), Vector(-2, 1), Vector(2, 1))
]