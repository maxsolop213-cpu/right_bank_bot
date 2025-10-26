import gspread
from google.oauth2.service_account import Credentials

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1U4SaGYLCwIBpDXBU0hvmCJmNxcUIBnwafwICR8edhRc")
ws = sheet.worksheet("Users")

users = ws.get_all_records()
print("🔍 Усі користувачі:")
for u in users:
    print(f"➡️ ID: {u.get('Telegram_ID')}, Ім’я: {u.get('Ім’я')}, Карта: {u.get('🗺 Карта територій')}")
