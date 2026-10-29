import json
import os

# Plik zapisu leży obok kodu gry, niezależnie od tego, skąd uruchamiasz program
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")


def load_game():
    """Wczytuje zapis. Gdy pliku nie ma albo jest uszkodzony, zwraca czysty postęp."""
    data = {"gold": 0, "levels": {}}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            gold = loaded.get("gold", 0)
            if isinstance(gold, int) and gold >= 0:
                data["gold"] = gold
            levels = loaded.get("levels", {})
            if isinstance(levels, dict):
                for key, value in levels.items():
                    if isinstance(value, int) and value >= 0:
                        data["levels"][str(key)] = value
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return data


def save_game(data):
    """Zapisuje postęp. Najpierw do pliku tymczasowego, żeby nie zepsuć zapisu przy awarii."""
    try:
        tmp_file = SAVE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, SAVE_FILE)
    except OSError as error:
        print(f"Nie udało się zapisać gry: {error}")