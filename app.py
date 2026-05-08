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