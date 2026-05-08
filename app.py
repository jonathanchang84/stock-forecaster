import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from datetime import date
from supabase import create_client, Client

# --- 1. CONFIG & DB CONNECTION ---
st.set_page_config(page_title="Global Finance AI", layout="wide")

@st.cache_resource
def init_connection():
    try:
        # These must match the names in your Streamlit Cloud Secrets
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        return None

supabase = init_connection()

def get_pinned_stocks():
    if not supabase: return []
    try:
        res = supabase.table("user_pins").select("ticker").execute()
        return sorted(list(set([i['ticker'] for i in res.data])))
    except:
        return []

# --- 2. SIDEBAR NAVIGATION ---
st.sidebar.header("Navigation")
st.sidebar.info("""
**Ticker Guide:**
- 📈 **Stocks:** `AAPL`, `TSLA`
- 💱 **Forex:** `GBPUSD=X`
- ₿ **Crypto:** `BTC-USD`
""")

pinned = get_pinned_stocks()
defaults = ["AAPL", "NVDA", "GBPUSD=X", "BTC-USD"]
options = sorted(list(set(defaults + pinned)))

selected_stock = st.sidebar.radio("Quick Select:", options)

# --- 3. MAIN INTERFACE ---
st.title("📈 AI Finance Dashboard")
ticker = st.text_input("Enter Ticker Symbol:", value=selected_stock).upper()
days = st.slider("Forecast Days:", 30, 365, 90)

if st.button(f"📌 Pin {ticker} to Sidebar"):
    if supabase:
        try:
            supabase.table("user_pins").insert({"ticker": ticker}).execute()
            st.success(f"{ticker} added to database!")
            st.rerun()
        except:
            st.error("Error saving to database.")
    else:
        st.warning("Database connection not detected.")

# --- 4. DATA ENGINE ---
@st.cache_data
def load_data(symbol):
    try:
        # Download 1 year of data for stability
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust