from random import choice
from random import random as rand
from typing import Iterable
from typing import NamedTuple
from typing import Union

from ppb import GameEngine
from ppb import Vector
from ppb import buttons
from ppb import events
from ppb import keycodes as key
from ppb.systems import System

from shooter import values
from shooter.sprites import gameplay as game_sprites


default_formations = (
    (5, Vector(0, 0), Vector(-2, 1), Vector(2, 1)),
)


PhysicalInputs = Union[buttons.MouseButton, key.KeyCode]


class Axis(NamedTuple):
    name: str
    default_negative: key.KeyCode
    default_positive: key.KeyCode


class Switch(NamedTuple):
    name: str
    default: key.KeyCode


class Impulse(NamedTuple):
    name: str
    default: key.KeyCode
    event: type


SoftwareInputs = Union[Axis, Switch, Impulse]


class ControllerSystem(System):
    """
    A controller subsystem for translating inputs into events or single
    values.

    Add to `ControllerSystem` to `GameEngine`'s systems parameter to use.

    `GameEngine` will require an `inputs` parameter which includes
    configuration for your control scheme. See `Axis`, `Switch`, and
    `Impulse` for more information.

    An option kwarg to add to `GameEngine` is `key_config` which can
    override your default controls.

    To access controls:

    In your on_update handlers, look for a controls dict, using the names
    defined in your config objects. Impulses do not have associated values,
    they emit the event you declared.
    """

    def __init__(self, *, engine: GameEngine,
                 inputs: Iterable[SoftwareInputs],
                 key_config: dict = None, **kwargs):
        """
        Initialize the controller subsystem.

        It is advised that you do not initialize this subsystem outside of
        the engine.

        :param engine: The game engine this will be used in. Required.
        :param inputs: An iterable of Axis, Switch, or Impulse objects.
        :param key_config: A dictionary of string names and key or button
        values.
        :param kwargs: Additional kwargs, required in ppb Systems.
        """
        super().__init__(inputs=inputs,
                         key_config=key_config,
                         **kwargs
                         )
        self.__values = {}
        self.__inputs = {}
        self.__key_config = key_config or {}
        for i in inputs:
            self.add(i)
        engine.register(events.Update, self.extend_update)

    def add(self, _input: SoftwareInputs):
        """
        Add an input to the controller.

        :param _input: And Axis, Switch, or Impulse.
        """
        if isinstance(_input, Impulse):
            self.add_impulse(_input)
        elif isinstance(_input, Axis):
            self.add_axis(_input)
        else:
            self.add_switch(_input)

    def add_impulse(self, impulse: Impulse):
        input_key = self.__key_config.get(impulse.name, impulse.default)
        self.__inputs[input_key] = None, impulse.event

    def add_axis(self, axis: Axis):
        self.__values[axis.name] = 0
        neg_key = self.__key_config.get(f"{axis.name}_negative",
                                        axis.default_negative)
        pos_key = self.__key_config.get(f"{axis.name}_positive",
                                        axis.default_positive)
        self.__inputs[neg_key] = axis.name, -1
        self.__inputs[pos_key] = axis.name, 1

    def add_switch(self, switch: Switch):
        self.__values[switch.name] = 0
        key_value = self.__key_config.get(switch.name, switch.default)
        self.__inputs[key_value] = switch.name, 1

    def extend_update(self, update_event: events.Update):
        update_event.controls = self.__values.copy()

    def handle_input_activated(self, input_value: PhysicalInputs,
                               signal_function, position=None):
        name: str
        value: Union[int, type]
        name, value = self.__inputs.get(input_value, (None, None))
        if name is None and value is not None:
            if isinstance(input_value, buttons.MouseButton):
                signal_function(value(position))
            else:
                signal_function(value())
        elif name is not None:
            self.__values[name] += value

    def handle_input_deactivated(self, input_value: PhysicalInputs):
        name: str
        value: Union[int, type]
        name, value = self.__inputs.get(input_value, (None, None))
        if name is not None:
            self.__values[name] -= value

    def on_key_pressed(self, key_event: events.KeyPressed, signal):
        self.handle_input_activated(key_event.key, signal)

    def on_button_pressed(self, button_event: events.ButtonPressed, signal):
        self.handle_input_activated(button_event.button,
                                    signal,
                                    button_event.position)

    def on_key_released(self, key_event: events.KeyPressed, signal):
        self.handle_input_deactivated(key_event.key)

    def on_button_released(self,
                           button_event: events.ButtonReleased, signal):
        self.handle_input_deactivated(button_event.button)


class NoStrategy:

    def __init__(self, formations):
        self.formations = formations

    def advance(self, time_delta, scene):
        pass

    def spawn_formation(self, scene):
        pass

    def calculate_next_spawn(self):
        pass


class EndlessStrategy(NoStrategy):
    next_spawn_time = 1.5
    counter = 0

    def advance(self, time_delta, scene):
        self.counter += time_delta
        while self.counter >= self.next_spawn_time:
            self.spawn_formation(scene)
            self.calculate_next_spawn()

    def spawn_formation(self, scene):
        formation = choice(self.formations)
        span, *modifiers = formation
        min_x = -span / 2
        spawn_x = min_x + (rand() * (10 - span))
        origin = Vector(spawn_x, 10)
        for modifier in modifiers:
            scene.add(game_sprites.EnemyShip(position=origin + modifier), tags=["enemy", "ship"])

    def calculate_next_spawn(self):
        self.next_spawn_time += 5


class EnemyLoader(System):
    """
    Spawns enemies based on either an input file or an algorithmic
    "endless" mode.
    """
    strategy = NoStrategy(())

    def __init__(self, *, formations=default_formations, **kwargs):
        super().__init__(formations=formations, **kwargs)
        self.formations = list(formations)

    def on_scene_started(self, started: events.SceneStarted, signal):
        strategy = getattr(started.scene, "spawn_strategy", None)
        if strategy == "endless":
            self.strategy = EndlessStrategy(self.formations)
        else:
            self.strategy = NoStrategy(self.formations)

    def on_idle(self, idle: events.Idle, signal):
        self.strategy.advance(idle.time_delta, idle.scene)


class LifeCounter(System):
    primed = False
    lives = values.player_starting_lives

    def on_idle(self, idle: events.Idle, signal):
        if self.primed and self.lives:
            idle.scene.add(game_sprites.Player())
            self.primed = False

    def on_player_died(self, died, signal):
        self.lives -= 1
        self.primed = True
