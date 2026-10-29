import random
import settings

# Rzadkości kart: kolor, waga losowania (im większa, tym częściej wypada)
# oraz mnożnik, który wzmacnia bonus karty.
RARITIES = {
    "common":    {"label": "Zwykła",     "color": (190, 190, 190), "weight": 50, "mult": 1.0},
    "uncommon":  {"label": "Niezwykła",  "color": (90, 210, 90),   "weight": 30, "mult": 1.5},
    "rare":      {"label": "Rzadka",     "color": (80, 150, 255),  "weight": 15, "mult": 2.2},
    "epic":      {"label": "Epicka",     "color": (180, 90, 255),  "weight": 4,  "mult": 3.5},
    "legendary": {"label": "Legendarna", "color": (255, 170, 30),  "weight": 1,  "mult": 5.0},
}

# Lista ulepszeń. Żeby dodać nową kartę, wystarczy dopisać jeden słownik.
#   stat  - nazwa atrybutu w klasie Player
#   mode  - "percent" (bonus w %) albo "flat" (stała liczba)
#   base  - bazowy bonus (dla common), mnożony potem przez rzadkość
#   int   - True, jeśli wartość ma być liczbą całkowitą
UPGRADES = [
    {"name": "Siła ataku",      "stat": "damage",       "mode": "percent", "base": 0.10, "int": True},
    {"name": "Szybkość ataku",  "stat": "attack_speed", "mode": "percent", "base": 0.10, "int": False},
    {"name": "Zdrowie",         "stat": "max_hp",       "mode": "flat",    "base": 10,   "int": True},
    {"name": "Szybkość ruchu",  "stat": "speed",        "mode": "percent", "base": 0.08, "int": True},
    {"name": "Zasięg ataku",    "stat": "attack_range", "mode": "percent", "base": 0.10, "int": True},
    {"name": "Magnes",          "stat": "pickup_range", "mode": "percent", "base": 0.15, "int": True},
]


def format_value(stat, value):
    """Ładnie formatuje liczbę do wyświetlenia na karcie."""
    if stat == "attack_speed":
        return f"{value:.2f}"
    return str(int(value))


def roll_cards(player, count=3):
    """Losuje `count` różnych kart. Każda ma rzadkość i policzone wartości przed -> po."""
    chosen = random.sample(UPGRADES, count)
    rarity_names = list(RARITIES.keys())
    weights = [RARITIES[r]["weight"] for r in rarity_names]

    cards = []
    for upgrade in chosen:
        rarity = random.choices(rarity_names, weights=weights)[0]
        bonus = upgrade["base"] * RARITIES[rarity]["mult"]

        old = getattr(player, upgrade["stat"])
        if upgrade["mode"] == "percent":
            new = old * (1 + bonus)
            bonus_text = f"+{round(bonus * 100)}%"
        else:
            new = old + bonus
            bonus_text = f"+{round(bonus)}"

        if upgrade["int"]:
            new = round(new)
            if new <= old:      # minimum +1, żeby karta zawsze coś dawała
                new = old + 1
        else:
            new = round(new, 2)

        cards.append({
            "name": upgrade["name"],
            "stat": upgrade["stat"],
            "rarity": rarity,
            "rarity_label": RARITIES[rarity]["label"],
            "color": RARITIES[rarity]["color"],
            "bonus_text": bonus_text,
            "old": old,
            "new": new,
            "old_text": format_value(upgrade["stat"], old),
            "new_text": format_value(upgrade["stat"], new),
        })
    return cards


def apply_upgrade(player, card):
    """Nakłada wybraną kartę na gracza."""
    setattr(player, card["stat"], card["new"])
    # Karta zdrowia od razu leczy o tyle, o ile zwiększyła maksymalne HP
    if card["stat"] == "max_hp":
        player.hp = min(player.max_hp, player.hp + (card["new"] - card["old"]))


# =====================================================================
#  STAŁE ULEPSZENIA (sklep w menu) - kupowane za złoto, zostają na zawsze
# =====================================================================
#   id          - klucz zapisywany w save.json
#   stat        - atrybut gracza, który ulepszenie zmienia
#   base_const  - nazwa stałej z settings.py z bazową wartością statystyki
#   per_level   - o ile rośnie statystyka z każdym poziomem
#   max_level   - maksymalny poziom
#   base_cost   - cena pierwszego poziomu (kolejne drożeją o COST_GROWTH)
META_UPGRADES = [
    {"id": "max_hp",       "name": "Zdrowie",         "stat": "max_hp",
     "base_const": "PLAYER_MAX_HP",       "per_level": 10,  "max_level": 10, "base_cost": 20},
    {"id": "damage",       "name": "Siła ataku",      "stat": "damage",
     "base_const": "PLAYER_DAMAGE",       "per_level": 1,   "max_level": 10, "base_cost": 25},
    {"id": "attack_speed", "name": "Szybkość ataku",  "stat": "attack_speed",
     "base_const": "PLAYER_ATTACK_SPEED", "per_level": 0.1, "max_level": 10, "base_cost": 30},
    {"id": "speed",        "name": "Szybkość ruchu",  "stat": "speed",
     "base_const": "PLAYER_SPEED",        "per_level": 10,  "max_level": 5,  "base_cost": 15},
    {"id": "attack_range", "name": "Zasięg ataku",    "stat": "attack_range",
     "base_const": "PLAYER_ATTACK_RANGE", "per_level": 25,  "max_level": 5,  "base_cost": 20},
    {"id": "pickup_range", "name": "Magnes",          "stat": "pickup_range",
     "base_const": "PLAYER_PICKUP_RANGE", "per_level": 10,  "max_level": 5,  "base_cost": 10},
]

COST_GROWTH = 1.35   # każdy kolejny poziom jest o 35% droższy


def meta_cost(upgrade, level):
    """Cena zakupu kolejnego poziomu (gdy aktualny poziom to `level`)."""
    return round(upgrade["base_cost"] * COST_GROWTH ** level)


def meta_stat_value(upgrade, level):
    """Wartość statystyki na danym poziomie ulepszenia (baza + bonus)."""
    base = getattr(settings, upgrade["base_const"])
    return round(base + upgrade["per_level"] * level, 2)


def buy_meta_upgrade(data, upgrade):
    """Próbuje kupić kolejny poziom. Zwraca True, jeśli się udało."""
    level = data["levels"].get(upgrade["id"], 0)
    if level >= upgrade["max_level"]:
        return False
    cost = meta_cost(upgrade, level)
    if data["gold"] < cost:
        return False
    data["gold"] -= cost
    data["levels"][upgrade["id"]] = level + 1
    return True


def apply_meta_upgrades(player, levels):
    """Nakłada kupione stałe ulepszenia na gracza na początku rundy."""
    for upgrade in META_UPGRADES:
        level = min(levels.get(upgrade["id"], 0), upgrade["max_level"])
        if level > 0:
            setattr(player, upgrade["stat"], meta_stat_value(upgrade, level))
    player.hp = player.max_hp