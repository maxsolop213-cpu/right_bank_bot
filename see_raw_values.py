import gspread
from google.oauth2.service_account import Credentials

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1U4SaGYLCwIBpDXBU0hvmCJmNxcUIBnwafwICR8edhRc")
ws = sheet.worksheet("Users")

data = ws.get_all_values()
print("🔍 Рядки як бачить Python (сирі значення):\n")
for i, row in enumerate(data[:5]):  # перші 5 рядків
    print(i+1, row)
