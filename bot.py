import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import random

# ---------- Налаштування ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

MAIN_SHEET_ID = os.getenv("SPREADSHEET_ID")
sheet = client.open_by_key(MAIN_SHEET_ID)
users_ws = sheet.worksheet("Users")

bot = telebot.TeleBot(BOT_TOKEN)

# ---------- Мотиваційні повідомлення ----------
MOTIVATION_QUOTES = [
    "💪 Сьогодні — чудовий день, щоб зробити більше, ніж учора!",
    "🔥 Маленький крок щодня — великий результат у підсумку!",
    "🚀 Дій упевнено, і успіх прийде до тебе!",
    "🏆 Твоя дисципліна — це головний секрет перемоги!",
    "💡 Хто контролює свій день — контролює свій результат!"
]

def get_random_motivation():
    return random.choice(MOTIVATION_QUOTES)

# ---------- ФУНКЦІЇ ----------

def get_user_data(user_id):
    """Отримати дані користувача з таблиці Users"""
    users = users_ws.get_all_records()
    for user in users:
        if str(user_id) == str(user["Telegram_ID"]):
            return user
    return None

# ---------- ГОЛОВНЕ МЕНЮ ----------

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в списку користувачів. Звернись до керівника.")
        return

    name = user["Ім’я"]
    bot.send_message(message.chat.id, f"👋 Привіт, {name}!\n{get_random_motivation()}")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🗺 Територія", "⚙️ Сервіси", "🎯 Фокуси")
    bot.send_message(message.chat.id, "Вибери розділ 👇", reply_markup=markup)

# ---------- ПІДМЕНЮ ----------

@bot.message_handler(func=lambda message: message.text in ["🗺 Територія", "⚙️ Сервіси", "🎯 Фокуси"])
def show_submenu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if message.text == "🗺 Територія":
        markup.add("📋 План", "📍 Візити", "📊 Індекси", "✅ Задачі", "⬅️ Назад")
    elif message.text == "⚙️ Сервіси":
        markup.add("🛠 Сервіс-C", "⚙️ Сервіс-Х", "🎁 Промо", "💰 МФ", "⬅️ Назад")
    elif message.text == "🎯 Фокуси":
        markup.add("🎯 Фокуси", "🌱 Розвиток території", "⬅️ Назад")

    bot.send_message(message.chat.id, "Обери напрямок 👇", reply_markup=markup)

# ---------- ПОВЕРНЕННЯ НАЗАД ----------

@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def back_to_main(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🗺 Територія", "⚙️ Сервіси", "🎯 Фокуси")
    bot.send_message(message.chat.id, "🔙 Повернувся у головне меню.", reply_markup=markup)

# ---------- ОБРОБКА КНОПОК І ВИВІД ЛІНКІВ ----------

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
        if text in col_name.lower():
            matched_column = col_name
            break

    if matched_column:
        link = str(user[matched_column]).strip()
        if link.startswith("http"):
            motivation = get_random_motivation()
            bot.send_message(message.chat.id, f"{motivation}\n\n🔗 {matched_column}:\n{link}")
        else:
            bot.send_message(message.chat.id, f"⛔️ Для '{matched_column}' ще немає посилання.")
    else:
        pass  # щоб не дублювати обробку в підменю

# ---------- ЗАПУСК БОТА ----------

print("✅ Бот запущений...")
bot.polling(none_stop=True)
  
