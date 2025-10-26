
import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import json

# ---------- Налаштування ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_SHEET_ID = os.getenv("SPREADSHEET_ID")

# Беремо ключ із Render (Environment Variables)
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Авторизація через JSON з середовища
creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDENTIALS), scopes=scope)
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


# ---------- КОМАНДА /start ----------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в списку користувачів. Звернись до керівника.")
        return

    role = user["Роль"]
    name = user["Ім’я"]
    bot.reply_to(message, f"👋 Привіт, {name}! Твоя роль: {role}")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "🗺 Карта територій", 
        "📋 Територія", 
        "🛠 Сервіси", 
        "🎯 Фокуси"
    ]
    for b in buttons:
        markup.add(b)

    bot.send_message(message.chat.id, "Вибери розділ 👇", reply_markup=markup)


# ---------- ОБРОБКА ПІДМЕНЮ ----------
@bot.message_handler(func=lambda m: m.text in ["📋 Територія", "🛠 Сервіси", "🎯 Фокуси"])
def submenu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    if message.text == "📋 Територія":
        markup.add("📋 План", "📋 Візити", "📋 Індекси", "⬅️ Назад")

    elif message.text == "🛠 Сервіси":
        markup.add("🛠 Сервіс-C", "⚙️ Сервіс-Х", "🎁 Промо", "💰 МФ", "⬅️ Назад")

    elif message.text == "🎯 Фокуси":
        markup.add("🎯 Фокуси", "🌱 Розвиток територій", "⬅️ Назад")

    bot.send_message(message.chat.id, "🔸 Вибери розділ:", reply_markup=markup)


# ---------- ПОВЕРНЕННЯ НАЗАД ----------
@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def go_back(message):
    start(message)


# ---------- ОБРОБКА ВСІХ ІНШИХ КНОПОК ----------
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return

    text = message.text.strip().lower()

    matched_column = None
    for col_name in user.keys():
        if text.replace("📋", "").replace("🎯", "").replace("✅", "").replace("🛠", "").replace("⚙️", "").strip() in col_name.lower():
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


# ---------- ЗАПУСК БОТА ----------
print("✅ Бот запущений...")
bot.polling(none_stop=True)
