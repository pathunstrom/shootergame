from typing import NamedTuple
from typing import Union

from ppb import events as event
from ppb import keycodes as key
from ppb.flags import DoNotRender

from shooter.root import SpriteRoot


class Axis(NamedTuple):
    name: str
    default_negative: key.KeyCode
    default_positive: key.KeyCode


class Button(NamedTuple):
    name: str
    default: key.KeyCode


class Impulse(NamedTuple):
    name: str
    default: key.KeyCode
    event: type


class Controller(SpriteRoot):
    image = DoNotRender

    def __init__(self, inputs, key_config=None):
        super().__init__()
        self.__values = {}
        self.__inputs = {}
        self.__key_config = key_config or {}
        for i in inputs:
            self.add(i)

    def add_impulse(self, impulse: Impulse):
        input_key = self.__key_config.get(impulse.name, impulse.default)
        self.__inputs[input_key] = None, impulse.event

    def add_axis(self, axis: Axis):
        self.__values[axis.name] = 0
        neg_key = self.__key_config.get(axis.name + "_negative", axis.default_negative)
        pos_key = self.__key_config.get(axis.name + "_positive", axis.default_positive)
        self.__inputs[neg_key] = axis.name, -1
        self.__inputs[pos_key] = axis.name, 1

    def add_button(self, button: Button):
        self.__values[button.name] = 0
        self.__inputs[self.__key_config.get(button.name, button.default)] = button.name, 1

    def add(self, i: Union[Axis, Button, Impulse]) -> None:
        if isinstance(i, Impulse):
            self.add_impulse(i)
        elif isinstance(i, Axis):
            self.add_axis(i)
        else:
            self.add_button(i)

    def get(self, name):
        return self.__values[name]

    def on_key_pressed(self, key_event: event.KeyPressed, signal):
        name: str
        value: Union[int, type]
        name, value = self.__inputs.get(key_event.key, (None, None))
        if name is None and value is not None:
            signal(value())
        elif name is not None:
            self.__values[name] += value

    def on_key_released(self, key_event: event.KeyReleased, signal):
        name: str
        value: Union[int, type]
        name, value = self.__inputs.get(key_event.key, (None, None))
        if name is not None:
            self.__values[name] -= value
