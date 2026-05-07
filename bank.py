import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- НАСТРОЙКИ ---
DB_FILE = "vault.csv"
STAFF_FILE = "staff.csv"

st.set_page_config(page_title="OPTIMUSUS PREMIUM", page_icon="🏦", layout="wide")

def load_db(file, cols):
    if os.path.exists(file):
        try: return pd.read_csv(file)
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

if 'df' not in st.session_state: st.session_state.df = load_db(DB_FILE, ['Имя', 'Сумма', 'Процент', 'Дата', 'Валюта'])
if 'staff' not in st.session_state: st.session_state.staff = load_db(STAFF_FILE, ['ФИО', 'Должность', 'Зарплата'])

def get_info(row):
    try:
        d1 = datetime.strptime(str(row['Дата']), "%d.%m.%Y")
        days = max(0, (datetime.now() - d1).days)
        current = float(row['Сумма']) * (1 + float(row['Процент'])/100)**days
        return round(current, 2), days
    except: return 0.0, 0

# --- СТИЛЬ ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a; }
    [data-testid="stSidebar"] { background-color: #0a0d12; border-right: 1px solid #1e293b; }
    .bank-card { background-color: #0f172a; border: 1px solid #1e293b; border-radius: 4px; padding: 20px; margin-bottom: 10px; }
    .debt-alert { background-color: #1a0a0a; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 10px; }
    h1, h2, h3 { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #0a0d12 !important; border: 1px solid #1e293b !important; border-radius: 4px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- МЕНЮ ---
st.sidebar.markdown("<h2 style='text-align:center; color:#3b82f6;'>OPTIMUSUS</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("ГЛАВНОЕ МЕНЮ", ["ОБЗОР", "РЕЕСТР", "СДЕЛКА", "ШТАТ", "КАССА", "ИНВЕСТ", "ЗАЩИТА", "НАЛОГИ", "АРХИВ", "СИСТЕМА"])

if menu == "ОБЗОР":
    st.title("Сводная отчетность")
    total_start = pd.to_numeric(st.session_state.df['Сумма']).sum()
    res = [get_info(row)[0] for i, row in st.session_state.df.iterrows()]
    total_now = sum(res)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("АКТИВЫ (СТАРТ)", f"${total_start:,.2f}")
    col2.metric("АКТИВЫ (ТЕКУЩИЕ)", f"${total_now:,.2f}", delta=f"${total_now - total_start:,.2f}")
    col3.metric("СДЕЛКИ", len(st.session_state.df))

elif menu == "РЕЕСТР":
    st.title("Реестр задолженностей")
    for i, row in st.session_state.df.iterrows():
        val, days = get_info(row)
        style = "debt-alert" if days > 7 else "bank-card"
        st.markdown(f"""<div class="{style}">
            <p style="color:#64748b; font-size:12px; margin:0;">ID-{i+1000}</p>
            <h3 style="margin:5px 0;">{row['Имя']}</h3>
            <p style="font-size:20px;">${val:,.2f} ({row['Валюта']}) | Дней: {days}</p>
        </div>""", unsafe_allow_html=True)
        if st.button(f"ЗАКРЫТЬ #{i}", key=f"del_{i}"):
            st.session_state.df = st.session_state.df.drop(i).reset_index(drop=True)
            st.session_state.df.to_csv(DB_FILE, index=False)
            st.rerun()

elif menu == "СДЕЛКА":
    st.title("Новый контракт")
    with st.form("contract"):
        n = st.text_input("Контрагент")
        a = st.number_input("Объем средств", min_value=0.0)
        p = st.number_input("Ставка (%/сутки)", min_value=0.0)
        d = st.text_input("Дата начала", datetime.now().strftime("%d.%m.%Y"))
        v = st.selectbox("Валюта", ["USD", "BTC", "RUB"])
        if st.form_submit_button("ЗАКЛЮЧИТЬ"):
            new = pd.DataFrame([[n, a, p, d, v]], columns=st.session_state.df.columns)
            st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True)
            st.session_state.df.to_csv(DB_FILE, index=False)
            st.success("Сохранено")

elif menu == "ШТАТ":
    st.title("Персонал")
    with st.expander("Добавить сотрудника"):
        fn = st.text_input("ФИО")
        ps = st.text_input("Должность")
        sl = st.number_input("Оклад ($)", min_value=0.0)
        if st.button("В ШТАТ"):
            new_s = pd.DataFrame([[fn, ps, sl]], columns=['ФИО', 'Должность', 'Зарплата'])
            st.session_state.staff = pd.concat([st.session_state.staff, new_s], ignore_index=True)
            st.session_state.staff.to_csv(STAFF_FILE, index=False)
            st.rerun()
    for i, row in st.session_state.staff.iterrows():
        col1, col2 = st.columns([4,1])
        col1.write(f"**{row['ФИО']}** | {row['Должность']} | ${row['Зарплата']:,.2f}")
        if col2.button("УВОЛИТЬ", key=f"st_{i}"):
            st.session_state.staff = st.session_state.staff.drop(i).reset_index(drop=True)
            st.session_state.staff.to_csv(STAFF_FILE, index=False)
            st.rerun()

elif menu == "КАССА":
    st.title("Расходы")
    st.metric("ФОНД ЗАРПЛАТ (МЕС)", f"${st.session_state.staff['Зарплата'].sum():,.2f}")
    st.table(st.session_state.staff)

else:
    st.title(menu)
    st.info("Раздел активен и находится под защитой.")
