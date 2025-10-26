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

scope = ["https://www.googleapis.com/auth/spreadsheets"]

# Авторизація Google Sheets
creds_dict = json.loads(GOOGLE_CREDENTIALS)
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(MAIN_SHEET_ID)
users_ws = sheet.worksheet("Users")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

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

# ---------- КНОПКИ ----------

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

# ---------- FLASK ВЕБХУК ----------

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
