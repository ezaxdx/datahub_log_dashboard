import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import toml
import os

secrets = toml.load(".streamlit/secrets.toml")
creds_dict = secrets["gcp_service_account"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1N0UUF2Qroqbukd37WRgur2FpjzxEXLevT79EB_GutEk/edit?usp=sharing")

headers = {
    "login": sh.worksheet("login").row_values(1),
    "download": sh.worksheet("download").row_values(1),
    "제안서_ezPDF": sh.worksheet("제안서_ezPDF").row_values(1)
}
with open("headers.json", "w", encoding='utf-8') as f:
    json.dump(headers, f, ensure_ascii=False, indent=2)
