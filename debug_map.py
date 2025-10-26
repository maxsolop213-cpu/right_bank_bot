import gspread
from google.oauth2.service_account import Credentials

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1U4SaGYLCwIBpDXBU0hvmCJmNxcUIBnwafwICR8edhRc")
ws = sheet.worksheet("Users")

users = ws.get_all_records()
user = users[0]          # твій перший рядок
print("🧩 Колонки, які бачить Python:\n")
for k in user.keys():
    print(repr(k))

print("\n🔍 Що зберігається у полі '🗺 Карта територій':")
print(repr(user.get("🗺 Карта територій")))
