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
creds_dict = json.loads(GOOGLE_CREDENTIALS)
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(MAIN_SHEET_ID)
users_ws = sheet.worksheet("Users")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---------- ГОЛОВНЕ МЕНЮ ----------
main_menu_buttons = ["📍 Територія", "🧰 Сервіси", "🎯 Фокуси"]

territory_buttons = ["🗺 Карта територій", "📋 План", "📊 Візити", "📈 Індекси", "⬅️ Назад"]
service_buttons = ["🛠 Сервіс-C", "⚙️ Сервіс-Х", "🎁 Промо", "💰 МФ", "⬅️ Назад"]
focus_buttons = ["🎯 Фокуси", "🌱 Розвиток територій", "⬅️ Назад"]

# ---------- ФУНКЦІЇ ----------
def get_user_data(user_id):
    users = users_ws.get_all_records()
    for user in users:
        if str(user_id) == str(user["Telegram_ID"]):
            return user
    return None


def send_menu(chat_id, buttons, text="Вибери розділ 👇"):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for b in buttons:
        markup.add(b)
    bot.send_message(chat_id, text, reply_markup=markup)


def send_link_or_warning(chat_id, user, key):
    link = str(user.get(key, "")).strip()
    if link.startswith("http"):
        bot.send_message(chat_id, f"🔗 {key}:\n{link}")
    else:
        bot.send_message(chat_id, f"⛔️ Для '{key}' ще немає посилання.")


# ---------- /start ----------
@bot.message_handler(commands=["start"])
def start(message):
    user = get_user_data(message.from_user.id)
    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в списку користувачів.")
        return

    name = user["Ім’я"]
    role = user["Роль"]
    bot.send_message(message.chat.id, f"👋 Привіт, {name}! Твоя роль: {role}")
    send_menu(message.chat.id, main_menu_buttons)


# ---------- ОБРОБКА КНОПОК ----------
@bot.message_handler(func=lambda m: True)
def handle(message):
    user = get_user_data(message.from_user.id)
    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return

    text = message.text.strip()

    # --- головне меню ---
    if text == "📍 Територія":
        send_menu(message.chat.id, territory_buttons, "📍 Вибери підрозділ:")
    elif text == "🧰 Сервіси":
        send_menu(message.chat.id, service_buttons, "🧰 Обери сервіс:")
    elif text == "🎯 Фокуси":
        send_menu(message.chat.id, focus_buttons, "🎯 Обери напрям:")

    # --- територія ---
    elif text in ["🗺 Карта територій", "📋 План", "📊 Візити", "📈 Індекси"]:
        send_link_or_warning(message.chat.id, user, text)

    # --- сервіси ---
    elif text in ["🛠 Сервіс-C", "⚙️ Сервіс-Х", "🎁 Промо", "💰 МФ"]:
        send_link_or_warning(message.chat.id, user, text)

    # --- фокуси ---
    elif text in ["🎯 Фокуси", "🌱 Розвиток територій"]:
        send_link_or_warning(message.chat.id, user, text)

    elif text == "⬅️ Назад":
        send_menu(message.chat.id, main_menu_buttons, "🏠 Головне меню")

    else:
        bot.send_message(message.chat.id, "❓ Невідома команда. Скористайся кнопками.")


# ---------- ВЕБХУК ----------
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200


@app.route('/')
def home():
    return "Bot is running ✅", 200


if __name__ == "__main__":
    import requests
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=url)
    print(f"✅ Вебхук встановлено: {url}")
    app.run(host="0.0.0.0", port=5000)
