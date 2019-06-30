from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from ppb import BaseSprite


class Scene(ABC):

    @abstractmethod
    def add(self, game_object: BaseSprite, tags: list) -> None: ...


@dataclass
class PlayerDied:
    scene: Scene = None


@dataclass
class PowerUp:
    kind: Any
    scene: Scene = None


@dataclass
class Shoot:
    scene: Scene = None

