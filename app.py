import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from datetime import date
from supabase import create_client, Client

# 1. DATABASE SETUP
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

# 2. UI LAYOUT
st.set_page_config(page_title="Stock AI", layout="wide")
st.sidebar.header("Navigation")

# Fetch pinned stocks
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
        st.success("Pinned!")
        st.rerun()
    except:
        st.error("Could not save to database.")

# 3. DATA & CHARTS
@st.cache_data
def load_data(symbol):
    try:
        df = yf.download(symbol, start="2015-01-01", end=date.today().strftime("%Y-%m-%d"), auto_adjust=True)
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

data = load_data(ticker)

if data is not None and not data.empty:
    t1, t2 = st.tabs(["Historical", "AI Forecast"])
    with t1:
        st.line_chart(data.set_index('Date')['Close'])
    with t2:
        df_t = data[['Date', 'Close']].copy().rename(columns={"Date":"ds", "Close":"y"})
        df_t['ds'] = df_t['ds'].dt.tz_localize(None)
        m = Prophet().fit(df_t)
        f = m.predict(m.make_future_dataframe(periods=days))
        st.plotly_chart(plot_plotly(m, f), use_container_width=True)

       # 4. NEWS (With Safe Images)
    st.divider()
    st.subheader(f"{ticker} Headlines")
    try:
        news = yf.Ticker(ticker).news
        for art in news[:5]:
            c = art.get("content", art)
            title = c.get('title', 'News Headline')
            link = c.get("clickThroughUrl", {}).get("url") or art.get("link")
            
            # Create two columns: one for image, one for text
            col1, col2 = st.columns([1, 4])
            
            # Safe Image Logic
            with col1:
                try:
                    thumb = c.get("thumbnail", {}).get("resolutions", [])
                    if thumb:
                        st.image(thumb[0].get("url"), use_container_width=True)
                    else:
                        st.caption("No Image")
                except:
                    st.caption("No Image")

            # Text Content
            with col2:
                st.write(f"**{title}**")
                if link: 
                    st.markdown(f"[Read Article]({link})")
            
            st.write("---")
    except:
        st.write("News feed currently unavailable.")