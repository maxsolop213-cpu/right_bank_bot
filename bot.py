import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import json
from flask import Flask, request

# ---------- Налаштування ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_SHEET_ID = os.getenv("SPREADSHEET_ID")

# Авторизація Google Sheets через ENV
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(json.loads(os.getenv("GOOGLE_CREDENTIALS")), scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(MAIN_SHEET_ID)
users_ws = sheet.worksheet("Users")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---------- МОТИВАЦІЙНІ ФРАЗИ ----------
MOTIVATION = [
    "🚀 Крок за кроком до перемоги!",
    "🔥 Ти робиш відмінну роботу!",
    "💪 З кожним днем ближче до цілі!",
    "🌟 Пам’ятай — результат приходить до тих, хто не здається!"
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
    role = user["Роль"]

    bot.send_message(message.chat.id, f"👋 Привіт, {name}! Твоя роль: {role}")

    # Головне меню
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🌍 Територія", "🧰 Сервіси", "🎯 Фокуси")

    import random
    bot.send_message(message.chat.id, random.choice(MOTIVATION))
    bot.send_message(message.chat.id, "Вибери розділ 👇", reply_markup=markup)


# ---------- ПІДМЕНЮ: ТЕРИТОРІЯ ----------
@bot.message_handler(func=lambda message: message.text == "🌍 Територія")
def territory_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 План", "📊 Індекси", "🗓 Візити", "✅ Задачі", "⬅️ Назад")
    bot.send_message(message.chat.id, "📍 Обери напрям по території:", reply_markup=markup)


# ---------- ПІДМЕНЮ: СЕРВІСИ ----------
@bot.message_handler(func=lambda message: message.text == "🧰 Сервіси")
def services_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛠 Сервіс-C", "⚙️ Сервіс-Х", "🎁 Промо", "💰 МФ", "⬅️ Назад")
    bot.send_message(message.chat.id, "🧰 Обери потрібний сервіс:", reply_markup=markup)


# ---------- ПІДМЕНЮ: ФОКУСИ ----------
@bot.message_handler(func=lambda message: message.text == "🎯 Фокуси")
def focuses_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🌱 Розвиток територій", "⬅️ Назад")
    bot.send_message(message.chat.id, "🎯 Фокуси місяця та розвиток територій:", reply_markup=markup)


# ---------- ПОВЕРНЕННЯ НАЗАД ----------
@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def back_to_main(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🌍 Територія", "🧰 Сервіси", "🎯 Фокуси")
    bot.send_message(message.chat.id, "🏠 Повернувся в головне меню.", reply_markup=markup)


# ---------- ОБРОБКА КНОПОК І ВІДКРИТТЯ ЛІНКІВ ----------
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return

    column = message.text.strip()
    if column == "⬅️ Назад":
        back_to_main(message)
        return

    url = user.get(column)
    if not url:
        bot.send_message(message.chat.id, f"⛔️ Для '{column}' ще немає посилання.")
        return

clean_url = normalize_url(url)
    bot.send_message(message.chat.id, f"🔗 {column}:\n{clean_url}")


# ---------- ВЕБХУК ДЛЯ RENDER ----------
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200


@app.route('/')
def home():
    return "Bot is running", 200


# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    import requests
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=url)
    print(f"✅ Вебхук встановлено: {url}")
    app.run(host="0.0.0.0", port=5000)
