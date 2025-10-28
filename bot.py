import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from flask import Flask, request
import os
import json
import random
import threading
import time as time_module
from datetime import datetime, time as dtime
import pytz
import re

# ---------- Налаштування ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_SHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

ADMIN_ID = 6851674667
TM_IDS = [6851674667, 6833216700]
PHOTO_GROUP_ID = -1003236605419  # 📸 ID групи з фото

scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDENTIALS), scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(MAIN_SHEET_ID)
users_ws = sheet.worksheet("Users")
photo_ws = sheet.worksheet("PhotoStats")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---------- МОТИВАЦІЯ ----------
MOTIVATION_DAILY = [
    "💼 Гарного й продуктивного дня!",
    "🚀 Фокус і дія! Продуктивного дня!",
    "⚡️ Сильний старт = сильний результат. Продуктивного дня!",
    "📈 Маленькі кроки щодня — великі перемоги. Успіхів!",
    "🎯 Концентрація → результат. Гарного дня!",
    "🧠 Плануй і роби. Максимальної продуктивності сьогодні!",
    "🔥 Твій ритм — твоя перевага. Продуктивного дня!",
    "🏁 Починай чітко, завершуй впевнено. Гарного дня!",
    "🌟 Тільки вперед. Нехай день буде ефективним!",
    "✅ Діємо без відкладань. Продуктивного дня!"
]

# ---------- ХЕЛПЕРИ ----------
def get_user_data(user_id):
    users = users_ws.get_all_records()
    for user in users:
        if str(user_id) == str(user.get("Telegram_ID", "")).strip():
            return user
    return None


def normalize_url(url):
    if not url:
        return None
    return url.replace("/edit", "/viewer")


def all_user_chat_ids():
    rows = users_ws.get_all_records()
    ids = []
    for r in rows:
        tid = str(r.get("Telegram_ID", "")).strip()
        if tid.isdigit():
            ids.append(int(tid))
    return ids


def is_tm_or_admin(user_id):
    """Визначає, чи користувач має роль ТМ, Admin або VIP ТП"""
    user = get_user_data(user_id)
    if not user:
        return False
    role = str(user.get("Роль", "")).lower()
    return (
        role in ["tm", "тм", "admin", "адмін", "vip тп", "vip tp"]
        or user_id in TM_IDS
        or user_id == ADMIN_ID
    )

# ---------- Корисна функція для витягу кодів (будь-який формат) ----------
def extract_codes_any_format(text):
    """Повертає список кодів у тексті: 123456 або 123 456 або 123-456 і т.д."""
    if not text:
        return []
    # З'єднати цифри, розділені пробілами/дефісами, наприклад "123 456" -> "123456"
    joined = re.sub(r"(?<=\d)[\s\-](?=\d)", "", text)
    # Замінити все, крім цифр, на пробіли — щоб не зліплювати літери
    cleaned = re.sub(r"[^\d]", " ", joined)
    # Знайти послідовності від 3 до 8 цифр
    return re.findall(r"(?<!\d)(\d{3,8})(?!\d)", cleaned)


# ---------- ГОЛОВНЕ МЕНЮ ----------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в списку користувачів. Звернись до керівника.")
        return

    name = user.get("Ім’я", "користувач")
    bot.send_message(message.chat.id, f"👋 Привіт, {name}! {random.choice(MOTIVATION_DAILY)}")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🗺 Територія", "🧩 Сервіси")
    markup.add("🎯 Фокуси", "📚 Знання")

    if is_tm_or_admin(user_id):
        markup.add("📊 Check Foto", "📨 Оновлення даних", "🎯 Фокус дня (нагадування)")

    bot.send_message(message.chat.id, "Вибери розділ 👇", reply_markup=markup)
# ---------- ПІДМЕНЮ ----------
@bot.message_handler(func=lambda msg: msg.text == "🗺 Територія")
def territory_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🗺 Карта територій")
    markup.add("📋 План", "📊 Індекси", "📅 Візити", "✅ Задачі")
    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "📍 Територія:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "🧩 Сервіси")
def services_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛠 Сервіс-C", "⚙️ Сервіс-Х", "👑 Premium Club", "💰 МФ")
    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "🧩 Сервіси:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "🎯 Фокуси")
def focus_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎯 Фокуси місяця", "🌱 Розвиток територій", "🎁 Промо", "🎯 Фокус дня")
    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "🎯 Фокуси:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "📚 Знання")
def knowledge_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📖 База знань", "💎 JET")
    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "📚 Знання:", reply_markup=markup)


# ---------- АНАЛІЗ (коди + фото будь-якого типу) ----------
photo_data = {}           # key: uid -> {"name","codes_count","photos","times","no_caption"}
album_captions = {}       # media_group_id -> caption (для альбомів)

@bot.message_handler(content_types=["photo", "document", "text"], func=lambda m: m.chat.id == PHOTO_GROUP_ID)
def handle_photo_group_message(message):
    """
    Обробляємо:
     - photo (message.photo)
     - document з image/* mime (message.document)
     - текст (message.text)
    Рахуємо коди (з caption або text) і фотографії (будь-які).
    """
    # --- діагностика (зняти або коментувати, якщо не потрібно) ---
    # print(f"DEBUG: got content_type={message.content_type}, from={getattr(message.from_user,'first_name',None)}")

    # отримуємо текст для аналізу коду (caption або текст повідомлення)
    text_content = None
    if getattr(message, "caption", None):
        text_content = message.caption
    elif getattr(message, "text", None):
        text_content = message.text

    # альбоми: зберегти caption від першого елемента
    if getattr(message, "media_group_id", None):
        mgid = str(message.media_group_id)
        if message.caption:
            album_captions[mgid] = message.caption
        elif mgid in album_captions and not text_content:
            text_content = album_captions[mgid]

    uid = str(message.from_user.id)
    name = message.from_user.first_name or message.from_user.username or "Невідомий"
    tz = pytz.timezone("Europe/Kyiv")
    now = datetime.now(tz).strftime("%H:%M:%S")

    if uid not in photo_data:
        photo_data[uid] = {"name": name, "codes_count": 0, "photos": 0, "times": [], "no_caption": 0}

    # Порахувати фото (всі типи зображень)
    counted_image = False
    if message.photo:
        photo_data[uid]["photos"] += 1
        counted_image = True
    elif getattr(message, "document", None):
        dt = getattr(message.document, "mime_type", "") or ""
        fname = getattr(message.document, "file_name", "") or ""
        # якщо документ — картинка (image/*) або має розширення зображення
        if dt.startswith("image/") or re.search(r"\.(jpg|jpeg|png|webp|gif|bmp|heic)$", fname, flags=re.IGNORECASE):
            photo_data[uid]["photos"] += 1
            counted_image = True

    # Якщо це зображення без підпису — відмічаємо no_caption (щоб відрізнити)
    if counted_image and not text_content:
        photo_data[uid]["no_caption"] += 1
# Знайти коди в тексті (caption або text) — працює для підписів під фото та для окремих смс
    codes = extract_codes_any_format(text_content) if text_content else []
    if codes:
        # збільшуємо загальну кількість кодів (рахуємо кожен знайдений як окремий код)
        photo_data[uid]["codes_count"] += len(codes)
        # лог часу (фіксуємо час відправки кодів)
        photo_data[uid]["times"].append(now)


def generate_photo_stats_text():
    tz = pytz.timezone("Europe/Kyiv")
    if not photo_data:
        return "📊 Даних за сьогодні немає."
    text = f"📊 Статистика за {datetime.now(tz).strftime('%d.%m')}\n"
    all_users = users_ws.get_all_records()
    sent_users = set(photo_data.keys())

    # Сортування: по кількості кодів, потім по фото
    sorted_data = sorted(photo_data.items(), key=lambda x: (x[1]["codes_count"], x[1]["photos"]), reverse=True)
    for uid, data in sorted_data:
        times = sorted(data["times"])
        avg_interval = 0
        if len(times) > 1:
            fmt = "%H:%M:%S"
            diffs = [(datetime.strptime(t2, fmt) - datetime.strptime(t1, fmt)).seconds for t1, t2 in zip(times, times[1:])]
            avg_interval = int(sum(diffs) / len(diffs) / 60)
        text += f"\n{data['name']} — {data['codes_count']} кодів, {data['photos']} фото\n"
        text += f"⏰ Почав: {times[0] if times else '-'} | Завершив: {times[-1] if times else '-'}\n"
        text += f"🕐 Інтервал: ~{avg_interval} хв"
        if data.get("no_caption", 0):
            text += f" | 📭 без підпису: {data['no_caption']}"
        text += "\n"

    # 🧾 Хто не надіслав — виключаємо ролі СВ і ТМ
    excluded_roles = {"св", "sv", "tm", "тм"}
    missing = [
        u["Ім’я"]
        for u in all_users
        if str(u.get("Telegram_ID", "")).strip().isdigit()
        and str(u["Telegram_ID"]) not in sent_users
        and str(u.get("Роль", "")).lower() not in excluded_roles
    ]
    if missing:
        text += "\n❌ Не надіслали сьогодні:\n" + ", ".join(missing)
    return text


def save_photo_stats_to_sheet():
    for uid, data in photo_data.items():
        times = sorted(data["times"])
        first = times[0] if times else "-"
        last = times[-1] if times else "-"
        photo_ws.append_row([
            data["name"], uid, data["codes_count"], data["photos"], first, last,
            # avg interval
            int((sum(
                (datetime.strptime(t2, "%H:%M:%S") - datetime.strptime(t1, "%H:%M:%S")).seconds
                for t1, t2 in zip(times, times[1:])
            ) / len(times[1:]) / 60) if len(times) > 1 else 0),
            data.get("no_caption", 0)
        ])
    photo_data.clear()


def send_photo_stats():
    text = generate_photo_stats_text()
    bot.send_message(PHOTO_GROUP_ID, text)
    bot.send_message(PHOTO_GROUP_ID, "✅ Дякую всім за роботу сьогодні!")
    save_photo_stats_to_sheet()


# ---------- /check_foto або кнопка ----------
@bot.message_handler(func=lambda msg: msg.text == "📊 Check Foto" or msg.text == "/check_foto")
def manual_check_foto(message):
    if not is_tm_or_admin(message.from_user.id):
        return
    text = generate_photo_stats_text()
    bot.send_message(message.chat.id, text)


# ---------- РОЗКЛАД (ранок/вечір) ----------
def photo_group_scheduler():
    tz = pytz.timezone("Europe/Kyiv")
    last_morning = None
    last_evening = None
    while True:
        now = datetime.now(tz)
        if now.weekday() <= 4:
            if now.hour == 9 and now.minute == 30 and last_morning != now.date():
                bot.send_message(PHOTO_GROUP_ID, "📸 Доброго ранку! Очікую ваші фото та коди 💪")
                last_morning = now.date()
            if now.hour == 19 and now.minute == 0 and last_evening != now.date():
                send_photo_stats()
                last_evening = now.date()
        time_module.sleep(30)


threading.Thread(target=photo_group_scheduler, daemon=True).start()

# ---------- ПОВЕРНЕННЯ ДО МЕНЮ ----------
@bot.message_handler(func=lambda msg: msg.text == "⬅️ Назад")
def back_to_main(message):
    start(message)
# ---------- ОБРОБКА ЛІНКІВ ----------
SKIP_BTNS = {"🗺 Територія", "🧩 Сервіси", "🎯 Фокуси", "📚 Знання",
              "⬅️ Назад", "📨 Оновлення даних", "🎯 Фокус дня (нагадування)", "📊 Check Foto"}


@bot.message_handler(func=lambda msg: msg.text not in SKIP_BTNS)
def handle_links(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return
    column = message.text.strip()
    url = user.get(column)
    if not url:
        bot.send_message(message.chat.id, f"⛔️ Для '{column}' ще немає посилання.")
        return
    bot.send_message(message.chat.id, f"🔗 {column}:\n{normalize_url(url)}")


# ---------- РАНКОВА МОТИВАЦІЯ ----------
def daily_sender_loop():
    tz = pytz.timezone("Europe/Kyiv")
    last_sent_date = None
    while True:
        now = datetime.now(tz)
        if now.weekday() <= 4 and now.hour == 9 and now.minute == 30:
            today = now.date()
            if last_sent_date != today:
                text = random.choice(MOTIVATION_DAILY)
                for cid in all_user_chat_ids():
                    try:
                        bot.send_message(cid, text)
                    except Exception:
                        pass
                last_sent_date = today
        time_module.sleep(30)


# ---------- FLASK ВЕБХУК ----------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def home():
    return "Bot is running", 200

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    threading.Thread(target=daily_sender_loop, daemon=True).start()
    bot.remove_webhook()
    render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if render_host:
        bot.set_webhook(url=f"https://{render_host}/{BOT_TOKEN}")
        print(f"✅ Вебхук встановлено: {render_host}")
    else:
        print("⚠️ RENDER_EXTERNAL_HOSTNAME не задано. Перевір ENV у Render.")
    app.run(host="0.0.0.0", port=5000)
