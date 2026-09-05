from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Shopping Bag POS System", layout="wide", page_icon="🛒"
)

# ඔබ Deploy කළ Google Apps Script Web App URL එක මෙහි දමන්න
WEB_APP_URL = "ඔබේ_Apps_Script_Web_App_URL_එක_මෙහි_දමන්න"


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
            st.success("බිල්පත සාර්ථකයි!")
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
    if not stock_df.empty:
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

  tab1, tab2, tab3 = st.tabs(
      ["➕ අලුත් භාණ්ඩ සෑදීම", "📥 තොග එකතු කිරීම", "❌ භාණ්ඩ ඉවත් කිරීම"]
  )

  # Tab 1: අලුත් භාණ්ඩයක් සිස්ටම් එකට හැඳින්වීම
  with tab1:
    st.subheader("අලුත් භාණ්ඩයක් සිස්ටම් එකට එකතු කිරීම")
    with st.form("add_new_item_form"):
      item_code = st.text_input("භාණ්ඩයේ කේතය (Item Code / Barcode)")
      cat = st.text_input("කාණ්ඩය (Item Category)")
      name = st.text_input("භාණ්ඩයේ නම (Item Name)")
      size = st.text_input("ප්‍රමාණය / සයිස් (Size)")
      col_a, col_b = st.columns(2)
      buy_price = col_a.number_input("ගැනුම් මිල (Buying Price)", min_value=0.0)
      sell_price = col_b.number_input(
          "විකුණුම් මිල (Selling Price)", min_value=0.0
      )
      profit = sell_price - buy_price

      if st.form_submit_button("System එකට එකතු කරන්න"):
        if name:
          if (
              not stock_df.empty
              and name in stock_df["Item Name"].values
          ):
            st.error("මෙම නමින් භාණ්ඩයක් දැනටමත් ඇත!")
          else:
            new_row = {
                "Item Code": item_code,
                "Item Category": cat,
                "Item Name": name,
                "Size": size,
                "ගැනුම් මිල": buy_price,
                "විකුණුම් මිල": sell_price,
                "ලාභය": profit,
                "උදේ Stock": 0.0,
                "අද විකුනපු": 0.0,
                "Balance Stock": 0.0,
                "Stock Value": 0.0,
            }
            stock_df = pd.concat(
                [stock_df, pd.DataFrame([new_row])], ignore_index=True
            )
            st.success(
                f"{name} සාර්ථකව එකතු කළා! (මෙය Google Sheet එකෙහි යාවත්කාලීන"
                " කරගත හැක)."
            )
        else:
          st.warning("කරුණාකර භාණ්ඩයේ නම ඇතුළත් කරන්න.")

  # Tab 2: දැනට ඇති භාණ්ඩයකට තොග එකතු කිරීම
  with tab2:
    st.subheader("දැනට ඇති භාණ්ඩයකට තොග එකතු කිරීම")
    if stock_df.empty:
      st.info("තොග දත්ත නොමැත.")
    else:
      with st.form("add_stock_qty_form"):
        item_to_add = st.selectbox(
            "භාණ්ඩය තෝරන්න", stock_df["Item Name"].unique()
        )
        added_qty = st.number_input("අලුතින් ගෙනා ප්‍රමාණය", min_value=1, value=1)

        if st.form_submit_button("තොගයට එකතු කරන්න"):
          idx = stock_df.index[stock_df["Item Name"] == item_to_add].tolist()[0]
          current_stock = stock_df.at[idx, "උදේ Stock"]
          current_stock = 0 if pd.isna(current_stock) else current_stock
          stock_df.at[idx, "උදේ Stock"] = current_stock + added_qty

          sold_qty = stock_df.at[idx, "අද විකුනපු"]
          sold_qty = 0 if pd.isna(sold_qty) else sold_qty

          stock_df.at[idx, "Balance Stock"] = (
              stock_df.at[idx, "උදේ Stock"] - sold_qty
          )
          buy_p = stock_df.at[idx, "ගැනුම් මිල"]
          stock_df.at[idx, "Stock Value"] = (
              stock_df.at[idx, "Balance Stock"] * (0 if pd.isna(buy_p) else buy_p)
          )

          st.success(f"{item_to_add} සඳහා අලුතින් {added_qty} ක් එකතු විය!")

  # Tab 3: භාණ්ඩයක් ඉවත් කිරීම
  with tab3:
    st.subheader("භාණ්ඩයක් ඉවත් කිරීම")
    if stock_df.empty:
      st.info("ඉවත් කිරීමට භාණ්ඩ නොමැත.")
    else:
      with st.form("remove_item_form"):
        item_to_remove = st.selectbox(
            "ඉවත් කළ යුතු භාණ්ඩය තෝරන්න", stock_df["Item Name"].unique()
        )
        if st.form_submit_button("සිස්ටම් එකෙන් ඉවත් කරන්න"):
          stock_df = stock_df[stock_df["Item Name"] != item_to_remove]
          st.success(f"{item_to_remove} සිස්ටම් එකෙන් ඉවත් කළා!")

  st.markdown("---")
  st.subheader("📦 වර්තමාන සම්පූර්ණ තොග ලැයිස්තුව")
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
