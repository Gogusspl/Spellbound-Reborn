import pygame
from settings import *


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Na razie zwykły kwadrat - później podmienisz na grafikę
        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()

        self.pos = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)
        self.rect.center = self.pos

        # Statystyki (karty i sklep będą modyfikować właśnie te wartości)
        self.speed = PLAYER_SPEED
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.damage = PLAYER_DAMAGE
        self.attack_speed = PLAYER_ATTACK_SPEED
        self.attack_range = PLAYER_ATTACK_RANGE
        self.pickup_range = PLAYER_PICKUP_RANGE

        # Postęp w rundzie
        self.xp = 0
        self.level = 1
        self.xp_to_next = XP_TO_FIRST_LEVEL
        self.gold = 0

        # Liczniki czasu
        self.hit_timer = 0      # nietykalność po trafieniu
        self.attack_timer = 0   # czas do kolejnego strzału

    def update(self, dt):
        keys = pygame.key.get_pressed()
        direction = pygame.math.Vector2(
            keys[pygame.K_d] - keys[pygame.K_a],
            keys[pygame.K_s] - keys[pygame.K_w],
        )
        # normalize, żeby ruch po skosie nie był szybszy
        if direction.length() > 0:
            direction = direction.normalize()

        self.pos += direction * self.speed * dt

        # Nie wychodź poza ekran
        half = PLAYER_SIZE / 2
        self.pos.x = max(half, min(WIDTH - half, self.pos.x))
        self.pos.y = max(half, min(HEIGHT - half, self.pos.y))
        self.rect.center = self.pos

        if self.hit_timer > 0:
            self.hit_timer -= dt
        if self.attack_timer > 0:
            self.attack_timer -= dt

    # ---------- Atak ----------
    def can_attack(self):
        return self.attack_timer <= 0

    def reset_attack_timer(self):
        self.attack_timer = 1 / self.attack_speed

    def find_target(self, enemies):
        """Zwraca najbliższego wroga w zasięgu (albo None)."""
        closest = None
        best_distance = self.attack_range
        for enemy in enemies:
            distance = self.pos.distance_to(enemy.pos)
            if distance < best_distance:
                best_distance = distance
                closest = enemy
        return closest

    # ---------- Obrażenia ----------
    def take_damage(self, amount):
        if self.hit_timer <= 0:
            self.hp -= amount
            self.hit_timer = PLAYER_HIT_COOLDOWN

    def is_dead(self):
        return self.hp <= 0

    # ---------- XP i złoto ----------
    def add_xp(self, amount):
        """Dodaje XP. Zwraca liczbę zdobytych poziomów (zwykle 0 albo 1)."""
        self.xp += amount
        levels_gained = 0
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * XP_LEVEL_GROWTH)
            levels_gained += 1
        return levels_gained

    def add_gold(self, amount):
        self.gold += amount

    def draw(self, screen):
        # Miganie podczas nietykalności
        if self.hit_timer > 0 and int(self.hit_timer * 20) % 2 == 0:
            return
        screen.blit(self.image, self.rect)