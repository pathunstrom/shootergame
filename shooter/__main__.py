import ppb
from ppb import keycodes

from shooter import systems
from shooter.events import Shoot
from shooter.scene import Splash
from shooter.values import resolution

inputs = [
    systems.Axis("vertical", keycodes.Down, keycodes.Up),
    systems.Axis("horizontal", keycodes.Left, keycodes.Right),
    systems.Impulse("fire", keycodes.Space, Shoot)
]

with ppb.GameEngine(Splash, systems=[systems.ControllerSystem, systems.LifeCounter, systems.EnemyLoader],
                    resolution=resolution, inputs=inputs) as ge:
    ge.run()
