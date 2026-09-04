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
  # සජීවීව service_account.json ෆයිල් එක හරහා ලෝඩ් කරගැනීම
  with open("service_account.json") as f:
    credentials_dict = json.load(f)

  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  creds = Credentials.from_service_account_info(
      credentials_dict, scopes=scope
  )
  client = gspread.authorize(creds)

  # ගූගල් ෂීට් ලින්ක් එක මෙතැනට දාන්න
  spreadsheet_url = "https://docs.google.com/spreadsheets/d/1rpA2L5VnGw226st1suhP3E5rHTSsX3T4huTWAGJdydI/edit"
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
