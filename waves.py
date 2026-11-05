import random
from settings import *

WAVES = [
    {"basic": 10},
    {"basic": 12, "fast": 6},
    {"basic": 12, "fast": 8, "tank": 4},
    {"boss": 1},
]

class WaveManager:

    def __init__(self):
        self.index = 0
        self.state = "intermission"
        self.timer = FIRST_WAVE_DELAY
        self.queue = []
        self.spawn_timer = 0
        self.total = len(WAVES) - 1

    @property
    def number(self):
        return self.index + 1

    def is_boss_wave(self):
        return "boss" in WAVES[self.index]

    def label(self):
        return "BOSS" if self.is_boss_wave() else f"Fala {self.number}"

    def remaining(self, alive):
        return len(self.queue) + alive

    def update(self, dt, alive):
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
        random.shuffle(self.queue)
        self.spawn_timer = 0
        self.state = "wave"

    def _finish_wave(self):
        if self.index >= len(WAVES) - 1:
            self.state = "done"
        else:
            self.index += 1
            self.timer = WAVE_BREAK_TIME
            self.state = "intermission"