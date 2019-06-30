from enum import Enum

from ppb import Vector
from ppb import events as event
from ppb.features.animation import Animation

from shooter import values
from shooter.sprites import SpriteRoot
from shooter.events import PlayerDied
from shooter.events import PowerUp as PowerUpEvent
from shooter.events import Shoot


__all__ = [
    "Bullet",
    "Player",
    "EnemyShip",
    "PowerUp"
]


class DamageTypes(Enum):
    COLLISION = "collision"


class PowerUps(Enum):
    GUN = "gun"


class MoveMixin(SpriteRoot):
    speed = 3
    heading = Vector(0, -1)

    def move(self, time_delta):
        self.position += self.heading * time_delta * self.speed


class Ship(MoveMixin):
    health = 100
    armor = 0
    mass = 100

    def damage(self, damage, kind=DamageTypes.COLLISION):
        if kind == DamageTypes.COLLISION:
            self.health -= damage - self.armor


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
        for player in update.scene.get(kind=Player):
            if self.collides_with(player):
                self.damage(player.mass, kind=DamageTypes.COLLISION)
                player.damage(self.mass, kind=DamageTypes.COLLISION)


class Player(Ship):
    position = Vector(0, -9)
    heading = Vector(0, 0)
    speed = 5
    guns = 0
    engines = 0

    def on_update(self, update: event.Update, signal):
        if self.health <= 0:
            update.scene.remove(self)
            signal(PlayerDied())
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
