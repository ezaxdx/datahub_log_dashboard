import gspread, toml
from oauth2client.service_account import ServiceAccountCredentials
secrets = toml.load('.streamlit/secrets.toml')
creds = ServiceAccountCredentials.from_json_keyfile_dict(secrets['gcp_service_account'], ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
cl = gspread.authorize(creds)
headers = cl.open_by_url('https://docs.google.com/spreadsheets/d/1N0UUF2Qroqbukd37WRgur2FpjzxEXLevT79EB_GutEk/edit?usp=sharing').worksheet('제안서_ezPDF').get_all_values()[0]
with open('debug_headers.txt', 'w', encoding='utf-8') as f:
    f.write(repr(headers))
