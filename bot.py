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

# ---------- Налаштування ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_SHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDENTIALS), scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(MAIN_SHEET_ID)
users_ws = sheet.worksheet("Users")

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
    """Повертає список chat_id (Telegram_ID) з таблиці, де поле заповнене."""
    rows = users_ws.get_all_records()
    ids = []
    for r in rows:
        tid = str(r.get("Telegram_ID", "")).strip()
        if tid.isdigit():
            ids.append(int(tid))
    return ids

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
    bot.send_message(message.chat.id, "Вибери розділ 👇", reply_markup=markup)

# ---------- ПІДМЕНЮ ----------
@bot.message_handler(func=lambda msg: msg.text == "🗺 Територія")
def territory_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
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
    markup.add("🎯 Фокуси місяця", "🌱 Розвиток територій", "🎁 Промо")
    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "🎯 Фокуси:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "📚 Знання")
def knowledge_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📖 База знань")
    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "📚 Знання:", reply_markup=markup)

# ---------- ПОВЕРНЕННЯ ДО ГОЛОВНОГО МЕНЮ ----------
@bot.message_handler(func=lambda msg: msg.text == "⬅️ Назад")
def back_to_main(message):
    start(message)

# ---------- ОБРОБКА КНОПОК З ЛІНКАМИ ----------
SKIP_BTNS = {"🗺 Територія", "🧩 Сервіси", "🎯 Фокуси", "📚 Знання", "⬅️ Назад"}

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

    clean_url = normalize_url(url)
    bot.send_message(message.chat.id, f"🔗 {column}:\n{clean_url}")

# ---------- ЩОДЕННЕ ПОВІДОМЛЕННЯ 09:30 (Пн–Пт, Europe/Kyiv) ----------
def daily_sender_loop():
    tz = pytz.timezone("Europe/Kyiv")
    target = dtime(hour=9, minute=30)
    last_sent_date = None

    while True:
        now = datetime.now(tz)
        if now.weekday() <= 4:  # Пн–Пт
            if now.time().hour == target.hour and now.time().minute == target.minute:
                today_str = now.strftime("%Y-%m-%d")
                if last_sent_date != today_str:
                    text = random.choice(MOTIVATION_DAILY)
                    for cid in all_user_chat_ids():
                        try:
                            bot.send_message(cid, text)
                        except Exception:
                            pass
                    last_sent_date = today_str
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
        render_url = f"https://{render_host}/{BOT_TOKEN}"
        bot.set_webhook(url=render_url)
        print(f"✅ Вебхук встановлено: {render_url}")
    else:
        print("⚠️ RENDER_EXTERNAL_HOSTNAME не задано. Перевір ENV у Render.")

    app.run(host="0.0.0.0", port=5000)
