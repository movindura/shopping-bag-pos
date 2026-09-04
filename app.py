from datetime import datetime
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
  credentials_dict = {
      "type": "service_account",
      "project_id": "pos-system-507617",
      "private_key_id": "0be7756d85b7f384ad090a648ee8713951ed0b5a",
      "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDBmHo/SzKv9i51
0wI0s2Szf43EMZXNxH886zFSAjzjPEZVDTmHFjq57rtnsOwQSNgvo9XxiXna8Z05
Igtv0nI/7a9SOJJxM1+W3PmUKyjhWNJEGSFD87l4pDxpxu/HurUCk25kCl0Gwplb
LC+gm2OotTlBqoMU2lbwmsCfzNLB3NYhmbi+MXJ2Rkat3Q3yM+wtabA0iRlsf/i5
xIMJJOrSxVjKOPb24tkCHhunfJZD9t8bszdtRtNfyYh0kRxVPcDdbpE1fV19ZD16
zwMXVllzVYm8aYL8O1ZXdsDW4z/l9g9iWrYdaUgYG7Qr4jeTANj5hVgC4BJdI5DR
1j6D3KpxAgMBAAECggEAGOKY+jhYFmLSg45BZxVVQTaI+lp2W2oiAepon1ZOzdXi
Y43s4may21Iq8E//dDNs6KjKeD8X9RMgRucPqcrXKU0L/4lql5cHN00F3uwyV88z
ThId4s56PZ387wrlqRqgqGlbpAvp+9O5Y00ZfS9kPtw2tTBuI5jSWqDF2HS7dbRM
a10io2bYHxJPwuow+K85d8YC5hleG3cyzrbDrl3CEsuEEfBIkrkf2ysrasBgXa9D
nzE4O6KjdLXHME4ufC/CBc8qtTGh6lpNj7OEyZJKxu0qs0J5wmKIV1boKMRLJUJOR
MwW4NRlOOGRVQpRCx8+04Yd2N153z8vpMV3ktMunPQKBgQDiZSllxcCRQwHkk27F
u10q1nK3SZ24zQKAIUukGXIq6RpczbhkmNm+3fYeq/0gfLNpwICSKpWEHUJsEsI3
HDnTyv5GZTWicHAjFXZ7dNH8JQNoZjlVz4ZBPPxcC9Kv1YaqmgHpz5R6RM7Wj411
Y8ztECR8Mkg7/Fru+kxcgBgjHQKBgQDa6VAyInYLhr8LMWX3edETV9D1b1BaHgqK
jNyQOeqTOZRJyi7yrvBXOIISfBH1kz/rL3VAJNXTiA6uRjWe7L0b6hYgfr1RpYT6
5ctMe6ucCSbkTNQR8cF9T6lmSVJjNwonW3HWuaYtrBUTT0uzDmvxxPpOKgVQX0Ht
nlZfQUqkQZQKBgFQLK+ANFlyWnHhHRwL+eCqz62ghWvzEll4MfjEQBTLq0A+NixtF
JuhVK83dGR3bTRtADDq2tkSSPBs0p4af4tO98sEdR1jjFq3fhNl115IcB3TVJgm1
/WfwhNqCxRbjVJe2jmlG1x7AtmwuZFwkzWlf6bt1Sx2BpBw9LOXV45/9AoGAOxKc
nrnq4KhIZeZbB8k8wCS04WRLJtxfGNm8ekdjfIQ13o5Xop1pnxtGb4AsU+ZTbucZb
nuIx4GxXrCEIv9AvkWCUKBYjN47trsBzUiHYS8A9ULGVDEPiRAxS9HLoKfnV6yvYV
OSFt44M9SLGsNsxceqhx9yfFuVOLQeaNSg0UTDUCgYEAyabMCRKwOabk97FdgwMt
LN2ln0hAPSklZ/AO8IRKx7wAFTPnz1PKFSEoD7MkpUZPvyaRWL/T7KyLukLr6s6X
nj5ZqWG22qiZPpqqCJvIGao8Vu3C1cdDMonPB1/S5/USCip8oFwur2ZYgWKbXUhqR
1Y8YSiwNVv59PyfD0mXpRpc=
-----END PRIVATE KEY-----""",
      "client_email": "pos-admin@pos-system-507617.iam.gserviceaccount.com",
      "client_id": "113174180402475269837",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": (
          "https://www.googleapis.com/robot/v1/metadata/x509/pos-admin%40pos-system-507617.iam.gserviceaccount.com"
      ),
  }

  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  creds = Credentials.from_service_account_info(
      credentials_dict, scopes=scope
  )
  client = gspread.authorize(creds)
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
