import gspread
from google.oauth2.service_account import Credentials

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1U4SaGYLCwIBpDXBU0hvmCJmNxcUIBnwafwICR8edhRc")
users_ws = sheet.worksheet("Users")

first_row = users_ws.row_values(1)
print("🔹 Заголовки колонок у твоїй таблиці:")
for col in first_row:
    print(f"- {repr(col)}")


