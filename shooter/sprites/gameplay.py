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


# TODO: Add the player to the update event.

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


class PowerUps(Enum):
    GUN = "gun"
    SHIELD = "shield"
    ENGINE = "engine"


class MoveMixin(SpriteRoot):
    speed = 3
    heading = Vector(0, -1)

    def move(self, time_delta):
        self.position += self.heading * time_delta * self.speed


class DamageMixin(SpriteRoot):
    health = 100

    def damage(self, damage):
        self.health -= damage


class Ship(MoveMixin, DamageMixin):
    mass = 100


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
                target.damage(self.intensity)
        if self.kill:
            update.scene.remove(self)


class Alert(Bullet):
    target = "there is none"
    image = Image("shooter/resources/enemies/message.png")
    speed = 5
    size = 0.5


class Beacon(MoveMixin):
    heading = Vector(0, -1)
    life_span = values.enemy_beacon_life_span
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
    sensor_distance = 1
    player_spotted = False

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
                self.damage(player.mass)
                player.damage(self.mass)
            elif (player.position - self.position).length <= self.sensor_distance:
                self.player_spotted = True
                self.sensor_response(player, signal)

    def sensor_response(self, player, signal):
        pass


class PatrolShip(EnemyShip):
    health = values.enemy_patrol_health
    image = Image("shooter/resources/enemies/patrol.png")
    speed = values.enemy_patrol_speed
    sensor_distance = values.enemy_patrol_watch_distance
    base_points = values.enemy_patrol_point_value
    bonus_points = values.enemy_patrol_bonus_value
    signaled = False

    @property
    def points(self):
        # TODO: Consider this a mixin?

        if not self.signaled:
            return self.base_points + self.bonus_points
        else:
            return self.base_points

    def sensor_response(self, player, signal):
        if not self.signaled:
            signal(shooter_events.EnemyAlerted(self))
            self.signaled = True


class CargoShip(EnemyShip):
    health = values.enemy_cargo_health
    image = Image("shooter/resources/enemies/cargo.png")
    speed = values.enemy_cargo_speed
    sensor_distance = values.enemy_cargo_watch_distance
    upgrade_points = values.enemy_cargo_upgrade_value
    max_speed = values.enemy_cargo_max_speed

    def on_update(self, update: ppb_events.Update, signal):
        super().on_update(update, signal)
        if self.player_spotted and self.speed < self.max_speed:
            self.speed *= values.enemy_cargo_acceleration
            if self.speed > self.max_speed:
                self.speed = self.max_speed


class EscortFrigate(EnemyShip):
    health = values.enemy_escort_health
    image = Image("shooter/resources/enemies/escort.png")
    speed = values.enemy_escort_speed
    cooldown_counter = 0
    next_shot = 0
    shots = []
    shooting = False
    escorting = None
    points = values.enemy_escort_point_value

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
        else:
            self.heading = Vector(0, -1)
        super().on_update(update, signal)
        self.cooldown_counter += update.time_delta
        if self.cooldown_counter >= self.next_shot:
            if not self.shots:
                players = list(update.scene.get(kind=Player))
                if not players:
                    return
                player = players.pop()
                self.shots = [
                    player.position + Vector(0, 2),
                    player.position,
                    player.position + Vector(0, -2)
                ]
            shot_target = self.shots.pop()
            shot_vector = shot_target - self.position
            bullet = Bullet(
                position=self.position,
                heading=shot_vector.normalize(),
                target="player"
            )
            bullet.facing = -shot_vector
            update.scene.add(bullet)
            self.cooldown_counter = 0
            if self.shots:
                self.next_shot = values.enemy_escort_volley_pause
            else:
                self.next_shot = values.enemy_escort_volley_cooldown


class Zero(EnemyShip):
    accelerate = False
    acceleration = values.enemy_zero_acceleration
    sensor_distance = values.enemy_zero_watch_distance
    health = values.enemy_zero_health
    image = Image("shooter/resources/enemies/zero.png")
    max_speed = values.enemy_zero_max_speed
    points_value = values.enemy_zero_points
    bonus_value = values.enemy_zero_bonus
    speed = values.enemy_zero_speed

    @property
    def points(self):
        if not self.accelerate:
            return self.points_value
        else:
            return self.points_value + self.bonus_value

    def on_update(self, update: ppb_events.Update, signal):
        super().on_update(update, signal)
        if self.player_spotted and self.speed < self.max_speed:
            self.speed *= self.acceleration
            if self.speed > self.max_speed:
                self.speed = self.max_speed

    def sensor_response(self, player, signal):
        self.heading = ((player.position + (player.heading * player.speed * .25)) - self.position).normalize()
        self.facing = self.heading


class Ace(EnemyShip):
    image = Image("shooter/resources/enemies/superiority.png")
    health = values.enemy_ace_health
    initial_speed = values.enemy_ace_speed_cruise
    sensor_distance = values.enemy_ace_sensor_range
    attack_mode = False
    target_attack_range = values.enemy_ace_optimal_range
    bullet_cool_down = values.enemy_ace_bullet_cool_down
    tri_missle_cool_down = values.enemy_ace_tri_missle_cool_down
    tri_missle_counter = 0
    tri_missle_count = 2
    max_thrust = values.enemy_ace_max_thrust

    def on_update(self, update: ppb_events.Update, signal):
        super().on_update(update, signal)
        if self.player_spotted:
            self.maneuver(update, signal)

    def maneuver(self, update, signal):
        if self.health > values.enemy_ace_health / 2:
            target_vector = Vector(0, 0)
            # Slow and aim to be the target distance.
            for player in update.scene.get(kind=Player):

                # Making moves
                # TODO: Add some variance to this to keep Aces from locking in position.
                from_player = self.position - player.position
                target_vector += from_player.scale(self.max_thrust)
                towards_player = player.position - self.position
                strength_of_towards = (towards_player.length / self.target_attack_range) * self.max_thrust
                target_vector += (player.position - self.position).scale(strength_of_towards)
                avoid_left = max(2 - self.position.x, 0)
                target_vector += Vector(avoid_left, 0).scale(avoid_left ** 2)
                avoid_right = max(self.position.x - 8, 0)
                target_vector += Vector(avoid_right, 0).scale(avoid_right ** 2)
                self.heading = target_vector.normalize()
                self.speed = target_vector.length

                # Attack time
                spawn_position = self.position + towards_player.truncate(0.5)
                if self.bullet_cool_down <= 0:
                    update.scene.add(
                        Bullet(
                            position=spawn_position,
                            heading=towards_player.normalize(),
                            target="player"
                        )
                    )
                    self.bullet_cool_down = values.enemy_ace_bullet_cool_down
                else:
                    self.bullet_cool_down -= update.time_delta
                if self.tri_missle_cool_down <= 0:
                    if self.tri_missle_count:
                        update.scene.add(
                            Zero(
                                position=spawn_position,
                                heading=towards_player.normalize(),
                                size=.5
                            )
                        )
                        self.tri_missle_count -= 1
                        self.tri_missle_cool_down = 0.2
                    else:
                        update.scene.add(
                            Zero(
                                position=spawn_position,
                                heading=towards_player.normalize(),
                                size=.5
                            )
                        )
                        self.tri_missle_count = 2
                        self.tri_missle_cool_down = values.enemy_ace_tri_missle_cool_down
                else:
                    self.tri_missle_cool_down -= update.time_delta
        else:
            self.heading = Vector(0, -1)
            self.speed = self.max_thrust


class Player(Ship):
    position = Vector(0, -9)
    heading = Vector(0, 0)
    guns = 0
    engines = 0
    health = values.player_health
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
            scene.add(Bullet(position=Vector(initial_x + (-0.5 * self.guns) + (0.5 * offset), initial_y), tags=tags))

    def on_power_up(self, power_up_event: shooter_events.PowerUp, signal):
        if (power_up_event.kind == PowerUps.GUN
                and self.guns < values.player_gun_max):
            self.guns += 1
        if (power_up_event.kind == PowerUps.ENGINE
                and self.engines < values.player_engine_max):
            self.engines += 1
        elif power_up_event.kind == PowerUps.SHIELD:
            if not list(power_up_event.scene.get(tag="shield")):
                power_up_event.scene.add(Shield(parent=self, position=self.position), tags=["player"])

    @property
    def speed(self):
        return values.player_base_speed + (self.engines * values.player_engine_bonus)

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


class Shield(DamageMixin):
    image = Image("shooter/resources/shield.png")
    parent: Ship = None
    size = 2
    impact = 1000
    health = 15

    def on_update(self, event: ppb_events.Update, signal):
        self.position = self.parent.position
        if self.health <= 0:
            event.scene.remove(self)
            return
        enemy: EnemyShip
        for enemy in event.scene.get(tag="enemy"):
            if self.collides_with(enemy):
                enemy.damage(self.impact)
                event.scene.remove(self)
                signal(ppb_events.PlaySound(sounds["shield_down"]))
                break
