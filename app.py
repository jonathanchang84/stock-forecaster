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
        # Standardize Forex input: if user types "GBPUSD", convert to "GBPUSD=X"
        if len(symbol) == 6 and symbol.isalpha():
            # Check if it's likely a currency pair (e.g., EURUSD)
            search_symbol = f"{symbol}=X"
        else:
            search_symbol = symbol

        df = yf.download(search_symbol, period="1y", interval="1d", auto_adjust=True)
        
        if df.empty and "=X" not in search_symbol:
            # Try one more time as a currency if first try failed
            df = yf.download(f"{symbol}=X", period="1y", interval="1d", auto_adjust=True)
            
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        return None
     # --- 4. VISUALIZATION ---
    
    # 1. Charts first in Tabs
    st.subheader("Market Analysis")
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

    # 2. Table moved to here (Under the charts)
    st.divider()
    st.subheader(f"Raw Data Records: {ticker}")
    
    # We show the most recent 50 rows, nicely formatted
    latest_data = data.sort_values(by='Date', ascending=False).head(50)
    st.dataframe(latest_data, use_container_width=True, hide_index=True)
       # --- 5. NEWS FEED ---
    st.divider()
    st.subheader(f"Latest {ticker} Headlines")
    
    try:
        # Fetch news with a fresh object
        news_fetcher = yf.Ticker(ticker)
        news = news_fetcher.news
        
        if not news:
            st.info("No recent news found for this ticker.")
        else:
            for art in news[:5]:
                # Deep-dive into the dictionary to find content
                # Some versions of yfinance put everything in 'content', others don't
                c = art.get("content", art)
                
                col_img, col_txt = st.columns([1, 4])
                
                with col_img:
                    # Very specific check for the thumbnail URL
                    thumb_data = c.get("thumbnail", {})
                    if isinstance(thumb_data, dict):
                        resolutions = thumb_data.get("resolutions", [])
                        if resolutions:
                            st.image(resolutions[0].get("url"), use_container_width=True)
                        else:
                            st.caption("No Image")
                    else:
                        st.caption("No Image")
                
                with col_txt:
                    title = c.get('title', art.get('title', 'News Headline'))
                    st.write(f"**{title}**")
                    
                    # Try multiple places for the link
                    link = c.get("clickThroughUrl", {}).get("url") or \
                           c.get("canonicalUrl", {}).get("url") or \
                           art.get("link")
                           
                    if link: 
                        st.markdown(f"[Read Full Article]({link})")
                st.write("---")
                
    except Exception as e:
        # This will show you the ACTUAL error for 5 seconds to help us debug
        st.warning(f"Note: News feed is stuttering (Error: {e})")
        st.info("The rest of your dashboard is working fine!")