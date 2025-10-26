import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from flask import Flask, request
import os
import threading

# ---------- Налаштування ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_SHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

scope = ["https://www.googleapis.com/auth/spreadsheets"]

# Ініціалізація Google Sheets
import json
creds_dict = json.loads(GOOGLE_CREDENTIALS)
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(MAIN_SHEET_ID)
users_ws = sheet.worksheet("Users")

bot = telebot.TeleBot(BOT_TOKEN)

# ---------- ФУНКЦІЇ ----------

def get_user_data(user_id):
    """Отримати дані користувача з таблиці Users"""
    users = users_ws.get_all_records()
    for user in users:
        if str(user_id) == str(user["Telegram_ID"]):
            return user
    return None


def normalize_url(url):
    """Замінює /edit → /viewer для посилань Google"""
    if not url:
        return None
    return url.replace("/edit", "/viewer")


# ---------- КОМАНДА /start ----------

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.send_message(message.chat.id, "⚠️ Тебе немає в списку користувачів. Звернись до керівника.")
        return

    role = user["Роль"]
    name = user["Ім’я"]
    bot.send_message(message.chat.id, f"👋 Привіт, {name}! Твоя роль: {role}")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "🗺 Карта територій", "📋 План", "🎯 Фокуси",
        "✅ Задачі", "🎁 Промо", "💰 МФ",
        "🛠 Сервіс-C", "⚙️ Сервіс-Х", "🌱 Розвиток територій"
    ]
    for b in buttons:
        markup.add(b)

    bot.send_message(message.chat.id, "Вибери розділ 👇", reply_markup=markup)


# ---------- ОБРОБКА КНОПОК ----------

@bot.message_handler(func=lambda message: message.text in [
    "🗺 Карта територій", "📋 План", "🎯 Фокуси",
    "✅ Задачі", "🎁 Промо", "💰 МФ",
    "🛠 Сервіс-C", "⚙️ Сервіс-Х", "🌱 Розвиток територій"
])
def handle_buttons(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.send_message(message.chat.id, "⚠️ Тебе немає в базі.")
        return

    column = message.text.strip()
    url = user.get(column)

    if not url:
        bot.send_message(message.chat.id, f"⚠️ Для '{column}' поки немає посилання.")
        return

    clean_url = normalize_url(url)
    bot.send_message(message.chat.id, f"🔗 {column}:\n{clean_url}")


# ---------- ВІЛЬНЕ СПІЛКУВАННЯ ДЛЯ СВ ----------

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.send_message(message.chat.id, "⚠️ Тебе немає в базі користувачів.")
        return

    role = str(user.get("Роль", "")).strip()
    text = message.text.strip()

    if role == "СВ":
        bot.send_message(message.chat.id, f"💬 ({user.get('Ім’я')}): {text}")
        return

    known_buttons = [
        "🗺 Карта територій", "📋 План", "🎯 Фокуси",
        "✅ Задачі", "🎁 Промо", "💰 МФ",
        "🛠 Сервіс-C", "⚙️ Сервіс-Х", "🌱 Розвиток територій"
    ]

    if text in known_buttons:
        handle_buttons(message)
    else:
        bot.send_message(message.chat.id, "⚠️ Скористайся кнопками нижче ⬇️")


# ---------- FLASK для Render (щоб бот не засинав) ----------

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("✅ Бот запущений")
    bot.polling(none_stop=True)
