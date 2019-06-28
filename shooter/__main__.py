import ppb
from ppb import buttons
from ppb import keycodes

from shooter import systems
from shooter.events import Shoot
from shooter.scene import Splash
from shooter.values import resolution

inputs = [
    systems.Axis("vertical", keycodes.S, keycodes.W),
    systems.Axis("horizontal", keycodes.A, keycodes.D),
    systems.Impulse("fire", buttons.Primary, Shoot)
]

with ppb.GameEngine(Splash, systems=[systems.ControllerSystem],
                    resolution=resolution, inputs=inputs) as ge:
    ge.run()
