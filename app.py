from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="At groceries POS System", layout="wide", page_icon="🛒"
)

# ඔබ Deploy කළ Google Apps Script Web App URL එක මෙහි දමන්න
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx4cqkJ_GlfGLHXpiZVx6AiOkQUU0h0TpDjZ7YaezN_DrK6DVgjDJBfQFCuhi6lI6iIyw/exec"


# Google Sheets වලින් දත්ත ලබා ගැනීම
@st.cache_data(ttl=2)
def load_data():
  try:
    response = requests.get(WEB_APP_URL + "?action=getData")
    data = response.json()

    sales = pd.DataFrame(data.get("Sales", []))
    stock = pd.DataFrame(data.get("Stock", []))
    expenses = pd.DataFrame(data.get("Expenses", []))

    # අලුත් Columns නැත්නම් හදාගැනීම
    if "Item Code" not in stock.columns and not stock.empty:
      stock.insert(0, "Item Code", "")
    if "විකුණුම් මිල" not in stock.columns and not stock.empty:
      stock["විකුණුම් මිල"] = 0.0
    if "ලාභය" not in stock.columns and not stock.empty:
      stock["ලාභය"] = 0.0

    if not stock.empty:
      stock["Item Code"] = stock["Item Code"].fillna("")

    return sales, stock, expenses
  except Exception as e:
    st.error(f"Error loading data from Google Sheets: {e}")
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


sales_df, stock_df, exp_df = load_data()

# Cart එක Session එකේ තියාගැනීම
if "cart" not in st.session_state:
  st.session_state.cart = []

st.title("🛒 Shopping Bag POS System")

# Sidebar
st.sidebar.header("මෙනුව (Menu)")
menu = st.sidebar.radio(
    "මෙතනින් තෝරන්න:",
    [
        "POS (බිල්පත් නිකුත් කිරීම)",
        "Dashboard (වාර්තා)",
        "Stock (තොග කළමනාකරණය)",
        "Expenses (වියදම්)",
    ],
)

# ---------------- 1. POS SYSTEM ----------------
if menu == "POS (බිල්පත් නිකුත් කිරීම)":
  st.header("🖥️ POS පද්ධතිය - නව බිල්පත")

  if stock_df.empty:
    st.warning("⚠️ තොග දත්ත (Stock) හමු නොවීය. කරුණාකර Google Sheet එක පරීක්ෂා කරන්න.")
  else:
    col1, col2 = st.columns([1, 1.2])

    with col1:
      st.subheader("භාණ්ඩය තෝරන්න")
      selected_item = st.selectbox(
          "භාණ්ඩයේ නම", stock_df["Item Name"].unique()
      )

      unit_price = 0.0
      available_qty = 0.0
      if selected_item:
        item_row = stock_df[stock_df["Item Name"] == selected_item]
        if not item_row.empty:
          unit_price = float(item_row["විකුණුම් මිල"].values[0])
          available_qty = float(item_row["Balance Stock"].values[0])

      st.info(
          f"💡 තොගයේ ඇති ප්‍රමාණය: **{available_qty}** | විකුණුම් මිල: **Rs."
          f" {unit_price}**"
      )

      qty = st.number_input("ප්‍රමාණය (Qty)", min_value=1, value=1)
      custom_price = st.number_input(
          "විකුණන මුළු මුදල (Rs.)", value=float(unit_price * qty)
      )

      if st.button("➕ Bill එකට එක් කරන්න (Add to Bill)"):
        if qty > available_qty:
          st.warning("⚠️ අවවාදයි: ගබඩාවේ අවශ්‍ය තරම් තොග නොමැත!")
        else:
          st.session_state.cart.append({
              "Item": selected_item,
              "Qty": qty,
              "Unit Price": unit_price,
              "Total": custom_price,
          })
          st.rerun()

    with col2:
      st.subheader("🧾 වර්තමාන බිල්පත (Current Bill)")

      if len(st.session_state.cart) > 0:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(cart_df, use_container_width=True)

        grand_total = cart_df["Total"].sum()
        st.markdown(f"### මුළු එකතුව: Rs. {grand_total:,.2f}")

        col_a, col_b = st.columns(2)
        with col_a:
          if st.button(
              "✅ මුදල් ගෙවා බිල අවසන් කරන්න", use_container_width=True
          ):
            st.session_state.cart = []
            st.success(
                "බිල්පත සාර්ථකයි! (Google Sheets වෙත දත්ත යැවීම සඳහා Apps Script"
                " POST පහසුකම ක්‍රියාත්මක කළ හැක)."
            )
        with col_b:
          if st.button("🗑️ බිල මකා දමන්න", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
      else:
        st.write("බිල්පතට තවම කිසිවක් ඇතුලත් කර නැත.")

# ---------------- 2. DASHBOARD ----------------
elif menu == "Dashboard (වාර්තා)":
  st.header("📊 ව්‍යාපාරික වාර්තා (Business Dashboard)")
  tab_daily, tab_monthly = st.tabs(
      ["📅 දෛනික වාර්තාව (Daily)", "📆 මාසික වාර්තාව (Monthly Summary)"]
  )

  with tab_daily:
    selected_date = st.date_input("දවස තෝරන්න", datetime.today())
    st.write("දෛනික වාර්තා දත්ත පෙන්වීම සඳහා සූදානම් කර ඇත.")
    display_stock = stock_df[
        [
            "Item Code",
            "Item Category",
            "Item Name",
            "ගැනුම් මිල",
            "විකුණුම් මිල",
            "ලාභය",
            "Balance Stock",
            "Stock Value",
        ]
    ]
    st.dataframe(display_stock, use_container_width=True)

  with tab_monthly:
    st.subheader("මාසික ආදායම් සහ වියදම් සාරාංශය")
    st.write("මාසික වාර්තා මෙහි පෙන්වනු ලැබේ.")

# ---------------- 3. STOCK MANAGEMENT ----------------
elif menu == "Stock (තොග කළමනාකරණය)":
  st.header("📦 තොග කළමනාකරණය (Stock Management)")
  st.dataframe(stock_df, use_container_width=True)

# ---------------- 4. EXPENSES ----------------
elif menu == "Expenses (වියදම්)":
  st.header("💸 වියදම් ඇතුලත් කරන්න")
  with st.form("expense_form"):
    date = st.date_input("දිනය")
    category = st.text_input("වියදම් වර්ගය (උදා: Transport)")
    desc = st.text_input("විස්තරය (උදා: Petrol)")
    amount = st.number_input("මුදල (Rs.)", min_value=0.0)

    if st.form_submit_button("වියදම Save කරන්න"):
      st.success(f"රු. {amount} ක වියදමක් සාර්ථකව ලබාදී ඇත!")
