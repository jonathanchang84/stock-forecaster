import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from datetime import date
from supabase import create_client, Client

# --- 1. SETTINGS & CONNECTIONS ---
st.set_page_config(page_title="Stock AI Dashboard", layout="wide")

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Secrets not found. Check Streamlit Cloud Settings.")
        return None

supabase = init_connection()

# --- 2. DATABASE FUNCTIONS ---
def get_pinned_stocks():
    if not supabase: return []
    try:
        response = supabase.table("user_pins").select("ticker").execute()
        return sorted(list(set([item['ticker'] for item in response.data])))
    except Exception:
        return []

def add_pin(ticker_symbol):
    if supabase:
        supabase.table("user_pins").insert({"ticker": ticker_symbol}).execute()

# --- 3. SIDEBAR ---
st.sidebar.header("Navigation")
default_stocks = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
pinned = get_pinned_stocks()
all_options = sorted(list(set(default_stocks + pinned)))

selected_stock = st.sidebar.radio("Select Stock:", all_options, key="nav_radio_v3")

if st.sidebar.button("Clear All Database Pins", key="clear_db_btn"):
    if supabase:
        supabase.table("user_pins").delete().neq("ticker", "empty").execute()
        st.rerun()

# --- 4. MAIN INTERFACE ---
st.title("📈 AI Stock Prediction Dashboard")
ticker = st.text_input("Ticker Symbol:", value=selected_stock, key="ticker_input_v3").upper()

col1, col2 = st.columns([1, 1])
with col1:
    # Adding a unique key here prevents the duplicate ID error you saw
    days_to_predict = st.slider("Forecast Days:", 30, 365, 90, key="forecast_slider_v3")
with col2:
    if st.button(f"📌 Pin {ticker} to Sidebar", key="pin_btn_v3"):
        add_pin(ticker)
        st.success(f"{ticker} added to database!")
        st.rerun()

# --- 5. DATA ENGINE ---
@st.cache_data
def load_data(symbol):
    try:
        df = yf.download(symbol, start="2015-01-01", end=date.today().strftime("%Y-%m-%d"), auto_adjust=True)
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception: return None

data = load_data(ticker)

if data is not None and not data.empty:
    st.subheader("Historical Price")
    st.line_chart(data.set_index('Date')['Close'])

    st.subheader("AI Future Trend")
    df_train = data[['Date', 'Close']].copy().rename(columns={"Date": "ds", "Close": "y"})
    df_train['ds'] = df_train['ds'].dt.tz_localize(None)
    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=days_to_predict)
    forecast = m.predict(future)
    st.plotly_chart(plot_plotly(m, forecast), use_container_width=True)

    st.subheader(f"Latest {ticker} News")
    news_data = yf.Ticker(ticker).news
    if news_data:
        for article in news_data[:5]:
            content = article.get("content", article)
            title = content.get("title", "No Title")
            st.write(f"**{title}**")
            st.divider()
else:
    st.warning("Enter a valid ticker to begin.")