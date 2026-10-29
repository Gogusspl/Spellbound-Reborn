import pygame
from settings import *


class Bullet(pygame.sprite.Sprite):
    """Pocisk lecący prosto. Używany przez gracza (domyślne wartości) i przez bossa."""

    def __init__(self, start_pos, target_pos, damage,
                 color=BULLET_COLOR, speed=BULLET_SPEED, radius=BULLET_RADIUS):
        super().__init__()
        size = radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect()

        self.pos = pygame.math.Vector2(start_pos)
        self.rect.center = self.pos

        # Kierunek lotu ustalany raz - pocisk leci prosto w stronę celu
        direction = pygame.math.Vector2(target_pos) - self.pos
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.direction = direction.normalize()

        self.speed = speed
        self.damage = damage

    def update(self, dt):
        self.pos += self.direction * self.speed * dt
        self.rect.center = self.pos

        # Usuń pocisk, gdy wyleci daleko poza ekran
        if not pygame.Rect(0, 0, WIDTH, HEIGHT).inflate(300, 300).collidepoint(self.pos):
            self.kill()