import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from datetime import date

# 1. Setup the Title
st.title("My AI Stock Forecast Tool")

# --- SIDEBAR NAVIGATION ---
st.sidebar.header("Top Performers")
top_stocks = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
selected_stock = st.sidebar.radio("Select a stock to view:", top_stocks)

# 2. User Input
ticker = st.text_input("Or enter any ticker manually:", selected_stock)

# --- ADD THIS LINE BACK ---
days_to_predict = st.slider("Days to predict into the future:", 30, 365)

# --- LOAD DATA ---
@st.cache_data
def load_data(symbol):
    # We use the 'ticker' variable which is now linked to the sidebar
    data = yf.download(symbol, start="2015-01-01", end=date.today().strftime("%Y-%m-%d"))
    data.reset_index(inplace=True)
    return data

# The rest of your code (Forecasting & Table) stays the same!
data = load_data(ticker)

# --- THE FIX STARTS HERE ---
# We need to make sure the data is "flat" so the AI can read it
df_train = data[['Date', 'Close']].copy()
df_train.columns = ['ds', 'y'] # Prophet requires these specific names
df_train['ds'] = df_train['ds'].dt.tz_localize(None) # Remove timezones
df_train['y'] = df_train['y'].values.flatten() # Make sure it's a simple list
# --- THE FIX ENDS HERE ---

# 4. The Forecasting Logic
m = Prophet()
m.fit(df_train)
future = m.make_future_dataframe(periods=days_to_predict)
forecast = m.predict(future)

# 5. Display the Chart
st.subheader(f"Prediction for {ticker}")
fig1 = plot_plotly(m, forecast)
st.plotly_chart(fig1)

st.write("Black dots = Actual Price | Blue line = Prediction")
# 6. Display the History Table
st.subheader("Historical Price Data")

# We use .tail(10) to show the most recent 10 days so the table isn't too long
# .sort_values(by='Date', ascending=False) puts the newest date at the top
history_table = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
history_table = history_table.sort_values(by='Date', ascending=False)

st.dataframe(history_table.head(20)) # Shows the top 20 rows
