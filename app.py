import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# Page Config
st.set_page_config(page_title="Shopping Bag POS System", layout="wide", page_icon="🛒")

# ඔයාගේ අලුත් Web App URL එක මෙතන දාන්න
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzi_3ZDoAG-dPPZ9zEvJf4omNvobMht5vsDXaSsEKLOcF5S_7x3DBB88Kn1OlLFr7fHgQ/exec"

# Cart එක Session එකේ තියාගැනීම
if 'cart' not in st.session_state:
    st.session_state.cart = []

# Google Sheets වලින් Data Load කිරීම
def load_data():
    try:
        response = requests.get(WEB_APP_URL + "?action=getData")
        data = response.json()
        
        sales = pd.DataFrame(data.get("Sales", []))
        stock = pd.DataFrame(data.get("Stock", []))
        expenses = pd.DataFrame(data.get("Expenses", []))
        
        if 'Item Code' not in stock.columns and not stock.empty:
            stock.insert(0, 'Item Code', '')
        if 'විකුණුම් මිල' not in stock.columns:
            stock['විකුණුම් මිල'] = 0.0
        if 'ලාභය' not in stock.columns:
            stock['ලාභය'] = 0.0
            
        if not stock.empty:
            stock['Item Code'] = stock['Item Code'].fillna('')
        return sales, stock, expenses
    except Exception as e:
        st.error("Google Sheets වලින් දත්ත ලබාගැනීමට නොහැකි විය!")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Google Sheets වලට Data Save කිරීම (POST Request)
def save_data(sales, stock, exp):
    def df_to_list(df):
        if df.empty:
            return [df.columns.values.tolist()]
        return [df.columns.values.tolist()] + df.fillna("").values.tolist()

    payload = {
        "action": "saveData",
        "sales": df_to_list(sales),
        "stock": df_to_list(stock),
        "expenses": df_to_list(exp)
    }
    
    try:
        payload_json = json.dumps(payload, default=str)
        res = requests.post(WEB_APP_URL, data=payload_json, headers={'Content-Type': 'application/json'})
        if res.status_code == 200 and res.json().get('status') == 'success':
            return True
        else:
            st.error("Google Sheets වෙත දත්ත යැවීම අසාර්ථකයි!")
            return False
    except Exception as e:
        st.error("Save කිරීමේදී දෝෂයක් මතු විය.")
        return False

# ඩේටා ලෝඩ් කිරීම
sales_df, stock_df, exp_df = load_data()

st.title("🛒 Shopping Bag POS System")

# Sidebar
st.sidebar.header("මෙනුව (Menu)")
menu = st.sidebar.radio("මෙතනින් තෝරන්න:", [
    "POS (බිල්පත් නිකුත් කිරීම)", 
    "Dashboard (වාර්තා)", 
    "Stock (තොග කළමනාකරණය)", 
    "Expenses (වියදම්)"
])

# ---------------- 1. POS SYSTEM ----------------
if menu == "POS (බිල්පත් නිකුත් කිරීම)":
    st.header("🖥️ POS පද්ධතිය - නව බිල්පත")
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("භාණ්ඩය තෝරන්න")
        if not stock_df.empty:
            selected_item = st.selectbox("භාණ්ඩයේ නම", stock_df['Item Name'].unique())
            
            unit_price = 0.0
            available_qty = 0.0
            if selected_item:
                unit_price = float(stock_df.loc[stock_df['Item Name'] == selected_item, 'විකුණුම් මිල'].values[0])
                available_qty = float(stock_df.loc[stock_df['Item Name'] == selected_item, 'Balance Stock'].values[0])
                
            st.info(f"💡 තොගයේ ඇති ප්‍රමාණය: **{available_qty}** | විකුණුම් මිල: **Rs. {unit_price}**")
            
            qty = st.number_input("ප්‍රමාණය (Qty)", min_value=1, value=1)
            custom_price = st.number_input("විකුණන මුළු මුදල (Rs.)", value=float(unit_price * qty))
            
            if st.button("➕ Bill එකට එක් කරන්න (Add to Bill)"):
                if qty > available_qty:
                    st.warning("⚠️ අවවාදයි: ගබඩාවේ අවශ්‍ය තරම් තොග නොමැත!")
                else:
                    st.session_state.cart.append({"Item": selected_item, "Qty": qty, "Unit Price": unit_price, "Total": custom_price})
                    st.rerun()
        else:
            st.warning("තොග දත්ත නොමැත.")

    with col2:
        st.subheader("🧾 වර්තමාන බිල්පත (Current Bill)")
        if len(st.session_state.cart) > 0:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.dataframe(cart_df, use_container_width=True)
            
            grand_total = cart_df['Total'].sum()
            st.markdown(f"### මුළු එකතුව: Rs. {grand_total:,.2f}")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ මුදල් ගෙවා බිල අවසන් කරන්න", use_container_width=True):
                    now = datetime.now()
                    
                    for item in st.session_state.cart:
                        i_name = item['Item']
                        i_qty = item['Qty']
                        i_total = item['Total']
                        
                        new_sale = pd.DataFrame([{'Date': now.date(), 'Item Name': i_name, 'QTY Sold': i_qty, 'Sold Price': i_total}])
                        sales_df = pd.concat([sales_df, new_sale], ignore_index=True)
                        
                        idx = stock_df.index[stock_df['Item Name'] == i_name].tolist()[0]
                        current_sold = stock_df.at[idx, 'අද විකුනපු']
                        stock_df.at[idx, 'අද විකුනපු'] = (0 if pd.isna(current_sold) else current_sold) + i_qty
                        
                        morning_stock = stock_df.at[idx, 'උදේ Stock']
                        morning_stock = 0 if pd.isna(morning_stock) else morning_stock
                        buy_price = stock_df.at[idx, 'ගැනුම් මිල']
                        
                        stock_df.at[idx, 'Balance Stock'] = morning_stock - stock_df.at[idx, 'අද විකුනපු']
                        stock_df.at[idx, 'Stock Value'] = stock_df.at[idx, 'Balance Stock'] * buy_price
                    
                    if save_data(sales_df, stock_df, exp_df):
                        st.session_state.cart = []
                        st.success("බිල්පත සාර්ථකයි! Google Sheet එකට දත්ත සේව් විය.")
                    st.rerun()
                    
            with col_b:
                if st.button("🗑️ බිල මකා දමන්න", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()
        else:
            st.write("බිල්පතට තවම කිසිවක් ඇතුලත් කර නැත.")

# ---------------- 2. DASHBOARD (Daily & Monthly) ----------------
elif menu == "Dashboard (වාර්තා)":
    st.header("📊 ව්‍යාපාරික වාර්තා (Business Dashboard)")
    tab_daily, tab_monthly = st.tabs(["📅 දෛනික වාර්තාව (Daily)", "📆 මාසික වාර්තාව (Monthly Summary)"])
    
    with tab_daily:
        selected_date = st.date_input("දවස තෝරන්න", datetime.today())
        sel_date_str = pd.to_datetime(selected_date).normalize()
        
        if not sales_df.empty:
            sales_df['Date'] = pd.to_datetime(sales_df['Date']).dt.normalize()
            daily_sales = sales_df[sales_df['Date'] == sel_date_str]
        else:
            daily_sales = pd.DataFrame()
            
        if not exp_df.empty:
            exp_df['දිනය'] = pd.to_datetime(exp_df['දිනය']).dt.normalize()
            daily_exp = exp_df[exp_df['දිනය'] == sel_date_str]
        else:
            daily_exp = pd.DataFrame()
        
        total_sales_revenue = daily_sales['Sold Price'].sum() if not daily_sales.empty else 0
        total_expenses = daily_exp['ගාන රු.'].sum() if not daily_exp.empty else 0
        
        total_cogs = 0 
        if not daily_sales.empty and not stock_df.empty:
            for index, row in daily_sales.iterrows():
                item = row['Item Name']
                qty = row['QTY Sold']
                if item in stock_df['Item Name'].values:
                    buy_price = stock_df.loc[stock_df['Item Name'] == item, 'ගැනුම් මිල'].values[0]
                    total_cogs += (buy_price * qty)
                
        net_profit = total_sales_revenue - total_cogs - total_expenses
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 අද මුළු විකුණුම්", f"Rs. {total_sales_revenue:,.2f}")
        col2.metric("💸 අද මුළු වියදම්", f"Rs. {total_expenses:,.2f}")
        col3.metric("📉 විකුණූ භාණ්ඩ පිරිවැය", f"Rs. {total_cogs:,.2f}")
        col4.metric("🏆 අද ශුද්ධ ලාභය", f"Rs. {net_profit:,.2f}")
        
        st.markdown("---")
        st.subheader("📦 දැනට ඉතිරිව ඇති සම්පූර්ණ තොගය")
        if not stock_df.empty:
            total_stock_value = stock_df['Stock Value'].sum()
            st.write(f"**ගබඩාවේ ඇති භාණ්ඩ වල සම්පූර්ණ වටිනාකම:** Rs. {total_stock_value:,.2f}")
            display_stock = stock_df[['Item Code', 'Item Category', 'Item Name', 'ගැනුම් මිල', 'විකුණුම් මිල', 'ලාභය', 'Balance Stock', 'Stock Value']]
            st.dataframe(display_stock, use_container_width=True)

    with tab_monthly:
        st.subheader("මාසික ආදායම් සහ වියදම් සාරාංශය")
        if not sales_df.empty or not exp_df.empty:
            if not sales_df.empty:
                sales_df['MonthStr'] = pd.to_datetime(sales_df['Date']).dt.strftime('%Y-%m')
            if not exp_df.empty:
                exp_df['MonthStr'] = pd.to_datetime(exp_df['දිනය']).dt.strftime('%Y-%m')
            
            s_months = sales_df['MonthStr'].dropna().tolist() if not sales_df.empty else []
            e_months = exp_df['MonthStr'].dropna().tolist() if not exp_df.empty else []
            available_months = list(set(s_months + e_months))
            available_months.sort(reverse=True)
            
            if not available_months:
                st.info("තවමත් විකුණුම් හෝ වියදම් දත්ත නොමැත.")
            else:
                selected_month = st.selectbox("මාසය තෝරන්න (අවුරුද්ද-මාසය)", available_months)
                
                m_sales = sales_df[sales_df['MonthStr'] == selected_month] if not sales_df.empty else pd.DataFrame()
                m_exp = exp_df[exp_df['MonthStr'] == selected_month] if not exp_df.empty else pd.DataFrame()
                
                m_sales_total = m_sales['Sold Price'].sum() if not m_sales.empty else 0
                m_exp_total = m_exp['ගාන රු.'].sum() if not m_exp.empty else 0
                
                m_cogs_total = 0
                if not m_sales.empty and not stock_df.empty:
                    for _, row in m_sales.iterrows():
                        item = row['Item Name']
                        qty = row['QTY Sold']
                        if item in stock_df['Item Name'].values:
                            buy_price = stock_df.loc[stock_df['Item Name'] == item, 'ගැනුම් මිල'].values[0]
                            m_cogs_total += (buy_price * qty)
                        
                m_net_profit = m_sales_total - m_cogs_total - m_exp_total
                
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("මාසයේ මුළු විකුණුම්", f"Rs. {m_sales_total:,.2f}")
                mc2.metric("මාසයේ මුළු වියදම්", f"Rs. {m_exp_total:,.2f}")
                mc3.metric("මාසයේ භාණ්ඩ පිරිවැය", f"Rs. {m_cogs_total:,.2f}")
                mc4.metric("මාසික ශුද්ධ ලාභය", f"Rs. {m_net_profit:,.2f}")

# ---------------- 3. STOCK MANAGEMENT ----------------
elif menu == "Stock (තොග කළමනාකරණය)":
    st.header("📦 තොග කළමනාකරණය (Stock Management)")
    tab1, tab2, tab3 = st.tabs(["➕ අලුත් භාණ්ඩ සෑදීම", "📥 තොග එකතු කිරීම", "❌ භාණ්ඩ ඉවත් කිරීම"])
    
    with tab1:
        st.subheader("අලුත් භාණ්ඩයක් සිස්ටම් එකට හඳුන්වා දීම")
        with st.form("add_new_item_form"):
            item_code = st.text_input("භාණ්ඩයේ කේතය (Item Code / Barcode)")
            cat = st.text_input("කාණ්ඩය (Item Category)")
            name = st.text_input("භාණ්ඩයේ නම (Item Name)")
            size = st.text_input("ප්‍රමාණය (Size)")
            col_a, col_b = st.columns(2)
            buy_price = col_a.number_input("ගැනුම් මිල (Buying Price)", min_value=0.0)
            sell_price = col_b.number_input("විකුණුම් මිල (Selling Price)", min_value=0.0)
            profit = sell_price - buy_price
            
            if st.form_submit_button("System එකට එකතු කරන්න"):
                if name:
                    if not stock_df.empty and name in stock_df['Item Name'].values:
                        st.error("මෙම නමින් භාණ්ඩයක් දැනටමත් ඇත!")
                    else:
                        new_row = {
                            'Item Code': item_code, 'Item Category': cat, 'Item Name': name, 'Size': size, 
                            'ගැනුම් මිල': buy_price, 'විකුණුම් මිල': sell_price, 'ලාභය': profit,
                            'උදේ Stock': 0.0, 'අද විකුනපු': 0.0, 'Balance Stock': 0.0, 'Stock Value': 0.0
                        }
                        stock_df = pd.concat([stock_df, pd.DataFrame([new_row])], ignore_index=True)
                        if save_data(sales_df, stock_df, exp_df):
                            st.success(f"{name} සාර්ථකව Google Sheet එකට එකතු කළා!")

    with tab2:
        st.subheader("දැනට ඇති භාණ්ඩයකට තොග එකතු කිරීම")
        if not stock_df.empty:
            with st.form("add_stock_qty_form"):
                item_to_add = st.selectbox("භාණ්ඩය තෝරන්න", stock_df['Item Name'].unique())
                added_qty = st.number_input("අලුතින් ගෙනා ප්‍රමාණය", min_value=1)
                
                if st.form_submit_button("තොගයට එකතු කරන්න"):
                    idx = stock_df.index[stock_df['Item Name'] == item_to_add].tolist()[0]
                    current_stock = stock_df.at[idx, 'උදේ Stock']
                    stock_df.at[idx, 'උදේ Stock'] = (0 if pd.isna(current_stock) else current_stock) + added_qty
                    
                    sold_qty = stock_df.at[idx, 'අද විකුනපු']
                    sold_qty = 0 if pd.isna(sold_qty) else sold_qty
                    
                    stock_df.at[idx, 'Balance Stock'] = stock_df.at[idx, 'උදේ Stock'] - sold_qty
                    stock_df.at[idx, 'Stock Value'] = stock_df.at[idx, 'Balance Stock'] * stock_df.at[idx, 'ගැනුම් මිල']
                    
                    if save_data(sales_df, stock_df, exp_df):
                        st.success(f"{item_to_add} සඳහා අලුතින් {added_qty} ක් එකතු විය!")

    with tab3:
        st.subheader("භාණ්ඩයක් ඉවත් කිරීම")
        if not stock_df.empty:
            with st.form("remove_item_form"):
                item_to_remove = st.selectbox("ඉවත් කළ යුතු භාණ්ඩය තෝරන්න", stock_df['Item Name'].unique())
                if st.form_submit_button("ඉවත් කරන්න"):
                    stock_df = stock_df[stock_df['Item Name'] != item_to_remove]
                    if save_data(sales_df, stock_df, exp_df):
                        st.success(f"{item_to_remove} සිස්ටම් එකෙන් ඉවත් කළා!")

# ---------------- 4. ADD EXPENSES ----------------
elif menu == "Expenses (වියදම්)":
    st.header("💸 වියදම් ඇතුලත් කරන්න")
    with st.form("expense_form"):
        date = st.date_input("දිනය")
        category = st.text_input("වියදම් වර්ගය (උදා: Transport)")
        desc = st.text_input("විස්තරය (උදා: Petrol)")
        amount = st.number_input("මුදල (Rs.)", min_value=0.0)
        
        if st.form_submit_button("වියදම Save කරන්න"):
            new_exp = pd.DataFrame([{'දිනය': pd.to_datetime(date), 'Item Category': category, 'විස්තර': desc, 'ගාන රු.': amount}])
            exp_df = pd.concat([exp_df, new_exp], ignore_index=True)
            if save_data(sales_df, stock_df, exp_df):
                st.success(f"රු. {amount} ක වියදමක් සාර්ථකව Google Sheet එකට ඇතුලත් කළා!")
