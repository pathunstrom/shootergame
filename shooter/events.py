from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from typing import Iterable


from ppb import BaseSprite


class Scene(ABC):

    @abstractmethod
    def add(self, game_object: BaseSprite, tags: list = ()) -> None: ...

    @abstractmethod
    def get(self, kind: type = None, tag: str = None) -> Iterable: ...

    @abstractmethod
    def remove(self, game_object: Any) -> None: ...


@dataclass
class EnemiesClear:
    scene: Scene = None


@dataclass
class EnemyAlerted:
    source: Any
    scene: Scene = None


@dataclass
class EnemyKilled:
    enemy: Any
    scene: Scene = None


@dataclass
class EnemyEscaped:
    enemy: Any
    scene: Scene = None


@dataclass
class GameOver:
    scene: Scene = None


@dataclass
class PlayerDied:
    scene: Scene = None


@dataclass
class PowerUp:
    kind: Any
    scene: Scene = None


@dataclass
class ScoreChange:
    score: int
    debug: str = "Score change"


@dataclass
class SetLives:
    scene: Scene = None


@dataclass
class Shoot:
    scene: Scene = None


@dataclass
class SpawnPlayer:
    scene: Scene = None
