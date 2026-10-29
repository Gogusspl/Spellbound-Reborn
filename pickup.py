import pygame
from settings import *


class Pickup(pygame.sprite.Sprite):
    """Kulka XP (niebieska) albo moneta (mała żółta). Leci do gracza, gdy jest blisko."""

    def __init__(self, pos, kind, value):
        super().__init__()
        self.kind = kind    # "xp" albo "gold"
        self.value = value

        if kind == "xp":
            radius, color = XP_RADIUS, XP_COLOR
        else:
            radius, color = GOLD_RADIUS, GOLD_COLOR

        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect()

        self.pos = pygame.math.Vector2(pos)
        self.rect.center = self.pos

    def update(self, dt, player, attract_all=False):
        # Magnes: przyciąganie do gracza, gdy jest w zasięgu zbierania
        # (albo od razu z całej mapy, np. w przerwie między falami)
        to_player = player.pos - self.pos
        distance = to_player.length()
        if 0 < distance and (attract_all or distance < player.pickup_range):
            self.pos += to_player.normalize() * PICKUP_FLY_SPEED * dt
            self.rect.center = self.pos