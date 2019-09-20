from enum import Enum

from ppb import Image
from ppb import Sound
from ppb import Vector
from ppb import events as ppb_events
from ppb.features.animation import Animation

from shooter import values
from shooter import events as shooter_events
from shooter.sprites import SpriteRoot
from shooter.sprites.root import RunOnceAnimation


__all__ = [
    "Bullet",
    "Player",
    "EnemyShip",
    "PowerUp"
]


class DamageTypes(Enum):
    COLLISION = "collision"
    SHIELD = "shield"


class PowerUps(Enum):
    GUN = "gun"
    SHIELD = "shield"
    ENGINE = "engine"


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
        elif kind == DamageTypes.SHIELD:  # Shields do full damage.
            self.health -= damage


class Bullet(MoveMixin):
    size = 0.25
    speed = 10
    heading = Vector(0, 1)
    target = "enemy"
    intensity = 1
    image = Image("shooter/resources/bullet.png")

    def on_update(self, update: ppb_events.Update, signal):
        if self.position.y > 10 or self.position.y < -10:
            update.scene.remove(self)
            return
        self.move(update.time_delta)
        for target in update.scene.get(tag=self.target):
            if self.collides_with(target):
                update.scene.remove(self)
                target.damage(self.intensity)


class EnemyShip(Ship):
    health = 1
    image = Image("shooter/resources/enemy/t0.png")

    def on_update(self, update: ppb_events.Update, signal):
        if self.health <= 0:
            update.scene.remove(self)
            signal(shooter_events.EnemyKilled(self))
        self.move(update.time_delta)
        for player in update.scene.get(kind=Player):
            if self.collides_with(player):
                self.damage(player.mass, kind=DamageTypes.COLLISION)
                player.damage(self.mass, kind=DamageTypes.COLLISION)


class Player(Ship):
    position = Vector(0, -9)
    heading = Vector(0, 0)
    guns = 0
    engines = 0
    images = [
        [
            Image(f"shooter/resources/ship/g{g}e{e}.png")
            for e
            in range(4)
        ]
        for g
        in range(4)
    ]
    sounds = {
        "laser": Sound("shooter/resources/sound/laser.wav"),
        "dead": Sound("shooter/resources/sound/life-lost.wav")
    }

    def on_update(self, update: ppb_events.Update, signal):
        if self.health <= 0:
            update.scene.remove(self)
            update.scene.add(RunOnceAnimation(
                position=self.position,
                life_span=0.25,
                image=Animation("shooter/resources/explosions/player/sprite_{1..7}.png", 24),
                end_event=shooter_events.PlayerDied(),
                size=2
            ))
            signal(ppb_events.PlaySound(self.sounds["dead"]))

        controller = update.controls
        self.heading = Vector(controller.get("horizontal"), controller.get("vertical"))
        if self.heading:
            self.heading = self.heading.normalize()
        self.move(update.time_delta)

    def on_shoot(self, shoot_event: shooter_events.Shoot, signal):
        scene = shoot_event.scene
        tags = ["bullet", "friendly"]
        signal(ppb_events.PlaySound(self.sounds["laser"]))
        initial_x, initial_y = self.top.center
        for offset in range(2 * self.guns + 1):
            scene.add(Bullet(position=Vector(initial_x + (-0.5 * self.guns) + (0.5 * offset), initial_y)))

    def on_power_up(self, power_up_event: shooter_events.PowerUp, signal):
        if (power_up_event.kind == PowerUps.GUN
                and self.guns < values.player_gun_max):
            self.guns += 1
        if (power_up_event.kind == PowerUps.ENGINE
                and self.engines < values.player_engine_max):
            self.engines += 1
        elif power_up_event.kind == PowerUps.SHIELD:
            if not list(power_up_event.scene.get(tag="shield")):
                power_up_event.scene.add(Shield(parent=self, position=self.position))

    @property
    def speed(self):
        return 3 + (self.engines * 1.5)

    @property
    def image(self):
        return self.images[self.guns][self.engines]


class PowerUp(MoveMixin):
    images = {
        PowerUps.GUN: Animation("shooter/resources/powerup/gun/{0..7}.png", 6),
        PowerUps.SHIELD: Animation("shooter/resources/powerup/shield/sprite_{0..7}.png", 6),
        PowerUps.ENGINE: Animation("shooter/resources/powerup/engine/sprite_{0..7}.png", 6)
    }
    speed = 1
    kind = PowerUps.GUN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image = self.images[self.kind]

    def on_update(self, update_event: ppb_events.Update, signal):
        self.move(update_event.time_delta)
        for p in update_event.scene.get(kind=Player):
            if (p.position - self.position).length * 2 < p.size + self.size:
                signal(shooter_events.PowerUp(self.kind))
                update_event.scene.remove(self)


class Shield(SpriteRoot):
    image = Image("shooter/resources/shield.png")
    parent: Ship = None
    size = 2
    impact = 1000

    def on_update(self, event: ppb_events.Update, signal):
        self.position = self.parent.position
        enemy: EnemyShip
        for enemy in event.scene.get(tag="enemy"):
            if self.collides_with(enemy):
                enemy.damage(self.impact, DamageTypes.SHIELD)

                event.scene.remove(self)
                break
