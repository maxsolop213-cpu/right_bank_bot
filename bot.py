import os
import telebot
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from flask import Flask, request
import json

# ---------- Налаштування ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDENTIALS), scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID)
users_ws = sheet.worksheet("Users")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ---------- Flask ----------
app = Flask(name)

@app.get("/")
def index():
    return "✅ Bot is alive"

@app.post(f"/{BOT_TOKEN}")
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "", 200

# ---------- Логіка ----------
def get_user_data(user_id):
    for user in users_ws.get_all_records():
        if str(user_id) == str(user.get("Telegram_ID", "")):
            return user
    return None

def normalize_url(url: str | None):
    if not url:
        return None
    return url.replace("/edit", "/viewer")

@bot.message_handler(commands=["start"])
def start(message):
    user = get_user_data(message.from_user.id)
    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в списку користувачів.")
        return
    name, role = user["Ім’я"], user["Роль"]
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for b in ["🗺 Карта територій","📋 План","🎯 Фокуси","✅ Задачі","🎁 Промо","💰 МФ","🛠 Сервіс-C","⚙️ Сервіс-Х","🌱 Розвиток територій"]:
        kb.add(b)
    bot.send_message(message.chat.id, f"👋 Привіт, {name}! Твоя роль: {role}", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in [
    "🗺 Карта територій","📋 План","🎯 Фокуси","✅ Задачі","🎁 Промо","💰 МФ","🛠 Сервіс-C","⚙️ Сервіс-Х","🌱 Розвиток територій"
])
def handle_buttons(message):
    user = get_user_data(message.from_user.id)
    if not user:
        bot.reply_to(message, "⚠️ Тебе немає в базі.")
        return
    url = normalize_url(user.get(message.text))
    if not url:
        bot.reply_to(message, f"⚠️ Для '{message.text}' немає посилання.")
        return
    bot.reply_to(message, f"🔗 {message.text}:\n{url}")

# ---------- Запуск (webhook) ----------
if __name__ == "_main_":
    bot.remove_webhook()
    public_url = os.getenv("RENDER_EXTERNAL_URL")  # Render задає автоматично
    webhook_url = f"{public_url}/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set: {webhook_url}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
