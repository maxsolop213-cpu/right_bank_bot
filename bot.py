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
    users = users_ws.get_all_records()
    for user in users:
        if str(user_id) == str(user["Telegram_ID"]):
            return user
    return None


def normalize_url(url):
    if not url:
        return None
    return url.replace("/edit", "/viewer")

# ---------- СТАН МЕНЮ ----------
user_states = {}

# ---------- ГОЛОВНЕ МЕНЮ ----------
def main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🗺 Карта територій")
    markup.row("📋 Територія", "⚙️ Сервіси")
    markup.row("🎯 Фокуси")
    bot.send_message(chat_id, "📍 Обери розділ:", reply_markup=markup)
    user_states[chat_id] = "main"


# ---------- ПІДМЕНЮ ----------
def territory_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 План", "📋 Візити", "📈 Індекси")
    markup.row("⬅️ Назад")
    bot.send_message(chat_id, "📋 Територія:", reply_markup=markup)
    user_states[chat_id] = "territory"


def services_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛠 Сервіс-C", "⚙️ Сервіс-Х")
    markup.row("🎁 Промо", "💰 МФ")
    markup.row("⬅️ Назад")
    bot.send_message(chat_id, "⚙️ Сервіси:", reply_markup=markup)
    user_states[chat_id] = "services"


def focus_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎯 Фокуси", "🌱 Розвиток територій")
    markup.row("⬅️ Назад")
    bot.send_message(chat_id, "🎯 Фокуси:", reply_markup=markup)
    user_states[chat_id] = "focus"


# ---------- КОМАНДА /start ----------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в списку користувачів. Звернись до керівника.")
        return

    name = user["Ім’я"]
    role = user["Роль"]

    bot.reply_to(message, f"👋 Привіт, {name}! Твоя роль: {role}")
    main_menu(message.chat.id)


# ---------- ОБРОБКА КНОПОК ----------
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return

    text = message.text.strip()

    # --- Навігація ---
    if text == "⬅️ Назад":
        main_menu(chat_id)
        return

    # --- Перехід у підменю ---
    if text == "📋 Територія":
        territory_menu(chat_id)
        return
    if text == "⚙️ Сервіси":
        services_menu(chat_id)
        return
    if text == "🎯 Фокуси":
        focus_menu(chat_id)
        return

    # --- Головне меню: проста кнопка ---
    if text == "🗺 Карта територій":
        link = user.get("🗺 Карта територій")
        if not link:
            bot.send_message(chat_id, "⛔️ Для 'Карта територій' ще немає посилання.")
        else:
            bot.send_message(chat_id, f"🗺 Карта територій:\n{normalize_url(link)}")
        return

    # --- Усі інші кнопки (підменю) ---
    link = user.get(text)
    if link:
        bot.send_message(chat_id, f"🔗 {text}:\n{normalize_url(link)}")
    else:
        bot.send_message(chat_id, f"⛔️ Для '{text}' ще немає посилання.")


# ---------- ЗАПУСК БОТА ----------
print("✅ Бот запущений...")
bot.polling(none_stop=True)
