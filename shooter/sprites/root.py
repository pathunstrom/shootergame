from ppb import BaseSprite

__all__ = ["SpriteRoot"]


class SpriteRoot(BaseSprite):

    def collides_with(self, other: 'SpriteRoot'):
        halfs = (self.size + other.size) / 2
        return (abs(self.center.x - other.center.x) < halfs
                and abs(self.center.y - other.center.y) < halfs)


class RunOnceAnimation(BaseSprite):
    life_span = 0.5
    counter = 0
    end_event = None

    def on_update(self, event, signal):
        self.counter += event.time_delta
        if self.counter >= self.life_span:
            event.scene.remove(self)
            if self.end_event is not None:
                signal(self.end_event)
