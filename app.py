import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from datetime import date
from supabase import create_client, Client

# --- 1. CONFIG & DB ---
st.set_page_config(page_title="Stock AI Dashboard", layout="wide")

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

# --- 2. SIDEBAR & INPUTS ---
st.sidebar.header("Navigation")
pinned = get_pinned_stocks()
defaults = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
options = sorted(list(set(defaults + pinned)))

selected_stock = st.sidebar.radio("Quick Select:", options)

st.title("📈 AI Stock Dashboard")
ticker = st.text_input("Ticker Symbol:", value=selected_stock).upper()
days = st.slider("Forecast Days:", 30, 365, 90)

if st.button(f"📌 Pin {ticker}"):
    try:
        supabase.table("user_pins").insert({"ticker": ticker}).execute()
        st.success(f"{ticker} pinned to database!")
        st.rerun()
    except:
        st.error("Could not save to database.")

# --- 3. DATA ENGINE ---
@st.cache_data
def load_data(symbol):
    try:
        # We use '1y' period to ensure the table isn't 10 years long and slow
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True)
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"Error downloading data: {e}")
        return None

data = load_data(ticker)

if data is not None and not data.empty:
    # --- 4. VISUALIZATION ---
    
    # FIRST: Show the Table (Moved it up so it's impossible to miss)
    st.subheader(f"Recent Price Data for {ticker}")
    # Displaying the last 10 rows clearly
    latest_data = data.sort_values(by='Date', ascending=False).head(20)
    st.table(latest_data) # Using st.table instead of st.dataframe for a static, visible view

    # SECOND: Show Charts in Tabs
    st.divider()
    t1, t2 = st.tabs(["📈 Historical Chart", "🤖 AI Forecast"])
    
    with t1:
        st.line_chart(data.set_index('Date')['Close'])
    
    with t2:
        df_t = data[['Date', 'Close']].copy().rename(columns={"Date":"ds", "Close":"y"})
        df_t['ds'] = df_t['ds'].dt.tz_localize(None)
        m = Prophet().fit(df_t)
        future = m.make_future_dataframe(periods=days)
        forecast = m.predict(future)
        st.plotly_chart(plot_plotly(m, forecast), use_container_width=True)
    # --- 5. NEWS FEED ---
    st.divider()
    st.subheader(f"Latest {ticker} Headlines")
    try:
        news = yf.Ticker(ticker).news
        for art in news[:5]:
            c = art.get("content", art)
            col_img, col_txt = st.columns([1, 4])
            
            with col_img:
                thumb = c.get("thumbnail", {}).get("resolutions", [])
                if thumb:
                    st.image(thumb[0].get("url"), use_container_width=True)
                else:
                    st.caption("No Image")
            
            with col_txt:
                st.write(f"**{c.get('title', 'News Headline')}**")
                link = c.get("clickThroughUrl", {}).get("url") or art.get("link")
                if link: st.markdown(f"[Read Full Article]({link})")
            st.write("---")
    except:
        st.info("News feed currently unavailable.")

else:
    st.warning("Please enter a valid ticker symbol to load data.")