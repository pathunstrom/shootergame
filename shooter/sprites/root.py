from ppb import BaseSprite

__all__ = ["SpriteRoot"]


class SpriteRoot(BaseSprite):

    def collides_with(self, other: 'SpriteRoot'):
        halfs = (self.size + other.size) / 2
        return abs(self.center.x - other.center.x) < halfs and abs(self.center.y - other.center.y) < halfs
