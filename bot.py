import logging
import os
from datetime import time as dtime

from dotenv import load_dotenv
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from zoneinfo import ZoneInfo

import duty
from storage import crew_by_chat_id, crew_by_id, crews, set_crew_chat_id

load_dotenv()

TOKEN = os.environ["BOT_TOKEN"]
TZ = ZoneInfo("Asia/Tashkent")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("navbatchi")

HELP_TEXT = (
    "🏠 <b>Navbatchi bot</b>\n\n"
    "Pastdagi tugmalardan yoki buyruqlardan foydalaning:\n"
    "/bugun — bugungi navbatchi\n"
    "/ertaga — ertangi navbatchi\n"
    "/kecha — kechagi navbatchi\n"
    "/royxat — barcha navbatchilar ro'yxati\n"
    "/haftalik — keyingi 7 kunlik jadval\n"
    "/belgila — shu guruhni eslatmalar uchun belgilash (faqat adminlar)\n"
)

MENU_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("📅 Bugun", callback_data="bugun"), InlineKeyboardButton("➡️ Ertaga", callback_data="ertaga")],
        [InlineKeyboardButton("⬅️ Kecha", callback_data="kecha"), InlineKeyboardButton("👥 Ro'yxat", callback_data="royxat")],
        [InlineKeyboardButton("🗓 Haftalik", callback_data="haftalik")],
    ]
)

NOT_REGISTERED_TEXT = (
    "⚠️ Bu guruh hali ro'yxatga olinmagan.\n"
    "Admin uchun: /belgila <guruh_id> buyrug'ini ishlating."
)


def _crew_for_chat(chat_id: int) -> dict | None:
    return crew_by_chat_id(chat_id)


def _bugun_text(crew: dict) -> str:
    return (
        f"📅 Bugun navbatchi: <b>{duty.display_people(duty.today(crew))}</b>\n\n"
        f"🧹 Bajarilishi kerak bo'lgan ishlar:\n{duty.tasks_text(crew)}"
    )


def _ertaga_text(crew: dict) -> str:
    return f"📅 Ertaga navbatchi: <b>{duty.plain_names(duty.tomorrow(crew))}</b>"


def _kecha_text(crew: dict) -> str:
    return f"📅 Kecha navbatchi edi: <b>{duty.plain_names(duty.yesterday(crew))}</b>"


def _royxat_text(crew: dict) -> str:
    today_idx = duty.shift_index_for(crew, duty.today_date())
    lines = []
    for i, people in enumerate(duty.shifts_roster(crew)):
        mark = " ⬅️ bugun" if i == today_idx else ""
        lines.append(f"{i + 1}. {duty.plain_names(people)}{mark}")
    return "👥 <b>Navbatchilar ro'yxati:</b>\n\n" + "\n".join(lines)


def _haftalik_text(crew: dict) -> str:
    lines = [
        f"{d.strftime('%d.%m')} ({duty.weekday_uz(d)}) — {duty.plain_names(people)}"
        for d, people in duty.upcoming(crew, 7)
    ]
    return "🗓 <b>Keyingi 7 kun:</b>\n\n" + "\n".join(lines)


MENU_ACTIONS = {
    "bugun": _bugun_text,
    "ertaga": _ertaga_text,
    "kecha": _kecha_text,
    "royxat": _royxat_text,
    "haftalik": _haftalik_text,
}


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(HELP_TEXT, reply_markup=MENU_KEYBOARD)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html("🏠 <b>Navbatchi menyu</b>", reply_markup=MENU_KEYBOARD)


async def on_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = MENU_ACTIONS.get(query.data)
    if not action:
        return
    crew = _crew_for_chat(query.message.chat.id)
    if not crew:
        await query.message.reply_html(NOT_REGISTERED_TEXT)
        return
    await query.message.reply_html(action(crew), reply_markup=MENU_KEYBOARD)


def _command(action) -> callable:
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        crew = _crew_for_chat(update.effective_chat.id)
        if not crew:
            await update.message.reply_html(NOT_REGISTERED_TEXT)
            return
        await update.message.reply_html(action(crew), reply_markup=MENU_KEYBOARD)

    return handler


cmd_bugun = _command(_bugun_text)
cmd_ertaga = _command(_ertaga_text)
cmd_kecha = _command(_kecha_text)
cmd_royxat = _command(_royxat_text)
cmd_haftalik = _command(_haftalik_text)


async def cmd_belgila(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Bu buyruq faqat guruhda ishlaydi.")
        return
    member = await chat.get_member(update.effective_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await update.message.reply_text("Bu buyruqni faqat guruh adminlari ishlata oladi.")
        return

    if context.args:
        crew = crew_by_id(context.args[0])
        if not crew:
            ids = ", ".join(c["id"] for c in crews())
            await update.message.reply_text(f"Bunday guruh topilmadi. Mavjud id'lar: {ids}")
            return
    else:
        unset = [c for c in crews() if not c.get("chat_id")]
        if len(unset) != 1:
            ids = ", ".join(c["id"] for c in crews())
            await update.message.reply_text(
                f"Qaysi ro'yxatni belgilashni aniq ko'rsating: /belgila <id>\nMavjud id'lar: {ids}"
            )
            return
        crew = unset[0]

    set_crew_chat_id(crew["id"], chat.id)
    await update.message.reply_text(
        f"✅ Shu guruh ({chat.title}) \"{crew['id']}\" ro'yxati uchun belgilandi.\n"
        "Har kuni soat 07:00 va 19:00 da xabar yuboriladi."
    )


def _morning_message(crew: dict) -> str:
    name = duty.display_people(duty.today(crew))
    return (
        f"📢 <b>{name}</b>, bugun sizning navbatchilik kuningiz!\n\n"
        f"🧹 Bajarilishi kerak bo'lgan ishlar:\n{duty.tasks_text(crew)}\n\n"
        "✅ Ishlarni bajarib bo'lgach, qilgan ishlaringiz rasmini shu yerga tashlang.\n\n"
        "Omad! 💪\n\n"
        "Ertangi navbatchini bilish uchun: /ertaga"
    )


def _evening_message(crew: dict) -> str:
    name = duty.display_people(duty.today(crew))
    next_name = duty.plain_names(duty.tomorrow(crew))
    return (
        f"🌙 <b>{name}</b>, bugungi navbatchilik kuningiz yakunlanmoqda.\n\n"
        f"🧹 Bajarilishi kerak bo'lgan ishlar:\n{duty.tasks_text(crew)}\n\n"
        "Barcha ishlarni bajardingizmi? Agar hali ulgurmagan bo'lsangiz, hoziroq yakunlang va "
        "qilgan ishlaringiz rasmini shu yerga tashlang. 📸\n\n"
        f"Ertaga navbatchi: <b>{next_name}</b> — batafsil: /ertaga"
    )


async def _send_to_all_crews(context: ContextTypes.DEFAULT_TYPE, build_message) -> None:
    for crew in crews():
        chat_id = crew.get("chat_id")
        if not chat_id:
            logger.warning("Crew %s has no chat_id; skipping", crew["id"])
            continue
        try:
            await context.bot.send_message(
                chat_id=chat_id, text=build_message(crew), parse_mode=ParseMode.HTML, reply_markup=MENU_KEYBOARD
            )
        except Exception:
            logger.exception("Failed to send reminder to crew %s (chat_id=%s)", crew["id"], chat_id)


async def send_morning(context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_to_all_crews(context, _morning_message)


async def send_evening(context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_to_all_crews(context, _evening_message)


async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands(
        [
            BotCommand("bugun", "Bugungi navbatchi"),
            BotCommand("ertaga", "Ertangi navbatchi"),
            BotCommand("kecha", "Kechagi navbatchi"),
            BotCommand("royxat", "Barcha navbatchilar ro'yxati"),
            BotCommand("haftalik", "Keyingi 7 kunlik jadval"),
            BotCommand("menu", "Tugmali menyuni ko'rsatish"),
            BotCommand("belgila", "Shu guruhni eslatmalar uchun belgilash (admin)"),
        ]
    )


def main() -> None:
    app = Application.builder().token(TOKEN).post_init(_post_init).build()

    app.add_handler(CommandHandler(["start", "yordam", "help"], cmd_start))
    app.add_handler(CommandHandler("bugun", cmd_bugun))
    app.add_handler(CommandHandler("ertaga", cmd_ertaga))
    app.add_handler(CommandHandler("kecha", cmd_kecha))
    app.add_handler(CommandHandler("royxat", cmd_royxat))
    app.add_handler(CommandHandler("haftalik", cmd_haftalik))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("belgila", cmd_belgila))
    app.add_handler(CallbackQueryHandler(on_menu_button))

    app.job_queue.run_daily(send_morning, time=dtime(7, 0, tzinfo=TZ), name="morning")
    app.job_queue.run_daily(send_evening, time=dtime(19, 0, tzinfo=TZ), name="evening")

    logger.info("Bot ishga tushdi")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
