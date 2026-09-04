from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Shopping Bag POS Cloud", layout="wide", page_icon="🛒"
)

# ඉහත Deploy කළ Google Apps Script Web App URL එක මෙහි දමන්න
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx4cqkJ_GlfGLHXpiZVx6AiOkQUU0h0TpDjZ7YaezN_DrK6DVgjDJBfQFCuhi6lI6iIyw/exec"


@st.cache_data(ttl=5)
def load_data_from_script():
  try:
    response = requests.get(WEB_APP_URL + "?action=getData")
    data = response.json()

    sales = pd.DataFrame(data.get("Sales", []))
    stock = pd.DataFrame(data.get("Stock", []))
    expenses = pd.DataFrame(data.get("Expenses", []))

    return sales, stock, expenses
  except Exception as e:
    st.error(f"Error connecting to Google Sheet: {e}")
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


if "cart" not in st.session_state:
  st.session_state.cart = []

sales, stock, expenses = load_data_from_script()

if "Item Code" not in stock.columns and not stock.empty:
  stock.insert(0, "Item Code", "")
if "විකුණුම් මිල" not in stock.columns:
  stock["විකුණුම් මිල"] = 0.0
if "ප්‍රමාණය" not in stock.columns:
  stock["ප්‍රමාණය"] = 0.0

st.title("🛒 Shopping Bag POS System")
st.success("ගූගල් ෂීට් සම්බන්ධතාවය සාර්ථකව ක්‍රියාත්මක වේ!")
