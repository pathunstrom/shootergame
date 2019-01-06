from ppb import BaseSprite

from pathlib import Path


class SpriteRoot(BaseSprite):
    resource_path = Path(r"C:\Users\pathu\src\pathunstrom\shooter\shooter\resources")

    def collides_with(self, other: 'SpriteRoot'):
        halfs = (self.size + other.size) / 2
        return abs(self.center.x - other.center.x) < halfs and abs(self.center.y - other.center.y) < halfs
