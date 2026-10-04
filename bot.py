import logging
import os
from datetime import time as dtime

from dotenv import load_dotenv
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from zoneinfo import ZoneInfo

import duty
from storage import load_state, set_chat_id

load_dotenv()

TOKEN = os.environ["BOT_TOKEN"]
FALLBACK_CHAT_ID = os.environ.get("GROUP_CHAT_ID") or None
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


def _target_chat_id() -> int | None:
    state = load_state()
    return state.get("chat_id") or (int(FALLBACK_CHAT_ID) if FALLBACK_CHAT_ID else None)


def _bugun_text() -> str:
    return (
        f"📅 Bugun navbatchi: <b>{duty.display(duty.today())}</b>\n\n"
        f"🧹 Bajarilishi kerak bo'lgan ishlar:\n{duty.tasks_text()}"
    )


def _ertaga_text() -> str:
    return f"📅 Ertaga navbatchi: <b>{duty.tomorrow()['name']}</b>"


def _kecha_text() -> str:
    return f"📅 Kecha navbatchi edi: <b>{duty.yesterday()['name']}</b>"


def _royxat_text() -> str:
    today_name = duty.today()["name"]
    lines = []
    for i, person in enumerate(duty.roster(), start=1):
        mark = " ⬅️ bugun" if person["name"] == today_name else ""
        lines.append(f"{i}. {person['name']}{mark}")
    return "👥 <b>Navbatchilar ro'yxati:</b>\n\n" + "\n".join(lines)


def _haftalik_text() -> str:
    lines = [f"{d.strftime('%d.%m')} ({duty.weekday_uz(d)}) — {person['name']}" for d, person in duty.upcoming(7)]
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
    action = MENU_ACTIONS.get(query.data)
    await query.answer()
    if not action:
        return
    await query.message.reply_html(action(), reply_markup=MENU_KEYBOARD)


async def cmd_bugun(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(_bugun_text(), reply_markup=MENU_KEYBOARD)


async def cmd_ertaga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(_ertaga_text(), reply_markup=MENU_KEYBOARD)


async def cmd_kecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(_kecha_text(), reply_markup=MENU_KEYBOARD)


async def cmd_royxat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(_royxat_text(), reply_markup=MENU_KEYBOARD)


async def cmd_haftalik(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(_haftalik_text(), reply_markup=MENU_KEYBOARD)


async def cmd_belgila(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Bu buyruq faqat guruhda ishlaydi.")
        return
    member = await chat.get_member(update.effective_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await update.message.reply_text("Bu buyruqni faqat guruh adminlari ishlata oladi.")
        return
    set_chat_id(chat.id)
    await update.message.reply_text(
        f"✅ Shu guruh ({chat.title}) eslatmalar uchun belgilandi.\nHar kuni soat 07:00 va 19:00 da xabar yuboriladi."
    )


def _morning_message() -> str:
    name = duty.display(duty.today())
    return (
        f"📢 <b>{name}</b>, bugun sizning navbatchilik kuningiz!\n\n"
        f"🧹 Bajarilishi kerak bo'lgan ishlar:\n{duty.tasks_text()}\n\n"
        "✅ Ishlarni bajarib bo'lgach, qilgan ishlaringiz rasmini shu yerga tashlang.\n\n"
        "Omad! 💪\n\n"
        "Ertangi navbatchini bilish uchun: /ertaga"
    )


def _evening_message() -> str:
    name = duty.display(duty.today())
    next_name = duty.tomorrow()["name"]
    return (
        f"🌙 <b>{name}</b>, bugungi navbatchilik kuningiz yakunlanmoqda.\n\n"
        f"🧹 Bajarilishi kerak bo'lgan ishlar:\n{duty.tasks_text()}\n\n"
        "Barcha ishlarni bajardingizmi? Agar hali ulgurmagan bo'lsangiz, hoziroq yakunlang va "
        "qilgan ishlaringiz rasmini shu yerga tashlang. 📸\n\n"
        f"Ertaga navbatchi: <b>{next_name}</b> — batafsil: /ertaga"
    )


async def send_morning(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _target_chat_id()
    if not chat_id:
        logger.warning("No target chat set; skipping morning reminder")
        return
    await context.bot.send_message(chat_id=chat_id, text=_morning_message(), parse_mode=ParseMode.HTML, reply_markup=MENU_KEYBOARD)


async def send_evening(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _target_chat_id()
    if not chat_id:
        logger.warning("No target chat set; skipping evening reminder")
        return
    await context.bot.send_message(chat_id=chat_id, text=_evening_message(), parse_mode=ParseMode.HTML, reply_markup=MENU_KEYBOARD)


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
