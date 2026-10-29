import sys
import math
import random
import pygame
import save
from settings import *
from player import Player
from enemy import Enemy
from bullet import Bullet
from pickup import Pickup
from upgrades import (
    roll_cards, apply_upgrade, format_value,
    META_UPGRADES, meta_cost, meta_stat_value, buy_meta_upgrade, apply_meta_upgrades,
)
from waves import WaveManager


class Button:
    def __init__(self, text, center_y, font):
        self.text = text
        self.font = font
        self.rect = pygame.Rect(0, 0, 300, 60)
        self.rect.center = (WIDTH // 2, center_y)

    def draw(self, screen):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = BUTTON_HOVER if hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        label = self.font.render(self.text, True, WHITE)
        screen.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Spellbound Reborn")
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("arial", 72, bold=True)
        self.font_button = pygame.font.SysFont("arial", 32)
        self.font_small = pygame.font.SysFont("arial", 24)
        self.font_card_title = pygame.font.SysFont("arial", 30, bold=True)
        self.font_card_value = pygame.font.SysFont("arial", 40, bold=True)

        # Stan gry: "menu", "game", "paused", "level_up", "game_over", "victory",
        #           "settings", "upgrades"
        self.state = "menu"
        self.running = True

        # Trwały postęp (złoto + poziomy stałych ulepszeń), wczytany z save.json
        self.save_data = save.load_game()
        self.run_active = False   # czy trwa runda, której złoto nie zostało jeszcze zapisane

        self.buttons = [
            Button("Start", 300, self.font_button),
            Button("Ulepszenia", 380, self.font_button),
            Button("Ustawienia", 460, self.font_button),
        ]
        self.pause_buttons = [
            Button("Wznów", 330, self.font_button),
            Button("Wróć do menu", 410, self.font_button),
        ]

        # Dane rundy (ustawiane w start_run)
        self.player = None
        self.enemies = None
        self.bullets = None         # pociski gracza
        self.enemy_bullets = None   # pociski bossa
        self.pickups = None
        self.waves = None
        self.kills = 0

        # Wybór kart po awansie na wyższy poziom
        self.cards = []
        self.pending_levelups = 0   # ile awansów czeka na wybór karty
        card_w, card_h, gap = 300, 420, 40
        total_w = 3 * card_w + 2 * gap
        start_x = (WIDTH - total_w) // 2
        self.card_rects = [
            pygame.Rect(start_x + i * (card_w + gap), 190, card_w, card_h)
            for i in range(3)
        ]

        # Wiersze ekranu "Ulepszenia": (ulepszenie, prostokąt wiersza, prostokąt przycisku kupna)
        self.meta_rows = []
        row_w, row_h, row_gap = 820, 70, 8
        row_x = (WIDTH - row_w) // 2
        for i, upgrade in enumerate(META_UPGRADES):
            y = 190 + i * (row_h + row_gap)
            row = pygame.Rect(row_x, y, row_w, row_h)
            buy = pygame.Rect(row.right - 170, y + 10, 150, 50)
            self.meta_rows.append((upgrade, row, buy))

    # ---------- Rozpoczęcie rundy ----------
    def start_run(self):
        self.player = Player()
        apply_meta_upgrades(self.player, self.save_data["levels"])   # stałe ulepszenia ze sklepu
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.waves = WaveManager()
        self.kills = 0
        self.cards = []
        self.pending_levelups = 0
        self.run_active = True
        self.state = "game"

    def bank_run_gold(self):
        """Dolicza złoto zebrane w rundzie do zapisu (tylko raz na rundę)."""
        if self.run_active and self.player:
            self.save_data["gold"] += self.player.gold
            save.save_game(self.save_data)
            self.run_active = False

    def end_run(self, new_state):
        self.bank_run_gold()
        self.state = new_state

    # ---------- Pętla główna ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000  # czas klatki w sekundach
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

    # ---------- Zdarzenia ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.bank_run_gold()   # złoto z przerwanej rundy też się liczy
                self.running = False

            if self.state == "menu":
                if self.buttons[0].clicked(event):
                    self.start_run()
                elif self.buttons[1].clicked(event):
                    self.state = "upgrades"
                elif self.buttons[2].clicked(event):
                    self.state = "settings"

            elif self.state == "game":
                # ESC włącza pauzę
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "paused"

            elif self.state == "paused":
                self.handle_pause_event(event)

            elif self.state == "level_up":
                self.handle_level_up_event(event)

            elif self.state == "upgrades":
                self.handle_upgrades_event(event)

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Ustawienia, ekran śmierci i zwycięstwa: ESC wraca do menu
                self.state = "menu"

    def handle_pause_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "game"
        elif self.pause_buttons[0].clicked(event):
            self.state = "game"
        elif self.pause_buttons[1].clicked(event):
            self.end_run("menu")   # złoto zebrane do tej pory zostaje zapisane

    def handle_upgrades_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "menu"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for upgrade, row, buy in self.meta_rows:
                if buy.collidepoint(event.pos):
                    if buy_meta_upgrade(self.save_data, upgrade):
                        save.save_game(self.save_data)
                    break

    # ---------- Logika ----------
    def update(self, dt):
        if self.state != "game":
            return

        self.player.update(dt)

        # Fale: menedżer mówi, jakich wrogów wypuścić
        for kind in self.waves.update(dt, len(self.enemies)):
            self.enemies.add(Enemy(kind))
        if self.waves.state == "done":
            self.win()
            return

        self.enemies.update(dt, self.player.pos)
        for enemy in self.enemies:
            self.enemy_bullets.add(enemy.shoot(self.player.pos))
        self.enemy_bullets.update(dt)

        self.handle_shooting()
        self.bullets.update(dt)
        self.handle_bullet_hits()

        # W przerwie między falami wszystkie dropy lecą do gracza
        self.pickups.update(dt, self.player, self.waves.state == "intermission")
        self.handle_pickups()

        self.handle_player_damage()
        if self.player.is_dead():
            self.end_run("game_over")

    def win(self):
        # Zbierz złoto, które zostało na ziemi (np. po bossie)
        for item in self.pickups:
            if item.kind == "gold":
                self.player.add_gold(item.value)
        self.pickups.empty()
        self.end_run("victory")

    def handle_shooting(self):
        """Auto-atak: gdy minie cooldown, strzelaj w najbliższego wroga."""
        if not self.player.can_attack():
            return
        target = self.player.find_target(self.enemies)
        if target:
            self.bullets.add(Bullet(self.player.pos, target.pos, self.player.damage))
            self.player.reset_attack_timer()

    def handle_bullet_hits(self):
        """Pociski trafiają wrogów; martwy wróg zostawia XP i (czasem) złoto."""
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, False)
        for bullet, enemies_hit in hits.items():
            enemy = enemies_hit[0]
            if not enemy.alive():
                continue
            if enemy.take_damage(bullet.damage):
                self.spawn_drops(enemy)
                enemy.kill()
                self.kills += 1

    def spawn_drops(self, enemy):
        self.pickups.add(Pickup(enemy.pos, "xp", enemy.xp_value))
        if random.random() < enemy.gold_chance:
            offset = pygame.math.Vector2(random.randint(-12, 12), random.randint(-12, 12))
            self.pickups.add(Pickup(enemy.pos + offset, "gold", enemy.gold_value))

    def handle_player_damage(self):
        # Dotyk wroga
        for enemy in pygame.sprite.spritecollide(self.player, self.enemies, False):
            self.player.take_damage(enemy.damage)
        # Pociski bossa (pocisk znika po trafieniu)
        for bullet in pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
            self.player.take_damage(bullet.damage)

    def handle_pickups(self):
        collected = pygame.sprite.spritecollide(self.player, self.pickups, True)
        for item in collected:
            if item.kind == "xp":
                levels = self.player.add_xp(item.value)
                if levels:
                    self.pending_levelups += levels
                    if self.state == "game":
                        self.cards = roll_cards(self.player)
                        self.state = "level_up"
            else:
                self.player.add_gold(item.value)

    # ---------- Wybór karty ----------
    def handle_level_up_event(self, event):
        # Kliknięcie myszą w kartę
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.card_rects):
                if rect.collidepoint(event.pos):
                    self.choose_card(i)
                    return
        # Albo klawisze 1, 2, 3
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            self.choose_card(event.key - pygame.K_1)

    def choose_card(self, index):
        apply_upgrade(self.player, self.cards[index])
        self.pending_levelups -= 1
        if self.pending_levelups > 0:
            # Zdobyłeś kilka poziomów naraz - losujemy kolejne karty
            self.cards = roll_cards(self.player)
        else:
            self.state = "game"

    # ---------- Rysowanie ----------
    def draw(self):
        self.screen.fill(BG_COLOR)

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "game":
            self.draw_game()
        elif self.state == "paused":
            self.draw_game()
            self.draw_pause()
        elif self.state == "level_up":
            self.draw_game()
            self.draw_level_up()
        elif self.state == "game_over":
            self.draw_game()
            self.draw_end_screen("Nie żyjesz")
        elif self.state == "victory":
            self.draw_game()
            self.draw_end_screen("Zwycięstwo!")
        elif self.state == "settings":
            self.draw_placeholder("Ustawienia")
        elif self.state == "upgrades":
            self.draw_upgrades()

        pygame.display.flip()

    def draw_gold_counter(self, right, center_y, amount):
        """Rysuje licznik złota (moneta + liczba) wyrównany do prawej krawędzi `right`."""
        text = self.font_button.render(str(amount), True, WHITE)
        text_rect = text.get_rect(midright=(right, center_y))
        self.screen.blit(text, text_rect)
        pygame.draw.circle(self.screen, GOLD_COLOR, (text_rect.left - 18, center_y), 10)

    def draw_menu(self):
        title = self.font_title.render("Spellbound Reborn", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
        for button in self.buttons:
            button.draw(self.screen)
        self.draw_gold_counter(WIDTH - 25, 35, self.save_data["gold"])

    def draw_upgrades(self):
        title = self.font_title.render("Ulepszenia", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 70)))
        self.draw_gold_counter(WIDTH // 2 + 30, 140, self.save_data["gold"])

        mouse = pygame.mouse.get_pos()
        gold = self.save_data["gold"]

        for upgrade, row, buy in self.meta_rows:
            level = self.save_data["levels"].get(upgrade["id"], 0)
            maxed = level >= upgrade["max_level"]

            pygame.draw.rect(self.screen, (40, 40, 60), row, border_radius=10)

            # Nazwa i poziom
            name = self.font_card_title.render(upgrade["name"], True, WHITE)
            self.screen.blit(name, (row.x + 20, row.y + 8))
            lvl = self.font_small.render(f"Poziom {level}/{upgrade['max_level']}", True, (150, 150, 170))
            self.screen.blit(lvl, (row.x + 20, row.y + 40))

            # Wartość statystyki: teraz -> po zakupie
            stat = upgrade["stat"]
            current = format_value(stat, meta_stat_value(upgrade, level))
            if maxed:
                effect = self.font_card_title.render(current, True, GOLD_COLOR)
            else:
                nxt = format_value(stat, meta_stat_value(upgrade, level + 1))
                effect = self.font_card_title.render(f"{current} -> {nxt}", True, WHITE)
            self.screen.blit(effect, effect.get_rect(midleft=(row.x + 330, row.centery)))

            # Przycisk kupna
            if maxed:
                bg, label_text, label_color = (50, 50, 60), "MAX", GOLD_COLOR
            else:
                cost = meta_cost(upgrade, level)
                if gold >= cost:
                    bg = (80, 160, 90) if buy.collidepoint(mouse) else (60, 130, 70)
                    label_text, label_color = f"Kup: {cost}", WHITE
                else:
                    bg, label_text, label_color = (60, 60, 70), f"Kup: {cost}", (200, 100, 100)
            pygame.draw.rect(self.screen, bg, buy, border_radius=8)
            label = self.font_small.render(label_text, True, label_color)
            self.screen.blit(label, label.get_rect(center=buy.center))

        hint = self.font_small.render("ESC - wróć do menu", True, (150, 150, 170))
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 690)))

    def draw_game(self):
        self.pickups.draw(self.screen)
        self.enemies.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw_health_bar(self.screen)
        self.enemy_bullets.draw(self.screen)
        self.bullets.draw(self.screen)
        self.player.draw(self.screen)
        self.draw_hud()
        self.draw_wave_info()

    def draw_hud(self):
        p = self.player
        bar_w = 250

        # Pasek HP
        pygame.draw.rect(self.screen, HP_BAR_BG, (20, 20, bar_w, 22))
        pygame.draw.rect(self.screen, HP_BAR_FG, (20, 20, bar_w * max(p.hp, 0) / p.max_hp, 22))
        hp_text = self.font_small.render(f"{max(p.hp, 0)}/{p.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (bar_w + 30, 17))

        # Pasek XP + poziom
        pygame.draw.rect(self.screen, XP_BAR_BG, (20, 50, bar_w, 12))
        pygame.draw.rect(self.screen, XP_COLOR, (20, 50, bar_w * p.xp / p.xp_to_next, 12))
        lvl_text = self.font_small.render(f"Poziom {p.level}", True, WHITE)
        self.screen.blit(lvl_text, (bar_w + 30, 43))

        # Złoto
        pygame.draw.circle(self.screen, GOLD_COLOR, (30, 85), 8)
        gold_text = self.font_small.render(str(p.gold), True, WHITE)
        self.screen.blit(gold_text, (46, 72))

    def draw_wave_info(self):
        w = self.waves

        # Numer fali na górze ekranu
        title = "BOSS" if w.is_boss_wave() else f"Fala {w.number}/{w.total}"
        text = self.font_card_title.render(title, True, WHITE)
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 30)))

        if w.state == "wave":
            left = self.font_small.render(f"Pozostało: {w.remaining(len(self.enemies))}", True, (200, 200, 220))
            self.screen.blit(left, left.get_rect(center=(WIDTH // 2, 62)))

        # Duży pasek zdrowia bossa
        boss = next((e for e in self.enemies if e.is_boss), None)
        if boss:
            bar_w, bar_h = 600, 20
            x, y = (WIDTH - bar_w) // 2, 85
            pygame.draw.rect(self.screen, HP_BAR_BG, (x, y, bar_w, bar_h))
            pygame.draw.rect(self.screen, BOSS_BAR_FG, (x, y, bar_w * max(boss.hp, 0) / boss.max_hp, bar_h))
            pygame.draw.rect(self.screen, WHITE, (x, y, bar_w, bar_h), 2)

        # Baner w przerwie przed falą
        if w.state == "intermission":
            color = (255, 80, 80) if w.is_boss_wave() else WHITE
            banner = self.font_title.render(w.label(), True, color)
            self.screen.blit(banner, banner.get_rect(center=(WIDTH // 2, 260)))
            countdown = self.font_button.render(f"Start za {math.ceil(w.timer)} s", True, (200, 200, 220))
            self.screen.blit(countdown, countdown.get_rect(center=(WIDTH // 2, 330)))

    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("Pauza", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 200)))
        for button in self.pause_buttons:
            button.draw(self.screen)
        hint = self.font_small.render("ESC - wznów grę", True, (170, 170, 190))
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 490)))

    def draw_level_up(self):
        # Przyciemnione tło
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("Nowy poziom!", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 80)))
        sub = self.font_small.render(
            "Wybierz ulepszenie (kliknij kartę albo naciśnij 1, 2, 3)", True, (170, 170, 190)
        )
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 140)))

        mouse = pygame.mouse.get_pos()
        for i, (card, rect) in enumerate(zip(self.cards, self.card_rects)):
            hovered = rect.collidepoint(mouse)
            bg = (60, 60, 90) if hovered else (40, 40, 60)
            pygame.draw.rect(self.screen, bg, rect, border_radius=14)
            pygame.draw.rect(self.screen, card["color"], rect, width=4, border_radius=14)

            # Rzadkość
            rarity = self.font_small.render(card["rarity_label"].upper(), True, card["color"])
            self.screen.blit(rarity, rarity.get_rect(center=(rect.centerx, rect.top + 40)))

            # Nazwa ulepszenia
            name = self.font_card_title.render(card["name"], True, WHITE)
            self.screen.blit(name, name.get_rect(center=(rect.centerx, rect.top + 120)))

            # Bonus, np. +20%
            bonus = self.font_card_title.render(card["bonus_text"], True, card["color"])
            self.screen.blit(bonus, bonus.get_rect(center=(rect.centerx, rect.top + 190)))

            # Wartość przed -> po, np. 10 -> 12
            values = self.font_card_value.render(
                f'{card["old_text"]} -> {card["new_text"]}', True, WHITE
            )
            self.screen.blit(values, values.get_rect(center=(rect.centerx, rect.top + 260)))

            # Podpowiedź klawisza
            key_hint = self.font_small.render(f"[{i + 1}]", True, (150, 150, 170))
            self.screen.blit(key_hint, key_hint.get_rect(center=(rect.centerx, rect.bottom - 40)))

    def draw_end_screen(self, title_text):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        text = self.font_title.render(title_text, True, WHITE)
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))
        summary = self.font_button.render(
            f"Poziom: {self.player.level}   Zabici: {self.kills}   Złoto: +{self.player.gold}",
            True, WHITE,
        )
        self.screen.blit(summary, summary.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))
        total = self.font_small.render(
            f"Łącznie złota: {self.save_data['gold']}  (wydasz je w menu, w Ulepszeniach)",
            True, GOLD_COLOR,
        )
        self.screen.blit(total, total.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))
        hint = self.font_small.render("Naciśnij ESC, aby wrócić do menu", True, WHITE)
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90)))

    def draw_placeholder(self, title_text):
        title = self.font_title.render(title_text, True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
        hint = self.font_small.render("(w budowie) - ESC wraca do menu", True, WHITE)
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 300)))


if __name__ == "__main__":
    Game().run()