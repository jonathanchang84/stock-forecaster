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

    # --- NEWS SECTION (Final Version) ---
    st.subheader(f"Latest {ticker} News")
    ticker_obj = yf.Ticker(ticker)
    news_data = ticker_obj.news

    if news_data:
        for article in news_data[:8]:  # Show top 8
            # 1. Get the content block
            content = article.get("content", article)
            
            # 2. Extract Data
            title = content.get("title", "No Title")
            
            # Link handling: Look in 'clickThroughUrl', then 'canonicalUrl', then 'link'
            link = None
            ct_url = content.get("clickThroughUrl")
            if isinstance(ct_url, dict):
                link = ct_url.get("url")
            if not link:
                link = content.get("canonicalUrl", {}).get("url")
            if not link:
                link = article.get("link")
            
            # 3. Layout with Image and Text
            with st.container():
                col1, col2 = st.columns([1, 3])
                
                # Thumbnail Logic
                thumb = content.get("thumbnail")
                has_image = False
                if isinstance(thumb, dict):
                    res = thumb.get("resolutions", [])
                    if res and isinstance(res, list):
                        col1.image(res[0].get("url"), use_container_width=True)
                        has_image = True
                
                if not has_image:
                    col1.info("No Image")

                with col2:
                    st.write(f"**{title}**")
                    if link:
                        st.markdown(f"[🔗 Read full article]({link})")
                    else:
                        st.write("*(Link unavailable)*")
                st.divider()
    else:
        st.write("No recent news found.")