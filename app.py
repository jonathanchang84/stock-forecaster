import streamlit as st
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go
from datetime import date

# 1. Page Config & Title
st.set_page_config(page_title="Stock Forecast App", layout="wide")
st.title("📈 AI Stock Prediction Dashboard")

<<<<<<< HEAD
# 2. Sidebar Navigation
st.sidebar.header("Top Performers")
top_stocks = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]

# Using a unique key to prevent the 'DuplicateElementId' error
selected_stock = st.sidebar.radio(
    "Quick Select:", 
    top_stocks, 
    key="sidebar_selector"
)

# 3. User Inputs
ticker = st.text_input("Enter Ticker Symbol (e.g. BTC-USD, AMD, AMZN):", selected_stock)
days_to_predict = st.slider("Days to predict into the future:", 30, 365)

# 4. Load Data Function
=======
# 2. User Input
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, BTC-USD)", "AAPL")
days_to_predict = st.slider("Days to predict into the future:", 30, 365)

# 3. Load Data
>>>>>>> parent of 59e9d0d (side nav addition)
@st.cache_data
def load_data(symbol):
    data = yf.download(symbol, start="2015-01-01", end=date.today().strftime("%Y-%m-%d"))
    data.reset_index(inplace=True)
    return data

<<<<<<< HEAD
data_load_state = st.text("Loading data...")
=======
>>>>>>> parent of 59e9d0d (side nav addition)
data = load_data(ticker)
data_load_state.text("Loading data... done!")

# 5. Raw Data Visualization
st.subheader(f"Historical Data for {ticker}")
st.line_chart(data.set_index('Date')['Close'])

# 6. Forecasting with Prophet
st.subheader("AI Forecast")
df_train = data[['Date', 'Close']]
df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})

m = Prophet()
m.fit(df_train)
future = m.make_future_dataframe(periods=days_to_predict)
forecast = m.predict(future)

# Show forecast chart
fig1 = plot_plotly(m, forecast)
st.plotly_chart(fig1)

# 7. History Table
st.subheader("Recent Price History")
# Formating the table to show newest dates first
history_table = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
history_table = history_table.sort_values(by='Date', ascending=False)
st.dataframe(history_table.head(20), use_container_width=True)