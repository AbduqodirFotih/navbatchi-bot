from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from storage import load_state

TZ = ZoneInfo("Asia/Tashkent")


def _today() -> date:
    return datetime.now(TZ).date()


TASKS = [
    "Oshxonani uborka qilish (tozalash)",
    "Hammomni uborka qilish (tozalash)",
    "Hojatxona — eski qog'ozlarni olib tashlash va yangi salafan (tualet qog'ozi) qo'yish",
    "Koridorni tozalash — shiftni supurish va changini artish",
]


def tasks_text() -> str:
    return "\n".join(f"{i}. {t}" for i, t in enumerate(TASKS, start=1))


WEEKDAYS_UZ = ["Dush", "Sesh", "Chor", "Pay", "Juma", "Shan", "Yak"]


def weekday_uz(d: date) -> str:
    return WEEKDAYS_UZ[d.weekday()]


def display(person: dict) -> str:
    username = person.get("username")
    return f"{person['name']} (@{username})" if username else person["name"]


def duty_for(d: date) -> dict:
    state = load_state()
    members = state["members"]
    start = date.fromisoformat(state["start_date"])
    idx = (d.toordinal() - start.toordinal()) % len(members)
    return members[idx]


def today() -> dict:
    return duty_for(_today())


def tomorrow() -> dict:
    return duty_for(_today() + timedelta(days=1))


def yesterday() -> dict:
    return duty_for(_today() - timedelta(days=1))


def roster() -> list[dict]:
    return load_state()["members"]


def upcoming(days: int = 7) -> list[tuple[date, dict]]:
    today_d = _today()
    return [(today_d + timedelta(days=i), duty_for(today_d + timedelta(days=i))) for i in range(days)]
