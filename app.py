import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Shopping Bag POS Cloud", layout="wide", page_icon="🛒")

# Google Sheets සම්බන්ධතාවය
conn = st.connection("gsheets", type=GSheetsConnection)

if 'cart' not in st.session_state:
    st.session_state.cart = []

def load_data():
    sales = conn.read(worksheet="Sales", ttl=0).dropna(how='all')
    stock = conn.read(worksheet="Stock", ttl=0).dropna(how='all')
    expenses = conn.read(worksheet="Expenses", ttl=0).dropna(how='all')
    
    if 'Item Code' not in stock.columns:
        stock.insert(0, 'Item Code', '')
    if 'විකුණුම් මිල' not in stock.columns:
        stock['විකුණුම් මිල'] = 0.0
    if 'ලාභය' not in stock.columns:
        stock['ලාභය'] = 0.0
        
    stock['Item Code'] = stock['Item Code'].fillna('')
    return sales, stock, expenses

def save_data(sales, stock, exp):
    conn.update(worksheet="Sales", data=sales)
    conn.update(worksheet="Stock", data=stock)
    conn.update(worksheet="Expenses", data=exp)

try:
    sales_df, stock_df, exp_df = load_data()
except Exception as e:
    st.error("Google Sheet එකට සම්බන්ධ වීමේ දෝෂයක්. Settings වල URL එක නිවැරදිදැයි බලන්න.")
    st.stop()

st.title("🛒 Shopping Bag POS System (Cloud)")
menu = st.sidebar.radio("මෙනුව (Menu):", ["POS (බිල්පත්)", "Dashboard (වාර්තා)", "Stock (තොග)", "Expenses (වියදම්)"])

if menu == "POS (බිල්පත්)":
    st.header("🖥️ POS පද්ධතිය - නව බිල්පත")
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("භාණ්ඩය තෝරන්න")
        selected_item = st.selectbox("භාණ්ඩයේ නම", stock_df['Item Name'].unique())
        
        unit_price = 0.0
        available_qty = 0.0
        if selected_item:
            unit_price = float(stock_df.loc[stock_df['Item Name'] == selected_item, 'විකුණුම් මිල'].values[0])
            available_qty = float(stock_df.loc[stock_df['Item Name'] == selected_item, 'Balance Stock'].values[0])
            
        st.info(f"💡 තොගය: **{available_qty}** | විකුණුම් මිල: **Rs. {unit_price}**")
        qty = st.number_input("ප්‍රමාණය (Qty)", min_value=1, value=1)
        custom_price = st.number_input("මුළු මුදල (Rs.)", value=float(unit_price * qty))
        
        if st.button("➕ Add to Bill"):
            if qty > available_qty:
                st.warning("⚠️ අවශ්‍ය තරම් තොග නොමැත!")
            else:
                st.session_state.cart.append({"Item": selected_item, "Qty": qty, "Unit Price": unit_price, "Total": custom_price})
                st.rerun()

    with col2:
        st.subheader("🧾 වර්තමාන බිල්පත")
        if len(st.session_state.cart) > 0:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.dataframe(cart_df, use_container_width=True)
            grand_total = cart_df['Total'].sum()
            st.markdown(f"### මුළු එකතුව: Rs. {grand_total:,.2f}")
            
            if st.button("✅ Checkout (මුදල් ගෙවන්න)", use_container_width=True):
                now = datetime.now()
                for item in st.session_state.cart:
                    i_name, i_qty, i_total = item['Item'], item['Qty'], item['Total']
                    
                    new_sale = pd.DataFrame([{'Date': now.strftime('%Y-%m-%d'), 'Item Name': i_name, 'QTY Sold': i_qty, 'Sold Price': i_total}])
                    sales_df = pd.concat([sales_df, new_sale], ignore_index=True)
                    
                    idx = stock_df.index[stock_df['Item Name'] == i_name].tolist()[0]
                    current_sold = stock_df.at[idx, 'අද විකුනපු']
                    stock_df.at[idx, 'අද විකුනපු'] = (0 if pd.isna(current_sold) else current_sold) + i_qty
                    
                    morning_stock = 0 if pd.isna(stock_df.at[idx, 'උදේ Stock']) else stock_df.at[idx, 'උදේ Stock']
                    buy_price = stock_df.at[idx, 'ගැනුම් මිල']
                    
                    stock_df.at[idx, 'Balance Stock'] = morning_stock - stock_df.at[idx, 'අද විකුනපු']
                    stock_df.at[idx, 'Stock Value'] = stock_df.at[idx, 'Balance Stock'] * buy_price
                
                save_data(sales_df, stock_df, exp_df)
                st.session_state.cart = []
                st.success("බිල්පත සේව් විය! Google Sheet එක අප්ඩේට් කර ඇත.")
                st.rerun()
        else:
            st.write("බිල්පත හිස්ය.")

elif menu == "Dashboard (වාර්තා)":
    st.header("📊 ව්‍යාපාරික වාර්තා")
    sales_df['Date'] = pd.to_datetime(sales_df['Date'])
    exp_df['දිනය'] = pd.to_datetime(exp_df['දිනය'])
    
    total_sales = sales_df['Sold Price'].sum()
    total_exp = exp_df['ගාන රු.'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("සමස්ත විකුණුම්", f"Rs. {total_sales:,.2f}")
    col2.metric("සමස්ත වියදම්", f"Rs. {total_exp:,.2f}")
    col3.metric("ඉතිරි තොගයේ වටිනාකම", f"Rs. {stock_df['Stock Value'].sum():,.2f}")
    
    st.subheader("දැනට ඇති තොගය")
    st.dataframe(stock_df[['Item Code', 'Item Name', 'Balance Stock', 'විකුණුම් මිල']], use_container_width=True)

elif menu == "Stock (තොග)":
    st.header("📦 තොග කළමනාකරණය")
    tab1, tab2 = st.tabs(["➕ අලුත් භාණ්ඩ සෑදීම", "📥 තොග එකතු කිරීම"])
    
    with tab1:
        with st.form("add_new_item_form"):
            item_code = st.text_input("Item Code")
            cat = st.text_input("Category")
            name = st.text_input("Item Name")
            size = st.text_input("Size")
            col_a, col_b = st.columns(2)
            buy_price = col_a.number_input("ගැනුම් මිල", min_value=0.0)
            sell_price = col_b.number_input("විකුණුම් මිල", min_value=0.0)
            
            if st.form_submit_button("System එකට එකතු කරන්න"):
                if name:
                    new_row = {
                        'Item Code': item_code, 'Item Category': cat, 'Item Name': name, 'Size': size, 
                        'ගැනුම් මිල': buy_price, 'විකුණුම් මිල': sell_price, 'ලාභය': sell_price - buy_price,
                        'උදේ Stock': 0.0, 'අද විකුනපු': 0.0, 'Balance Stock': 0.0, 'Stock Value': 0.0
                    }
                    stock_df = pd.concat([stock_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(sales_df, stock_df, exp_df)
                    st.success(f"{name} එකතු කළා!")

    with tab2:
        with st.form("add_stock_qty_form"):
            item_to_add = st.selectbox("භාණ්ඩය තෝරන්න", stock_df['Item Name'].unique())
            added_qty = st.number_input("අලුතින් ගෙනා ප්‍රමාණය", min_value=1)
            
            if st.form_submit_button("තොගයට එකතු කරන්න"):
                idx = stock_df.index[stock_df['Item Name'] == item_to_add].tolist()[0]
                stock_df.at[idx, 'උදේ Stock'] = float(stock_df.at[idx, 'උදේ Stock']) + added_qty
                stock_df.at[idx, 'Balance Stock'] = float(stock_df.at[idx, 'උදේ Stock']) - float(stock_df.at[idx, 'අද විකුනපු'])
                stock_df.at[idx, 'Stock Value'] = stock_df.at[idx, 'Balance Stock'] * stock_df.at[idx, 'ගැනුම් මිල']
                
                save_data(sales_df, stock_df, exp_df)
                st.success("තොගය අප්ඩේට් විය!")

elif menu == "Expenses (වියදම්)":
    st.header("💸 වියදම් ඇතුලත් කරන්න")
    with st.form("expense_form"):
        date = st.date_input("දිනය")
        category = st.text_input("වියදම් වර්ගය")
        desc = st.text_input("විස්තරය")
        amount = st.number_input("මුදල (Rs.)", min_value=0.0)
        
        if st.form_submit_button("Save කරන්න"):
            new_exp = pd.DataFrame([{'දිනය': date.strftime('%Y-%m-%d'), 'Item Category': category, 'විස්තර': desc, 'ගාන රු.': amount}])
            exp_df = pd.concat([exp_df, new_exp], ignore_index=True)
            save_data(sales_df, stock_df, exp_df)
            st.success("වියදම ඇතුලත් කළා!")
