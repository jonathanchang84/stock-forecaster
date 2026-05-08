import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from datetime import date

# 1. Setup the Title
st.title("My AI Stock Forecast Tool")

# 2. User Input
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, BTC-USD)", "AAPL")
days_to_predict = st.slider("Days to predict into the future:", 30, 365)

# 3. Load Data
@st.cache_data
def load_data(symbol):
    data = yf.download(symbol, start="2015-01-01", end=date.today().strftime("%Y-%m-%d"))
    data.reset_index(inplace=True)
    return data

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