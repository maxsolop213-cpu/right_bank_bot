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
from datetime import datetime
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

# створюємо аркуш для зауважень якщо нема
try:
    remarks_ws = sheet.worksheet("PhotoRemarks")
except:
    remarks_ws = sheet.add_worksheet(title="PhotoRemarks", rows=100, cols=4)
    remarks_ws.append_row(["Дата", "Користувач", "Автор зауваження", "Текст"])

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(name)

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


# ---------- Корисна функція ----------
def extract_codes_any_format(text):
    if not text:
        return []
    joined = re.sub(r"(?<=\d)[\s\-](?=\d)", "", text)
    cleaned = re.sub(r"[^\d]", " ", joined)
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


# ---------- АНАЛІЗ (фото+коди) ----------
photo_data = {}
album_captions = {}

@bot.message_handler(content_types=["photo", "document", "text"], func=lambda m: m.chat.id == PHOTO_GROUP_ID)
def handle_photo_group_message(message):
    text_content = message.caption or message.text
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

    if message.photo or (getattr(message, "document", None) and getattr(message.document, "mime_type", "").startswith("image")):
        photo_data[uid]["photos"] += 1
        if not text_content:
            photo_data[uid]["no_caption"] += 1

    codes = extract_codes_any_format(text_content) if text_content else []
    if codes:
        photo_data[uid]["codes_count"] += len(codes)
        photo_data[uid]["times"].append(now)


def generate_photo_stats_text():
    tz = pytz.timezone("Europe/Kyiv")
    if not photo_data:
        return "📊 Даних за сьогодні немає."
    text = f"📊 Статистика за {datetime.now(tz).strftime('%d.%m')}\n"
    all_users = users_ws.get_all_records()
    sent_users = set(photo_data.keys())

    sorted_data = sorted(photo_data.items(), key=lambda x: (x[1]["codes_count"], x[1]["photos"]), reverse=True)
    for uid, data in sorted_data:
        times = sorted(data["times"])
        avg_interval = 0
        if len(times) > 1:
            fmt = "%H:%M:%S"
            diffs = [(datetime.strptime(t2, fmt) - datetime.strptime(t1, fmt)).seconds for t1, t2 in zip(times, times[1:])]
            avg_interval = int(sum(diffs) / len(diffs) / 60)
        text += f"\n{data['name']} — {data['codes_count']} кодів, {data['photos']} фото\n"
        text += f"⏰ Почав: {times[0] if times else '-'} | Завершив: {times[-1] if times else '-'} | 🕐 Інтервал: ~{avg_interval} хв\n"

    excluded_roles = {"св", "sv", "tm", "тм"}
    missing = [u["Ім’я"] for u in all_users if str(u.get("Telegram_ID", "")).isdigit() and str(u["Telegram_ID"]) not in sent_users and str(u.get("Роль", "")).lower() not in excluded_roles]
    if missing:
        text += "\n❌ Не надіслали сьогодні:\n" + ", ".join(missing)
    return text
def send_photo_stats():
    text = generate_photo_stats_text()
    bot.send_message(PHOTO_GROUP_ID, text)
    bot.send_message(PHOTO_GROUP_ID, "✅ Дякую всім за роботу сьогодні!")


# ---------- /remark ----------
@bot.message_handler(commands=["remark"])
def remark_handler(message):
    if not is_tm_or_admin(message.from_user.id):
        return
    if not message.reply_to_message or not message.text.strip().split(" ", 1)[-1]:
        bot.reply_to(message, "📸 Відповідай на фото з текстом, напр.: /remark Представленість по ТТ не відповідає стандарту")
        return
    target = message.reply_to_message.from_user
    author = message.from_user.first_name
    text = message.text.split(" ", 1)[1]
    tz = pytz.timezone("Europe/Kyiv")
    date = datetime.now(tz).strftime("%d.%m.%Y %H:%M")
    remarks_ws.append_row([date, target.first_name, author, text])
    bot.reply_to(message, f"⚠️ Зауваження для {target.first_name}: {text}\n✅ Зафіксовано у базі.")


# ---------- /check_foto ----------
@bot.message_handler(func=lambda msg: msg.text == "📊 Check Foto" or msg.text == "/check_foto")
def manual_check_foto(message):
    if not is_tm_or_admin(message.from_user.id):
        return
    text = generate_photo_stats_text()
    bot.send_message(message.chat.id, text)


# ---------- РОЗКЛАД (ранок/вечір/нагадування) ----------
def photo_group_scheduler():
    tz = pytz.timezone("Europe/Kyiv")
    last_morning = None
    last_evening = None
    last_remind = None
    last_weekly = None
    while True:
        now = datetime.now(tz)
        # будні дні
        if now.weekday() <= 4:
            # ранкове повідомлення
            if now.hour == 9 and now.minute == 30 and last_morning != now.date():
                bot.send_message(PHOTO_GROUP_ID, "📸 Доброго ранку! Очікую ваші фото та коди 💪")
                last_morning = now.date()
            # нагадування о 10:00
            if now.hour == 10 and now.minute == 0 and last_remind != now.date():
                all_users = users_ws.get_all_records()
                sent_users = set(photo_data.keys())
                missing = [u["Ім’я"] for u in all_users if str(u.get("Telegram_ID", "")).isdigit() and str(u["Telegram_ID"]) not in sent_users and str(u.get("Роль", "")).lower() not in {"св", "tm", "тм"}]
                if missing:
                    bot.send_message(PHOTO_GROUP_ID, f"⚠️ Не надіслали фото сьогодні:\n{', '.join(missing)}")
                last_remind = now.date()
            # вечірній звіт
            if now.hour == 19 and now.minute == 0 and last_evening != now.date():
                send_photo_stats()
                last_evening = now.date()
        # щотижневий звіт у п'ятницю
        if now.weekday() == 4 and now.hour == 19 and now.minute == 5 and last_weekly != now.date():
            bot.send_message(PHOTO_GROUP_ID, "📊 Підсумок тижня: 🥇 Найактивніші, 🕐 Найпізніші старти, 🔁 Кому нагадували частіше. Деталі в таблиці PhotoStats 💼")
            last_weekly = now.date()

        time_module.sleep(30)


threading.Thread(target=photo_group_scheduler, daemon=True).start()


# ---------- Вебхук ----------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "!", 200


@app.route("/")
def home():
    return "Bot is running", 200


# ---------- Запуск ----------
if name == "main":
    bot.remove_webhook()
    render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if render_host:
        bot.set_webhook(url=f"https://{render_host}/{BOT_TOKEN}")
        print(f"✅ Вебхук встановлено: {render_host}")
    else:
        print("⚠️ RENDER_EXTERNAL_HOSTNAME не задано. Перевір ENV у Render.")
    app.run(host="0.0.0.0", port=5000)
