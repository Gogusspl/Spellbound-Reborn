import random
from settings import *

# Skład fal: {typ wroga: ilość}. Typy są zdefiniowane w settings.py (ENEMY_TYPES).
# Ostatnia fala to boss - po jego pokonaniu wygrywasz.
WAVES = [
    {"basic": 10},                              # fala 1
    {"basic": 12, "fast": 6},                   # fala 2 - nowy wróg: szybki
    {"basic": 12, "fast": 8, "tank": 4},        # fala 3 - nowy wróg: tank
    {"boss": 1},                                # boss
]


class WaveManager:
    """
    Stany:
      "intermission" - odliczanie do kolejnej fali (czas na zebranie dropów)
      "wave"         - wrogowie z fali się pojawiają, a fala kończy się,
                       gdy wszyscy zostaną zabici
      "done"         - ostatnia fala (boss) pokonana
    """

    def __init__(self):
        self.index = 0
        self.state = "intermission"
        self.timer = FIRST_WAVE_DELAY
        self.queue = []             # wrogowie, którzy jeszcze nie pojawili się w tej fali
        self.spawn_timer = 0
        self.total = len(WAVES) - 1  # liczba zwykłych fal (bez bossa)

    @property
    def number(self):
        return self.index + 1

    def is_boss_wave(self):
        return "boss" in WAVES[self.index]

    def label(self):
        return "BOSS" if self.is_boss_wave() else f"Fala {self.number}"

    def remaining(self, alive):
        """Ilu wrogów jeszcze zostało do pokonania w tej fali."""
        return len(self.queue) + alive

    def update(self, dt, alive):
        """Zwraca listę typów wrogów, którzy mają się pojawić w tej klatce."""
        spawned = []

        if self.state == "intermission":
            self.timer -= dt
            if self.timer <= 0:
                self._start_wave()

        elif self.state == "wave":
            if self.queue:
                self.spawn_timer -= dt
                if self.spawn_timer <= 0 and alive < MAX_ENEMIES_ALIVE:
                    spawned.append(self.queue.pop())
                    self.spawn_timer = WAVE_SPAWN_INTERVAL
            elif alive == 0:
                self._finish_wave()

        return spawned

    def _start_wave(self):
        self.queue = []
        for kind, count in WAVES[self.index].items():
            self.queue += [kind] * count
        random.shuffle(self.queue)   # różne typy pojawiają się wymieszane
        self.spawn_timer = 0
        self.state = "wave"

    def _finish_wave(self):
        if self.index >= len(WAVES) - 1:
            self.state = "done"
        else:
            self.index += 1
            self.timer = WAVE_BREAK_TIME
            self.state = "intermission"