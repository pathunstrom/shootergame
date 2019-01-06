import ppb

from shooter.scene import Splash
from shooter.values import resolution

with ppb.GameEngine(Splash, resolution=resolution) as ge:
    ge.run()
