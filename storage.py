import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "state.json"


def load_state() -> dict:
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def crews() -> list[dict]:
    return load_state()["crews"]


def crew_by_id(crew_id: str) -> dict | None:
    return next((c for c in crews() if c["id"] == crew_id), None)


def crew_by_chat_id(chat_id: int) -> dict | None:
    return next((c for c in crews() if c.get("chat_id") == chat_id), None)


def set_crew_chat_id(crew_id: str, chat_id: int) -> None:
    state = load_state()
    for c in state["crews"]:
        if c["id"] == crew_id:
            c["chat_id"] = chat_id
            break
    save_state(state)
