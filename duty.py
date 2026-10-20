from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Tashkent")

WEEKDAYS_UZ = ["Dush", "Sesh", "Chor", "Pay", "Juma", "Shan", "Yak"]


def today_date() -> date:
    return datetime.now(TZ).date()


def weekday_uz(d: date) -> str:
    return WEEKDAYS_UZ[d.weekday()]


def tasks_text(crew: dict) -> str:
    return "\n".join(f"{i}. {t}" for i, t in enumerate(crew["tasks"], start=1))


def display_person(person: dict) -> str:
    username = person.get("username")
    return f"{person['name']} (@{username})" if username else person["name"]


def display_people(people: list[dict]) -> str:
    return ", ".join(display_person(p) for p in people)


def plain_names(people: list[dict]) -> str:
    return ", ".join(p["name"] for p in people)


def shift_count(crew: dict) -> int:
    return len(crew["members"]) // crew["shift_size"]


def shift_index_for(crew: dict, d: date) -> int:
    start = date.fromisoformat(crew["start_date"])
    return (d.toordinal() - start.toordinal()) % shift_count(crew)


def duty_for(crew: dict, d: date) -> list[dict]:
    size = crew["shift_size"]
    idx = shift_index_for(crew, d)
    return crew["members"][idx * size : idx * size + size]


def today(crew: dict) -> list[dict]:
    return duty_for(crew, today_date())


def tomorrow(crew: dict) -> list[dict]:
    return duty_for(crew, today_date() + timedelta(days=1))


def yesterday(crew: dict) -> list[dict]:
    return duty_for(crew, today_date() - timedelta(days=1))


def upcoming(crew: dict, days: int = 7) -> list[tuple[date, list[dict]]]:
    today_d = today_date()
    return [(today_d + timedelta(days=i), duty_for(crew, today_d + timedelta(days=i))) for i in range(days)]


def shifts_roster(crew: dict) -> list[list[dict]]:
    size = crew["shift_size"]
    members = crew["members"]
    return [members[i : i + size] for i in range(0, len(members), size)]
