import pygame
from settings import *


class Pickup(pygame.sprite.Sprite):
    def __init__(self, pos, kind, value):
        super().__init__()
        self.kind = kind    # "xp" albo "gold"
        self.value = value

        if kind == "xp":
            self.image = load_sprite("xp.png", XP_SIZE)
        else:
            self.image = load_sprite("coin.png", GOLD_SIZE)
        self.rect = self.image.get_rect()

        self.pos = pygame.math.Vector2(pos)
        self.rect.center = self.pos

    def update(self, dt, player, attract_all=False):
        # Magnes
        to_player = player.pos - self.pos
        distance = to_player.length()
        if 0 < distance and (attract_all or distance < player.pickup_range):
            self.pos += to_player.normalize() * PICKUP_FLY_SPEED * dt
            self.rect.center = self.pos