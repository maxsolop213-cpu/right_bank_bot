Максим Солоп, [26.10.2025 22:36]
import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from flask import Flask, request
import os
import json

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
app = Flask(name)

# ---------- ФУНКЦІЇ ----------

def get_user_data(user_id):
    """Отримати дані користувача з таблиці Users"""
    users = users_ws.get_all_records()
    for user in users:
        if str(user_id) == str(user["Telegram_ID"]):
            return user
    return None

def normalize(text):
    return (
        text.lower()
        .replace("🗺", "")
        .replace("📋", "")
        .replace("🎯", "")
        .replace("✅", "")
        .replace("🎁", "")
        .replace("💰", "")
        .replace("🛠", "")
        .replace("⚙️", "")
        .replace("🌱", "")
        .strip()
    )

# ---------- /start ----------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в списку користувачів. Звернись до керівника.")
        return

    role = user.get("Роль", "")
    name = user.get("Ім’я", "")
    bot.reply_to(message, f"👋 Привіт, {name}! Твоя роль: {role}")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🗺 Карта територій", "📋 Територія")
    markup.add("🛠 Сервіси", "🎯 Фокуси")
    bot.send_message(message.chat.id, "Вибери розділ 👇", reply_markup=markup)

# ---------- ПІДМЕНЮ ----------
@bot.message_handler(func=lambda m: m.text in ["📋 Територія", "🛠 Сервіси", "🎯 Фокуси"])
def submenu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    if message.text == "📋 Територія":
        markup.add("📋 План", "📋 Візити", "📋 Індекси")
    elif message.text == "🛠 Сервіси":
        markup.add("🛠 Сервіс-C", "⚙️ Сервіс-Х", "🎁 Промо", "💰 МФ")
    elif message.text == "🎯 Фокуси":
        markup.add("🎯 Фокуси", "🌱 Розвиток територій")

    markup.add("⬅️ Назад")
    bot.send_message(message.chat.id, "🔸 Вибери розділ:", reply_markup=markup)

# ---------- ПОВЕРНЕННЯ НАЗАД ----------
@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def go_back(message):
    start(message)

# ---------- ОБРОБКА КНОПОК ----------
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return

    text = normalize(message.text)
    matched_column = None
    for col_name in user.keys():
        if text in col_name.lower():
            matched_column = col_name
            break

    if matched_column:
        link = str(user[matched_column]).strip()
        if link.startswith("http"):
            bot.send_message(message.chat.id, f"🔗 {matched_column}:\n{link}")
        elif link == "" or link.lower() == "none":
            bot.send_message(message.chat.id, f"⛔️ Для '{matched_column}' ще немає посилання.")
        else:
            bot.send_message(message.chat.id, f"⚠️ Для '{matched_column}' записано не посилання.")
    else:
        bot.send_message(message.chat.id, "❓ Невідома команда, скористайся кнопками.")

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

Максим Солоп, [26.10.2025 22:36]
if __name__ == "__main__":
    import requests
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=url)
    print(f"✅ Вебхук встановлено: {url}")
    app.run(host="0.0.0.0", port=5000)
