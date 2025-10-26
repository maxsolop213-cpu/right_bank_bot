import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os

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
        "🗺 Карта територій", "📋 План", "🎯 Фокуси",
        "✅ Задачі", "🎁 Промо", "💰 МФ",
        "🛠 Сервіс-C", "⚙️ Сервіс-Х", "🌱 Розвиток територій"
    ]
    for b in buttons:
        markup.add(b)

    bot.send_message(message.chat.id, "Вибери розділ 👇", reply_markup=markup)

# ---------- ОБРОБКА КНОПОК ----------

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return

    text = message.text.strip().lower()

    # нормалізація emoji і назв
    def normalize(s):
        return (
            s.lower()
            .replace("🗺", "🗺")
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

    matched_column = None
    for col_name in user.keys():
        if normalize(text) in normalize(col_name):
            matched_column = col_name
            break

    if matched_column:
        link = str(user[matched_column]).strip()
        if link.startswith("http://") or link.startswith("https://"):
            # автоматично виправляємо Google Maps MyMaps URL
            if "google.com/maps/d/" in link:
                if "edit" in link:
                    link = link.replace("edit?", "viewer?")
                elif "viewer" not in link:
                    link = link.replace("d/", "d/viewer?")

            bot.send_message(message.chat.id, f"🔗 {matched_column}:\n{link}")

        elif link == "" or link.lower() == "none":
            bot.send_message(message.chat.id, f"⛔️ Для '{matched_column}' ще немає посилання.")
        else:
            bot.send_message(message.chat.id, f"⚠️ Для '{matched_column}' записано текст, але це не посилання.")
    else:
        bot.send_message(message.chat.id, "❓ Невідома команда, скористайся кнопками.")

# ---------- ЗАПУСК БОТА ----------

print("✅ Бот запущений...")
bot.polling(none_stop=True)
