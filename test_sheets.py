import gspread
from google.oauth2.service_account import Credentials

# Область доступу (дозволяє лише читання)
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Підключення ключа service_account.json
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

# Відкриваємо головну таблицю
sheet = client.open_by_key("1U4SaGYLCwIBpDXBU0hvmCJmNxcUIBnwafwICR8edhRc")
worksheet = sheet.worksheet("Users")

# Зчитуємо перший рядок
data = worksheet.row_values(1)
print("Перший рядок із таблиці Users:", data)
