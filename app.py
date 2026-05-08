import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from datetime import date

# 1. Page Setup
st.set_page_config(page_title="Stock AI Dashboard", layout="wide")

# 2. Sidebar - Only ONE radio menu here
st.sidebar.header("Navigation")
top_stocks = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
selected_stock = st.sidebar.radio("Select a Top Performer:", top_stocks, key="nav_radio")

# 3. Main Inputs
st.title("📈 AI Stock Prediction Dashboard")
ticker = st.text_input("Or type any ticker (e.g., BTC-USD):", value=selected_stock)
days_to_predict = st.slider("Forecast Days:", 30, 365, 90)

# 4. Data Engine (The Flattening Fix)
@st.cache_data
def load_data(symbol):
    try:
        # auto_adjust=True keeps the headers simple
        df = yf.download(symbol, start="2015-01-01", end=date.today().strftime("%Y-%m-%d"), auto_adjust=True)
        df.reset_index(inplace=True)
        
        # This removes the multi-layer headers that caused the '2 sections' and 'missing chart' issues
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

data = load_data(ticker)

if data is not None and not data.empty:
    # 5. SECTION 1: Historical Chart
    st.subheader(f"Historical Price: {ticker}")
    st.line_chart(data.set_index('Date')['Close'])

    # 6. SECTION 2: AI Forecast
    st.subheader("AI Future Trend")
    
    # Prepare data for Prophet
    df_train = data[['Date', 'Close']].copy()
    df_train.columns = ['ds', 'y']
    df_train['ds'] = df_train['ds'].dt.tz_localize(None) # Remove timezone for Prophet
    
    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=days_to_predict)
    forecast = m.predict(future)
    
    fig = plot_plotly(m, forecast)
    st.plotly_chart(fig, use_container_width=True)

    # 7. SECTION 3: History Table
    st.subheader("Recent Price Records")
    # Sort by date so the newest is at the top
    table_data = data.sort_values(by='Date', ascending=False)
    st.dataframe(table_data.head(20), use_container_width=True)

else:
    st.info("Waiting for valid ticker symbol...")
    

# --- 8. NEWS SECTION ---
st.header(f"Latest News for {ticker}")

news_data = yf.Ticker(ticker).news

if news_data:
    for article in news_data:
        # 1. Safely grab the content block
        content = article.get("content")
        if not isinstance(content, dict):
            content = article
            
        # 2. Get Title and Publisher
        title = content.get("title", "No Title")
        provider_data = content.get("provider", {})
        publisher = "Finance News"
        if isinstance(provider_data, dict):
            publisher = provider_data.get("displayName", "Finance News")
        
        # 3. SAFELY GET LINK (This fixes the AttributeError)
        link = None
        ct_url = content.get("clickThroughUrl")
        if isinstance(ct_url, dict):
            link = ct_url.get("url")
        
        # Fallback to standard link if ct_url failed
        if not link:
            link = article.get("link")
        
        with st.container():
            col1, col2 = st.columns([1, 4])
            
            # 4. ULTRA-SAFE THUMBNAIL CHECK
            thumb = content.get("thumbnail")
            if isinstance(thumb, dict):
                resolutions = thumb.get("resolutions", [])
                if isinstance(resolutions, list) and len(resolutions) > 0:
                    res = resolutions[0]
                    if isinstance(res, dict):
                        col1.image(res.get("url"))
            
            with col2:
                st.subheader(title)
                st.write(f"Source: {publisher}")
                if link:
                    st.markdown(f"[Read full article]({link})")
            st.divider()
else:
    st.write("No recent news found for this ticker.")
    from supabase import create_client, Client

import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from datetime import date
from supabase import create_client, Client

# --- 1. SETTINGS & CONNECTIONS ---
st.set_page_config(page_title="Stock AI Dashboard", layout="wide")

# Connect to Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 2. DATABASE FUNCTIONS ---
def get_pinned_stocks():
    try:
        response = supabase.table("user_pins").select("ticker").execute()
        # Returns a unique list of tickers from the DB
        return sorted(list(set([item['ticker'] for item in response.data])))
    except Exception:
        return []

def add_pin(ticker_symbol):
    supabase.table("user_pins").insert({"ticker": ticker_symbol}).execute()

# --- 3. SIDEBAR ---
st.sidebar.header("Navigation")
default_stocks = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
pinned = get_pinned_stocks()

# Combine default stocks with pinned stocks for the menu
all_options = sorted(list(set(default_stocks + pinned)))

selected_stock = st.sidebar.radio("Select Stock:", all_options, key="main_nav")

if st.sidebar.button("Clear All Pins (Database)"):
    # Safety: In a real app, you'd only delete user-specific pins
    supabase.table("user_pins").delete().neq("ticker", "empty").execute()
    st.rerun()

# --- 4. MAIN INTERFACE ---
st.title("📈 AI Stock Prediction Dashboard")
ticker = st.text_input("Ticker Symbol:", value=selected_stock).upper()

col1, col2 = st.columns([1, 1])
with col1:
    days_to_predict = st.slider("Forecast Days:", 30, 365, 90)
with col2:
    if st.button(f"📌 Pin {ticker} to Sidebar"):
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
    # Historical Chart
    st.subheader("Historical Price")
    st.line_chart(data.set_index('Date')['Close'])

    # AI Forecast
    st.subheader("AI Future Trend")
    df_train = data[['Date', 'Close']].copy().rename(columns={"Date": "ds", "Close": "y"})
    df_train['ds'] = df_train['ds'].dt.tz_localize(None)
    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=days_to_predict)
    forecast = m.predict(future)
    st.plotly_chart(plot_plotly(m, forecast), use_container_width=True)

    # News (Ultra-Safe Version)
    st.subheader(f"Latest {ticker} News")
    news_data = yf.Ticker(ticker).news
    if news_data:
        for article in news_data[:5]: # Show top 5
            content = article.get("content", article)
            title = content.get("title", "No Title")
            st.write(f"**{title}**")
            st.divider()
else:
    st.warning("Enter a valid ticker to begin.")