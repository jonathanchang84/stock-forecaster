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

# --- 2. SIDEBAR ---
st.sidebar.header("Navigation")
pinned = get_pinned_stocks()
defaults = ["AAPL", "NVDA", "GBPUSD=X", "BTC-USD"]
options = sorted(list(set(defaults + pinned)))
selected_stock = st.sidebar.radio("Quick Select:", options)

# --- 3. MAIN INPUTS ---
st.title("📈 AI Finance Dashboard")
ticker = st.text_input("Enter Ticker Symbol:", value=selected_stock).upper()
days = st.slider("Forecast Days:", 30, 365, 90)

if st.button(f"📌 Pin {ticker}"):
    try:
        supabase.table("user_pins").insert({"ticker": ticker}).execute()
        st.success(f"{ticker} pinned!")
        st.rerun()
    except:
        st.error("Database error.")

# --- 4. DATA ENGINE ---
@st.cache_data
def load_data(symbol):
    try:
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True)
        if df.empty: return None
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

data = load_data(ticker)

if data is not None and not data.empty:
    # --- 5. THE TOGGLE (TABS) ---
    st.subheader("Market Analysis")
    # This creates the toggle you liked
    tab1, tab2 = st.tabs(["📉 Historic Chart", "🤖 AI Forecast"])
    
    with tab1:
        st.line_chart(data.set_index('Date')['Close'])
    
    with tab2:
        df_train = data[['Date', 'Close']].copy().rename(columns={"Date":"ds", "Close":"y"})
        df_train['ds'] = df_train['ds'].dt.tz_localize(None)
        m = Prophet().fit(df_train)
        future = m.make_future_dataframe(periods=days)
        forecast = m.predict(future)
        st.plotly_chart(plot_plotly(m, forecast), use_container_width=True)

    # --- 6. THE TABLE (UNDERNEATH) ---
    st.divider()
    st.subheader("📋 Price History Table")
    # This ensures the table stays visible below the charts
    st.dataframe(data.sort_values(by='Date', ascending=False), use_container_width=True)

    # --- 7. NEWS FEED ---
    st.divider()
    st.subheader(f"Latest {ticker} Headlines")
    try:
        news = yf.Ticker(ticker).news
        if news:
            for art in news[:5]:
                c = art.get("content", art)
                col_img, col_txt = st.columns([1, 4])
                with col_img:
                    thumb = c.get("thumbnail", {}).get("resolutions", [])
                    if thumb: st.image(thumb[0].get("url"), use_container_width=True)
                    else: st.caption("No Image")
                with col_txt:
                    st.write(f"**{c.get('title', 'Headline')}**")
                    link = c.get("clickThroughUrl", {}).get("url") or art.get("link")
                    if link: st.markdown(f"[Read Article]({link})")
                st.write("---")
    except:
        st.info("News feed unavailable.")

else:
    st.warning("Invalid ticker. Try AAPL or GBPUSD=X.")