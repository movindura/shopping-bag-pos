from datetime import datetime
import json
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Shopping Bag POS Cloud", layout="wide", page_icon="🛒"
)


class GSheetsConnCompat:

  def __init__(self, spreadsheet):
    self.spreadsheet = spreadsheet

  def read(self, worksheet, ttl=0):
    try:
      ws = self.spreadsheet.worksheet(worksheet)
      data = ws.get_all_records()
      if not data:
        return pd.DataFrame()
      df = pd.DataFrame(data)
      return df.dropna(how="all")
    except Exception as e:
      st.error(f"Error loading worksheet {worksheet}: {e}")
      return pd.DataFrame()


@st.cache_resource
def get_connection():
  # st.secrets සිට ඩික්ෂනරියක් ලබා ගැනීම
  raw_secrets = st.secrets["connections"]["gsheets"]
  credentials_dict = {
      "type": raw_secrets["type"],
      "project_id": raw_secrets["project_id"],
      "private_key_id": raw_secrets["private_key_id"],
      # \n අකුරු සැබෑ newline බවට හැරවීම
      "private_key": raw_secrets["private_key"].replace("\\n", "\n"),
      "client_email": raw_secrets["client_email"],
      "client_id": raw_secrets["client_id"],
      "auth_uri": raw_secrets["auth_uri"],
      "token_uri": raw_secrets["token_uri"],
      "auth_provider_x509_cert_url": raw_secrets["auth_provider_x509_cert_url"],
      "client_x509_cert_url": raw_secrets["client_x509_cert_url"],
  }

  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  creds = Credentials.from_service_account_info(
      credentials_dict, scopes=scope
  )
  client = gspread.authorize(creds)
  spreadsheet_url = raw_secrets["spreadsheet"]
  spreadsheet = client.open_by_url(spreadsheet_url)
  return GSheetsConnCompat(spreadsheet)


# Google Sheets සම්බන්ධතාවය
conn = get_connection()

if "cart" not in st.session_state:
  st.session_state.cart = []


def load_data():
  sales = conn.read(worksheet="Sales", ttl=0)
  stock = conn.read(worksheet="Stock", ttl=0)
  expenses = conn.read(worksheet="Expenses", ttl=0)

  if "Item Code" not in stock.columns:
    stock.insert(0, "Item Code", "")
  if "විකුණුම් මිල" not in stock.columns:
    stock["විකුණුම් මිල"] = 0.0
  if "ප්‍රමාණය" not in stock.columns:
    stock["ප්‍රමාණය"] = 0.0

  return sales, stock, expenses


sales, stock, expenses = load_data()

st.title("🛒 Shopping Bag POS System")
st.success("ගූගල් ෂීට් සම්බන්ධතාවය සාර්ථකව ක්‍රියාත්මක වේ!")
