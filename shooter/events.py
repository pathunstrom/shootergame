from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from ppb import BaseSprite


class Scene(ABC):

    @abstractmethod
    def add(self, game_object: BaseSprite, tags: list) -> None: ...


@dataclass
class Shoot:
    scene: Scene = None
