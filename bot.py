import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from flask import Flask, request
import os
import json
import random

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
MOTIVATION = [
    "🚀 Крок за кроком до перемоги!",
    "🔥 Ти справжній профі!",
    "💪 Твоя стабільність — твоя сила!",
    "🌟 Результати приходять до наполегливих!",
    "⚡️ Кожен день — шанс зробити краще!"
]

# ---------- ФУНКЦІЇ ----------
def get_user_data(user_id):
    users = users_ws.get_all_records()
    for user in users:
        if str(user_id) == str(user["Telegram_ID"]):
            return user
    return None

def normalize_url(url):
    if not url:
        return None
    return url.replace("/edit", "/viewer")

# ---------- ГОЛОВНЕ МЕНЮ ----------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в списку користувачів. Звернись до керівника.")
        return

    name = user["Ім’я"]
    bot.send_message(message.chat.id, f"👋 Привіт, {name}! {random.choice(MOTIVATION)}")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🗺 Територія", "🧩 Сервіси")
    markup.add("🎯 Фокуси")
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
    markup.add("🛠 Сервіс-C", "⚙️ Сервіс-Х", "🎁 Промо", "💰 МФ")
    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "🧩 Сервіси:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "🎯 Фокуси")
def focus_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎯 Фокуси місяця", "🌱 Розвиток територій")
    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "🎯 Фокуси:", reply_markup=markup)

# ---------- ПОВЕРНЕННЯ ДО ГОЛОВНОГО МЕНЮ ----------
@bot.message_handler(func=lambda msg: msg.text == "⬅️ Назад")
def back_to_main(message):
    start(message)

# ---------- ОБРОБКА КНОПОК З ЛІНКАМИ ----------
@bot.message_handler(func=lambda msg: msg.text not in ["🗺 Територія", "🧩 Сервіси", "🎯 Фокуси", "⬅️ Назад"])
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
    import requests
    bot.remove_webhook()
    render_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    bot.set_webhook(url=render_url)
    print(f"✅ Вебхук встановлено: {render_url}")
    app.run(host="0.0.0.0", port=5000)
