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


sounds = {
    "power_up": Sound("shooter/resources/sound/pickup.wav"),
    "player_laser": Sound("shooter/resources/sound/laser.wav"),
    "enemy_laser": Sound("shooter/resources/sound/laser2.wav"),
    "hit": Sound("shooter/resources/sound/hit.wav"),
    "dead": Sound("shooter/resources/sound/life-lost.wav"),
    "shield_down": Sound("shooter/resources/sound/shield_down.wav")
}


class DamageTypes(Enum):
    COLLISION = "collision"
    BULLET = "bullet"
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
        else:
            self.health -= damage - self.armor * 2


class Bullet(MoveMixin):
    size = 0.25
    speed = 10
    heading = Vector(0, 1)
    target = "enemy"
    intensity = 5
    image = Image("shooter/resources/bullet.png")
    kill = False

    def on_update(self, update: ppb_events.Update, signal):
        if self.position.y > 10 or self.position.y < -10:
            update.scene.remove(self)
            return
        self.move(update.time_delta)
        for target in update.scene.get(tag=self.target):
            if self.collides_with(target):
                self.kill = True
                target.damage(self.intensity, kind=DamageTypes.BULLET)
        if self.kill:
            update.scene.remove(self)


class Alert(Bullet):
    target = "there is none"
    image = Image("shooter/resources/enemies/message.png")
    speed = 5
    size = 0.5


class Beacon(MoveMixin):
    heading = Vector(0, -1)
    life_span = 2
    image = Image("shooter/resources/enemies/beacon.png")
    size = 0.5

    def on_update(self, update: ppb_events.Update, signal):
        self.life_span -= update.time_delta
        if self.life_span <= 0:
            update.scene.remove(self)
        for enemy in update.scene.get(kind=EnemyShip):
            if (self.position - enemy.position).length < 1:
                signal(shooter_events.EnemyAlerted(self))
                update.scene.remove(self)
                break


class EnemyShip(Ship):
    health = 1
    upgrade_points = 1
    points = 1

    def on_update(self, update: ppb_events.Update, signal):
        if self.health <= 0:
            update.scene.remove(self)
            signal(shooter_events.EnemyKilled(self))
        if self.position.y <= -11:
            update.scene.remove(self)
            signal(shooter_events.EnemyEscaped(self))
        self.move(update.time_delta)
        for player in update.scene.get(kind=Player):
            if self.collides_with(player):
                self.damage(player.mass, kind=DamageTypes.COLLISION)
                player.damage(self.mass, kind=DamageTypes.COLLISION)


class PatrolShip(EnemyShip):
    health = 15
    image = Image("shooter/resources/enemies/patrol.png")
    speed = 5
    critical_distance = 4
    points = 20
    signaled = False

    def on_update(self, event: ppb_events.Update, signal):
        p = list(event.scene.get(kind=Player))
        if p:
            player = p.pop()
            if (player.position - self.position).length < self.critical_distance:
                if not self.signaled:
                    signal(shooter_events.EnemyAlerted(self))
                    self.signaled = True
                    self.points = 10
        super().on_update(event, signal)


class CargoShip(EnemyShip):
    health = 25
    image = Image("shooter/resources/enemies/cargo.png")
    speed = 2
    critical_distance = 5
    upgrade_points = 5
    accelerate = False
    max_speed = 5

    def on_update(self, update: ppb_events.Update, signal):
        p = list(update.scene.get(kind=Player))
        if p:
            player = p.pop()
            if (player.position - self.position).length < self.critical_distance:
                self.accelerate = True
        if self.accelerate and self.speed < self.max_speed:
            self.speed *= 1.02
            if self.speed > self.max_speed:
                self.speed = self.max_speed
        super().on_update(update, signal)


class EscortFrigate(EnemyShip):
    health = 10
    image = Image("shooter/resources/enemies/escort.png")
    speed = 4
    cooldown_counter = 0
    next_shot = 0
    shots = []
    shooting = False
    escorting = None

    def on_update(self, update: ppb_events.Update, signal):
        if self.escorting is not None or self.escorting not in update.scene:
            cargo_ships = list(update.scene.get(kind=CargoShip))
            if cargo_ships:
                self.escorting = cargo_ships[0]  # We can modify this later. Might be better handled by a subsystem.
            else:
                self.escorting = None
        if self.escorting is not None:
            target = (self.position - self.escorting.position).scale(3)
            heading = Vector(0, -1) + (target - self.position)
            self.heading = heading.normalize()
        super().on_update(update, signal)
        self.cooldown_counter += update.time_delta
        if self.cooldown_counter >= self.next_shot:
            if not self.shots:
                self.shots = [5, 0, -5]  # Modifiers to the y component of the player position.
            players = list(update.scene.get(kind=Player))
            if not players:
                return
            player = players.pop()
            shot_modifier = self.shots.pop()
            shot_vector = player.position - self.position
            shot_vector = Vector(shot_vector.x, shot_vector.y + shot_modifier)
            bullet = Bullet(
                position=self.position,
                heading=shot_vector.normalize(),
                target="player"
            )
            bullet.facing = -shot_vector
            update.scene.add(bullet)
            self.cooldown_counter = 0
            if self.shots:
                self.next_shot = 0.25
            else:
                self.next_shot = 1.25


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
            signal(ppb_events.PlaySound(sounds["dead"]))

        controller = update.controls
        self.heading = Vector(controller.get("horizontal"), controller.get("vertical"))
        if self.heading:
            self.heading = self.heading.normalize()
        self.move(update.time_delta)

    def on_shoot(self, shoot_event: shooter_events.Shoot, signal):
        scene = shoot_event.scene
        tags = ["bullet", "friendly"]
        signal(ppb_events.PlaySound(sounds["player_laser"]))
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
                signal(ppb_events.PlaySound(sounds["power_up"]))
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
                signal(ppb_events.PlaySound(sounds["shield_down"]))
                break
