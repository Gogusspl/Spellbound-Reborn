# Ustawienia i stałe gry

WIDTH = 1280
HEIGHT = 720
FPS = 60

# Kolory
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG_COLOR = (25, 25, 35)
BUTTON_COLOR = (60, 60, 90)
BUTTON_HOVER = (90, 90, 140)
PLAYER_COLOR = (70, 130, 255)
BULLET_COLOR = (190, 120, 255)
ENEMY_BULLET_COLOR = (255, 90, 90)
GOLD_COLOR = (255, 215, 0)
XP_COLOR = (80, 220, 255)
HP_BAR_BG = (80, 20, 20)
HP_BAR_FG = (60, 200, 80)
XP_BAR_BG = (20, 50, 70)
BOSS_BAR_FG = (200, 40, 40)

# Gracz
PLAYER_SIZE = 40
PLAYER_SPEED = 300          # piksele na sekundę
PLAYER_MAX_HP = 100
PLAYER_HIT_COOLDOWN = 0.6   # sekundy nietykalności po otrzymaniu obrażeń
PLAYER_DAMAGE = 10
PLAYER_ATTACK_SPEED = 1.5   # strzałów na sekundę
PLAYER_ATTACK_RANGE = 500   # zasięg w pikselach
PLAYER_PICKUP_RANGE = 90    # z jakiej odległości przedmioty lecą do gracza

# Pociski gracza
BULLET_SPEED = 650
BULLET_RADIUS = 6

# Pociski wrogów (używa ich boss)
ENEMY_BULLET_SPEED = 260
ENEMY_BULLET_RADIUS = 7

# Typy wrogów - żeby dodać nowy typ, wystarczy dopisać wpis do słownika.
#   radius      - wielkość kółka
#   speed, hp, damage - statystyki
#   xp          - ile XP wypada po śmierci
#   gold        - wartość monety, gold_chance - szansa, że moneta wypadnie
#   outline     - (opcjonalnie) kolor obwódki
#   shoot_interval, bullet_damage, ring_bullets - (opcjonalnie) strzelanie bossa
ENEMY_TYPES = {
    "basic": {
        "radius": 16, "color": (220, 60, 60),
        "speed": 120, "hp": 30, "damage": 10,
        "xp": 5, "gold": 1, "gold_chance": 0.5,
    },
    "fast": {
        "radius": 11, "color": (255, 150, 40),
        "speed": 210, "hp": 20, "damage": 8,
        "xp": 6, "gold": 1, "gold_chance": 0.5,
    },
    "tank": {
        "radius": 26, "color": (150, 50, 150),
        "speed": 70, "hp": 120, "damage": 20,
        "xp": 15, "gold": 3, "gold_chance": 0.8,
    },
    "boss": {
        "radius": 60, "color": (130, 20, 20), "outline": GOLD_COLOR,
        "speed": 60, "hp": 800, "damage": 25,
        "xp": 50, "gold": 30, "gold_chance": 1.0,
        "shoot_interval": 2.0, "bullet_damage": 15, "ring_bullets": 10,
    },
}

# Fale
FIRST_WAVE_DELAY = 2.0      # pauza przed pierwszą falą
WAVE_BREAK_TIME = 4.0       # pauza między falami (czas na zebranie dropów)
WAVE_SPAWN_INTERVAL = 0.5   # co ile sekund pojawia się kolejny wróg z fali
MAX_ENEMIES_ALIVE = 30      # limit wrogów na ekranie jednocześnie

# Dropy
XP_RADIUS = 6
GOLD_RADIUS = 4             # mniejsze od XP
PICKUP_FLY_SPEED = 500

# Poziomy
XP_TO_FIRST_LEVEL = 20
XP_LEVEL_GROWTH = 1.4       # każdy kolejny poziom wymaga 1.4x więcej XP