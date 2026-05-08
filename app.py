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
        # Pulling from Streamlit Cloud Secrets
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
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
        # Download 1 year of data
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True)
        if df.empty:
            return None
        df.reset_index(inplace=True)
        # Handle potential MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

data = load_data(ticker)

if data is not None and not data.empty:
    # --- 5. VISUALIZATION TABS ---
    t1, t2 = st.tabs(["📊 Market Charts", "📋 Raw Data Records"])
    
    with t1:
        st.subheader("Historical Price Analysis")
        st.line_chart(data.set_index('Date')['Close'])
        
        st.subheader("AI Trend Forecast")
        df_train = data[['Date', 'Close']].copy().rename(columns={"Date":"ds", "Close":"y"})
        df_train['ds'] = df_train['ds'].dt.tz_localize(None)
        
        m = Prophet()
        m.fit(df_train)
        
        future = m.make_future_dataframe(periods=days)
        forecast = m.predict(future)
        
        fig = plot_plotly(m, forecast)
        st.plotly_chart(fig, use_container_width=True)
        
    with t2:
        st.subheader("Recent Price History")
        st.dataframe(data.sort_values(by='Date', ascending=False), use_container_width=True)

    # --- 6. NEWS FEED ---
    st.divider()
    st.subheader(f"Latest {ticker} Headlines")
    try:
        news_items = yf.Ticker(ticker).news
        if news_items:
            for art in news_items[:5]:
                c = art.get("content", art)
                col_img, col_txt = st.columns([1, 4])
                
                with col_img:
                    thumb = c.get("thumbnail", {}).get("resolutions", [])
                    if thumb:
                        st.image(thumb[0].get("url"), use_container_width=True)
                    else:
                        st.caption("No Image")
                
                with col_txt:
                    title = c.get('title', art.get('title', 'Headline'))
                    st.write(f"**{title}**")
                    link = c.get("clickThroughUrl", {}).get("url") or \
                           c.get("canonicalUrl", {}).get("url") or \
                           art.get("link")
                    if link:
                        st.markdown(f"[Read Article]({link})")
                st.write("---")
        else:
            st.info("No news found for this ticker.")
    except:
        st.info("News feed is currently unavailable.")

else:
    st.warning("Invalid ticker. Please try a different symbol (e.g., AAPL, GBPUSD=X).")