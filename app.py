import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from datetime import date
from supabase import create_client, Client

# --- 1. CONFIG & DB ---
st.set_page_config(page_title="Global Finance AI", layout="wide")

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_connection()

def get_pinned_stocks():
    if not supabase: return []
    try:
        res = supabase.table("user_pins").select("ticker").execute()
        return sorted(list(set([i['ticker'] for i in res.data])))
    except: return []

# --- 2. SIDEBAR ---
st.sidebar.header("Navigation")
st.sidebar.info("💡 **Forex:** Use `=X` (e.g., `GBPUSD=X`)\n\n💡 **Crypto:** Use `-USD` (e.g., `BTC-USD`)")

pinned = get_pinned_stocks()
defaults = ["AAPL", "NVDA", "GBPUSD=X", "BTC-USD"]
options = sorted(list(set(defaults + pinned)))

selected_stock = st.sidebar.radio("Quick Select:", options)

# --- 3. MAIN INPUTS ---
st.title("📈 AI Finance Dashboard")
ticker = st.text_input("Ticker Symbol:", value=selected_stock).upper()
days = st.slider("Forecast Days:", 30, 365, 90)

if st.button(f"📌 Pin {ticker}"):
    try:
        supabase.table("user_pins").insert({"ticker": ticker}).execute()
        st.success("Pinned!")
        st.rerun()
    except: st.error("Database error.")

# --- 4. DATA ENGINE ---
@st.cache_data
def load_data(symbol):
    try:
        # Download data (1 year for speed and stability)
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True)
        if df.empty:
            return None
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

data = load_data(ticker)

if data is not None and not data.empty:
    # --- 5. VISUALS ---
    t1, t2 = st.tabs(["📊 Charts", "📋 Raw Data"])
    
    with t1:
        st.subheader("Historical