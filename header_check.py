import gspread
from google.oauth2.service_account import Credentials

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1U4SaGYLCwIBpDXBU0hvmCJmNxcUIBnwafwICR8edhRc")
ws = sheet.worksheet("Users")

header = ws.row_values(1)
for i, h in enumerate(header, start=1):
    print(f"{i}: {repr(h)}")

