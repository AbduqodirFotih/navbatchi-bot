import json
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "state.json"
EXAMPLE_FILE = DATA_DIR / "state.example.json"

_DEFAULT_MEMBERS = [
    {"name": "Quvonchbek", "username": "quvonchbek8833"},
    {"name": "Diyorbek", "username": "Atunelie"},
    {"name": "Ibodullo", "username": None},
    {"name": "Muhammad Yahyo", "username": "M2008_31"},
    {"name": "Sardor", "username": "Sardor833"},
    {"name": "O'ralbek", "username": None},
    {"name": "Sarkorbek", "username": "O3071"},
    {"name": "Abduqodir", "username": "abduqodir_fotih"},
]


def _default_state() -> dict:
    return {
        "chat_id": None,
        "start_date": date.today().isoformat(),
        "members": [dict(m) for m in _DEFAULT_MEMBERS],
    }


def load_state() -> dict:
    if not STATE_FILE.exists():
        state = _default_state()
        save_state(state)
        return state
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def set_chat_id(chat_id: int) -> None:
    state = load_state()
    state["chat_id"] = chat_id
    save_state(state)
