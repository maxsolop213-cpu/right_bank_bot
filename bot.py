import telebot
import gspread
from google.oauth2 import service_account
from dotenv import load_dotenv
import os
import json

# ---------- Налаштування ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN_SHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS")

# Авторизація через JSON із Render environment
creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
creds = service_account.Credentials.from_service_account_info(
    creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
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
    """Заміна /edit на /viewer"""
    if not url:
        return None
    return url.replace("/edit", "/viewer")


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
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return

    column = message.text.strip()
    url = user.get(column)

    if not url:
        bot.reply_to(message, f"⚠️ Для '{column}' поки немає посилання.")
        return

    clean_url = normalize_url(url)
    bot.reply_to(message, f"🔗 {column}:\n{clean_url}")


# ---------- ЗАПУСК ----------
if name == "main":
    print("✅ Бот запущений")
    bot.polling(none_stop=True)
