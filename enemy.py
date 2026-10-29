import random
import pygame
from settings import *
from bullet import Bullet


class Enemy(pygame.sprite.Sprite):
    def __init__(self, kind="basic"):
        super().__init__()
        data = ENEMY_TYPES[kind]
        self.kind = kind
        self.is_boss = (kind == "boss")

        # Na razie zwykłe kółko - później podmienisz na grafikę
        self.radius = data["radius"]
        size = self.radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, data["color"], (self.radius, self.radius), self.radius)
        if "outline" in data:
            pygame.draw.circle(self.image, data["outline"], (self.radius, self.radius), self.radius, 4)
        self.rect = self.image.get_rect()

        self.pos = self._spawn_position()
        self.rect.center = self.pos

        # Statystyki
        self.speed = data["speed"]
        self.damage = data["damage"]
        self.max_hp = data["hp"]
        self.hp = self.max_hp

        # Co wypada po śmierci
        self.xp_value = data["xp"]
        self.gold_value = data["gold"]
        self.gold_chance = data["gold_chance"]

        # Strzelanie (tylko boss)
        self.shoot_interval = data.get("shoot_interval", 0)
        self.shoot_timer = self.shoot_interval
        self.bullet_damage = data.get("bullet_damage", 0)
        self.ring_bullets = data.get("ring_bullets", 0)
        self.ring_offset = 0

    def _spawn_position(self):
        """Boss wchodzi z góry na środku, reszta pojawia się na losowej krawędzi."""
        r = self.radius
        if self.is_boss:
            return pygame.math.Vector2(WIDTH // 2, -r)
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            return pygame.math.Vector2(random.randint(0, WIDTH), -r)
        if side == "bottom":
            return pygame.math.Vector2(random.randint(0, WIDTH), HEIGHT + r)
        if side == "left":
            return pygame.math.Vector2(-r, random.randint(0, HEIGHT))
        return pygame.math.Vector2(WIDTH + r, random.randint(0, HEIGHT))

    def update(self, dt, target_pos):
        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        self.pos += direction * self.speed * dt
        self.rect.center = self.pos

        if self.shoot_interval:
            self.shoot_timer -= dt

    def shoot(self, target_pos):
        """Zwraca listę pocisków do wystrzelenia (pustą, jeśli wróg nie strzela albo ma cooldown)."""
        if not self.shoot_interval or self.shoot_timer > 0:
            return []
        self.shoot_timer = self.shoot_interval

        shots = []
        # Pierścień pocisków we wszystkie strony (za każdym razem lekko obrócony)
        self.ring_offset += 17
        for i in range(self.ring_bullets):
            angle = self.ring_offset + i * 360 / self.ring_bullets
            direction = pygame.math.Vector2(1, 0).rotate(angle)
            shots.append(Bullet(self.pos, self.pos + direction, self.bullet_damage,
                                ENEMY_BULLET_COLOR, ENEMY_BULLET_SPEED, ENEMY_BULLET_RADIUS))
        # Do tego jeden szybszy pocisk wycelowany w gracza
        shots.append(Bullet(self.pos, target_pos, self.bullet_damage,
                            ENEMY_BULLET_COLOR, ENEMY_BULLET_SPEED * 1.4, ENEMY_BULLET_RADIUS + 2))
        return shots

    def take_damage(self, amount):
        """Zadaje obrażenia. Zwraca True, jeśli wróg zginął."""
        self.hp -= amount
        return self.hp <= 0

    def draw_health_bar(self, screen):
        # Boss ma własny duży pasek na górze ekranu
        if self.is_boss:
            return
        # Pasek HP pokazuje się dopiero, gdy wróg jest ranny
        if self.hp >= self.max_hp:
            return
        width = self.radius * 2
        x = self.rect.left
        y = self.rect.top - 8
        ratio = max(self.hp, 0) / self.max_hp
        pygame.draw.rect(screen, HP_BAR_BG, (x, y, width, 4))
        pygame.draw.rect(screen, HP_BAR_FG, (x, y, width * ratio, 4))