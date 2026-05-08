import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from datetime import date

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Stock Forecast AI", layout="wide")

# --- 2. SIDEBAR NAVIGATION ---
st.sidebar.header("Navigation")

# Top performing stocks list
top_stocks = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]

# We use a very specific 'key' here to prevent the duplicate ID error
selected_from_sidebar = st.sidebar.radio(
    "Quick Select a Stock:", 
    options=top_stocks, 
    key="sidebar_navigation_radio_v1"
)

# --- 3. MAIN INTERFACE ---
st.title("📈 AI Stock Prediction Dashboard")

# The text input is 'linked' to the sidebar selection
ticker = st.text_input("Stock Ticker:", value=selected_from_sidebar)

# Prediction slider
days_to_predict = st.slider("Forecast Days:", 30, 365, 90)

# --- 4. DATA ENGINE ---
@st.cache_data
def load_data(symbol):
    try:
        # We add 'auto_adjust=True' to help simplify the columns
        df = yf.download(symbol, start="2015-01-01", end=date.today().strftime("%Y-%m-%d"), auto_adjust=True)
        df.reset_index(inplace=True)
        
        # MANDATORY FIX: If yfinance returns multi-level columns, we flatten them
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except Exception as e:
        st.error(f"Error loading {symbol}: {e}")
        return None

# Add this line at the very top of your imports if you don't have it:
import pandas as pd 

data = load_data(ticker)

if data is not None and not data.empty:
    # --- 5. VISUALIZATION ---
    st.subheader(f"Historical Price: {ticker}")
    
    # We ensure we are looking for the 'Close' column in a clean way
    if 'Close' in data.columns:
        st.line_chart(data.set_index('Date')['Close'])
    else:
        st.error("Could not find 'Close' column. Columns found: " + str(list(data.columns)))
    # --- 5. VISUALIZATION ---
    st.subheader(f"Historical Price: {ticker}")
    st.line_chart(data.set_index('Date')['Close'])

        # --- 6. AI FORECASTING ---
    st.subheader("AI Future Trend")
    
    # 1. Prepare data (Flatten the headers and remove timezone)
    df_train = data[['Date', 'Close']].copy()
    
    # This line fixes the specific TypeError you saw:
    df_train.columns = ['ds', 'y'] 
    
    # Ensure 'y' is a simple list of numbers and 'ds' has no timezone
    df_train['y'] = df_train['y'].values.flatten()
    df_train['ds'] = df_train['ds'].dt.tz_localize(None)
    
    # 2. Run the AI
    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=days_to_predict)
    forecast = m.predict(future)
    
    # 3. Show forecast chart
    fig = plot_plotly(m, forecast)
    st.plotly_chart(fig, use_container_width=True)

    # --- 7. HISTORY TABLE ---
    st.subheader("Latest Price Records")
    # Show newest data at the top
    st.dataframe(data.sort_values(by='Date', ascending=False).head(20), use_container_width=True)
else:
    st.warning("No data found for that ticker. Please check the symbol and try again.")