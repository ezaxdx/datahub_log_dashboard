import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import toml

secrets = toml.load(".streamlit/secrets.toml")
creds_dict = secrets["gcp_service_account"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1N0UUF2Qroqbukd37WRgur2FpjzxEXLevT79EB_GutEk/edit?usp=sharing")

print("login:", sh.worksheet("login").row_values(1))
print("download:", sh.worksheet("download").row_values(1))
print("제안서_ezPDF:", sh.worksheet("제안서_ezPDF").row_values(1))
