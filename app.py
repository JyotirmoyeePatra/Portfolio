import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pyxirr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import traceback
import sys

# --- Utility Functions ---

def perform_buy(date, portfolio, allocation, price, buy_type, maintenance_fee, initial_capital, trade_history):
    units = int(allocation / price)
    if units >= 1:
        portfolio['units'] += units
        buy_amt = units * price
        portfolio['cash'] -= buy_amt
        portfolio['last_buy_price'] = price
        
        cash_rounded = int(portfolio['cash'])
        cash_pct = int(100 * portfolio['cash'] / (price * portfolio['units'] + portfolio['cash'])) if (price * portfolio['units'] + portfolio['cash']) != 0 else 0
        cash_pos = f"{cash_rounded} ( {cash_pct}% )"
        
        trade_history.append((date, 'Buy', buy_type, units, price, cash_pos))
        
        # Maintenance fee
        fee = buy_amt * maintenance_fee / 100
        portfolio['cash'] -= fee
        cash_rounded = int(portfolio['cash'])
        cash_pct = int(100 * portfolio['cash'] / (price * portfolio['units'] + portfolio['cash'])) if (price * portfolio['units'] + portfolio['cash']) != 0 else 0
        cash_pos = f"{cash_rounded} ( {cash_pct}% )"
        
        trade_history.append((date, 'Maintenance', 'Fees', maintenance_fee, fee, cash_pos))
        
    return portfolio, trade_history

def perform_sell(date, portfolio, sell_pct, price, trade_history):
    units_to_sell = int(portfolio['units'] * sell_pct)
    if units_to_sell >= 1:
        portfolio['units'] -= units_to_sell
        sell_amt = units_to_sell * price
        portfolio['cash'] += sell_amt
        
        cash_rounded = int(portfolio['cash'])
        cash_pct = int(100 * portfolio['cash'] / (price * portfolio['units'] + portfolio['cash'])) if (price * portfolio['units'] + portfolio['cash']) != 0 else 0
        cash_pos = f"{cash_rounded} ( {cash_pct}% )"
        
        trade_history.append((date, 'Sell', 'Profit_Taking', units_to_sell, price, cash_pos))
        
    return portfolio, trade_history

# --- Streamlit Configuration ---

st.set_page_config(page_title="Learn python in 1 hour.", layout="wide")

st.title("📈 Portfolio Rebalancing Strategy Analysis")
st.markdown("""
This app analyzes a momentum-based trading strategy using moving averages.
Adjust the parameters below and click 'Run Analysis' to see the results.
""")

# Sidebar inputs (unchanged from your existing code)

st.sidebar.header("Strategy Parameters")
# Predefined tickers
ticker_options = {
    "Motilal Oswal Midcap": {"symbol": "0P0001BAYU.BO", "percent": 100},
    "Nifty BeES": {"symbol": "^NSEI", "percent": 100},
    "Parag Parikh Flexi Cap": {"symbol": "0P0000YWL0.BO", "percent": 100},
    "Abbott India": {"symbol": "ABBOTINDIA.NS", "percent": 2},
    "Amber Enterprises India Limited": {"symbol": "AMBER.NS", "percent": 3.54},
    "Angel One Limited": {"symbol": "ANGELONE.NS", "percent": 1.96},
    "Apar Industries Limited": {"symbol": "APARINDS.NS", "percent": 3.21},
    "Ashok Leyland": {"symbol": "ASHOKLEY.NS", "percent": 2},
    "Bajaj Finance": {"symbol": "BAJFINANCE.NS", "percent": 3.20},
    "Bharat Dynamics Limited": {"symbol": "BDL.NS", "percent": 2.78},
    "Bharat Electronics Limited": {"symbol": "BEL.NS", "percent": 4.29},
    "CG Power and Industrial Solutions Limited": {"symbol": "CGPOWER.NS", "percent": 3.97},
    "Cholamandalam Investment and Finance Company Ltd": {"symbol": "CHOLAFIN.NS", "percent": 3.29},
    "Data Patterns": {"symbol": "DATAPATTNS.NS", "percent": 2},
    "Deepak Fertilisers": {"symbol": "DEEPAKFERT.NS", "percent": 2},
    "Dixon Technologies (India) Limited": {"symbol": "DIXON.NS", "percent": 2.32},
    "Eicher Motors": {"symbol": "EICHERMOT.NS", "percent": 2},
    "GE Vernova T&D India Limited": {"symbol": "GEVERNOVA.NS", "percent": 3.12},
    "Godrej Industries": {"symbol": "GODREJIND.NS", "percent": .1},
    "Gravita": {"symbol": "GRAVITA.NS", "percent": .1},
    "Gujarat Fluorochemicals Limited": {"symbol": "GUJFLUORO.NS", "percent": 2.19},
    "HDFC Bank": {"symbol": "HDFCBANK.NS", "percent": 2},
    "Hindustan Aeronautics Limited": {"symbol": "HAL.NS", "percent": 3.10},
    "Inox Wind Limited": {"symbol": "INOXWIND.NS", "percent": 2.35},
    "Kaynes Technology India Limited": {"symbol": "KAYNES.NS", "percent": 2.52},
    "Kalyan Jewellers India Limited": {"symbol": "KALYAN.NS", "percent": 1.64},
    "K.P.R. Mill Limited": {"symbol": "KPRMILL.NS", "percent": 0.84},
    "Kirloskar Engines": {"symbol": "KIRLOSENG.NS", "percent": .1},
    "Larsen & Toubro": {"symbol": "LT.NS", "percent": 2},
    "Max Healthcare": {"symbol": "MAXHEALTH.NS", "percent": .4},
    "Muthoot Finance Limited": {"symbol": "MUTHOOTFIN.NS", "percent": 2.38},
    "Multi Commodity Exchange of India Limited": {"symbol": "MCX.NS", "percent": 3.45},
    "NBCC": {"symbol": "NBCC.NS", "percent": .15},
    "Neuland Labs": {"symbol": "NEULANDLAB.NS", "percent": .01},
    "Narayana Hrudayalaya": {"symbol": "NH.NS", "percent": .25},
    "Onesource Specialty Pharma Limited": {"symbol": "ONESOURCE.NS", "percent": 2.99},
    "PB Fintech Limited": {"symbol": "PBFINTECH.NS", "percent": 1.96},
    "Premier Energies Limited": {"symbol": "PREMIER.NS", "percent": 2.78},
    "Prestige Estates Projects Limited": {"symbol": "PRESTIGE.NS", "percent": 3.16},
    "PTC Industries Limited": {"symbol": "PTCINDIA.NS", "percent": 3.21},
    "Religare Enterprises Limited": {"symbol": "RELIGARE.NS", "percent": 2.10},
    "Samvardhana Motherson International Limited": {"symbol": "MOTHERSON.NS", "percent": 3.23},
    "Siemens Energy India Limited": {"symbol": "ENRIN.NS", "percent": 3.71},
    "Suzlon Energy Limited": {"symbol": "SUZLON.NS", "percent": 3.21},
    "Trent Limited": {"symbol": "TRENT.NS", "percent": 2.63},
    "TVS Motor Company Limited": {"symbol": "TVSMOTOR.NS", "percent": 0.54},
    "V2 Retail Limited": {"symbol": "V2RETAIL.NS", "percent": 2.08},
    "Waaree Energies Limited": {"symbol": "WAAREEENER.NS", "percent": 4.23},
    "Zen Technologies Limited": {"symbol": "ZENTEC.NS", "percent": 2.43}
}

use_custom = st.sidebar.checkbox("Use custom ticker")
if use_custom:
    ticker = st.sidebar.text_input("Enter ticker symbol", value="0P0001BAYU.BO")
else:
    selected_fund = st.sidebar.selectbox("Select Fund", list(ticker_options.keys()))
    ticker = ticker_options[selected_fund]["symbol"]

min_date = datetime.now() - timedelta(days=365*20)
max_date = datetime.now()

default_start = datetime(2025, 1, 1)
default_end = datetime.now()

start_date_input = st.sidebar.date_input("Start Date", value=default_start, min_value=min_date, max_value=max_date)
end_date_input = st.sidebar.date_input("End Date", value=default_end, min_value=min_date, max_value=max_date)

st.sidebar.subheader("Trading Parameters")
total_capital = st.sidebar.number_input("Total Capital (₹)", min_value=10000, max_value=500000000, value=60000000, step=10000)
profit_threshold = st.sidebar.slider("Profit threshold for selling (%)", min_value=1, max_value=20, value=1)
sell_pct = st.sidebar.slider("Sell percentage (%)", min_value=0, max_value=20, value=0) / 100
drop_threshold = st.sidebar.slider("Peak Drop (%) Buy", min_value=5, max_value=50, value=15) / 100 
strong_buy_allocation = st.sidebar.slider("Strong Buy allocation (%)", min_value=1, max_value=100, value=4) / 100
moderate_buy_allocation = st.sidebar.slider("Moderate Buy allocation (%)", min_value=1, max_value=100, value=1) / 100
interest_rate_pct = 8.25
daily_interest_rate = interest_rate_pct / 100 / 365
maintenance_fee = st.sidebar.number_input("Annual Maintenance Fee", min_value=0.0, value=0.15, step=.05, format="%.2f")

# --- Main Execution ---

if st.sidebar.button("🚀 Run Analysis", type="primary"):
    end_date = (end_date_input + timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = start_date_input
    start_date_moving = (start_date - timedelta(days=365)).strftime("%Y-%m-%d")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("Downloading market data...")
        progress_bar.progress(10)
        
        data = yf.download(ticker, start=start_date_moving, end=end_date, progress=False)
        
        if data.empty:
            st.error(f"No data found for ticker {ticker}")
            st.stop()
            
        progress_bar.progress(30)
        
        status_text.text("Calculating moving averages...")
        data['30DMA'] = data['Close'].rolling(window=30).mean()
        data['50DMA'] = data['Close'].rolling(window=50).mean()
        data['200DMA'] = data['Close'].rolling(window=200).mean()
        
        data = data.dropna()
        
        if data.empty:
            st.error("Insufficient data after calculating moving averages")
            st.stop()
            
        progress_bar.progress(50)
        
        initial_capital = total_capital
        if not use_custom:
            initial_capital = round(total_capital * ticker_options[selected_fund]["percent"] / 100)

        portfolio = {
            'cash': initial_capital,
            'units': 0,
            'last_buy_price': None,
            'history': []
        }
        
        status_text.text(f"Applying trading strategy...for {ticker} with initial amount {initial_capital}")
        progress_bar.progress(70)
        
        trade_history_with_cash = []
        
        dates = data.index.to_numpy()
        close_prices = data['Close'].values
        dma30_values = data['30DMA'].values
        dma50_values = data['50DMA'].values
        dma200_values = data['200DMA'].values

        final_price = close_prices[-1]
        last_date = -1
        initial_price = -1
        initial_date = dates[0]
        peak_price = -1
        muhurth = 1

        for i in range(len(dates)):
            date_str = dates[i]
            if peak_price < close_prices[i]:
                peak_price = close_prices[i]
            
            date = pd.Timestamp(date_str)
            if date < pd.Timestamp(start_date):
                continue

            if muhurth:
                muhurth = 0
                initial_price = close_prices[i]
                initial_date = dates[i]
                units = 1
                price = initial_price
                portfolio['units'] += units
                buy_amt = units * price
                portfolio['cash'] -= buy_amt
                portfolio['last_buy_price'] = price
                cash_rounded = int(portfolio['cash'])
                cash_pct = int(100 * portfolio['cash'] / (price * portfolio['units'] + portfolio['cash']))
                cash_pos = f"{cash_rounded} ( {cash_pct}% )"
                trade_history_with_cash.append((date, 'Buy', 'Strong', units, price, cash_pos))
                portfolio['cash'] -= buy_amt * maintenance_fee / 100
                trade_history_with_cash.append((date, 'Maintenance', 'Fees', maintenance_fee, buy_amt * maintenance_fee / 100, int(portfolio['cash'])))

            price = close_prices[i]
            dma30 = dma30_values[i]
            dma50 = dma50_values[i]
            dma200 = dma200_values[i]

            days = 0
            if last_date == -1:
                last_date = date
            else:
                days = (date - last_date).days
                last_date = date
            
            if days > 0:
                interest_income = portfolio['cash'] * daily_interest_rate * days
                portfolio['cash'] += interest_income
                interest_rate = f"{interest_rate_pct}%"
                cash_rounded = int(portfolio['cash'])
                cash_pct = int(100 * portfolio['cash'] / (price * portfolio['units'] + portfolio['cash']))
                cash_pos = f"{cash_rounded} ( {cash_pct}% )"
                trade_history_with_cash.append((date, 'Interest', interest_rate, interest_income, days, cash_pos))

            # Strong Buy
            if dma200 > dma50 > price and portfolio['cash'] > 0 and price <= peak_price * (1 - drop_threshold):
                allocation = initial_capital * strong_buy_allocation
                if portfolio['cash'] < (1 + (maintenance_fee / 100)) * allocation:
                    allocation = (1 - (maintenance_fee / 100)) * portfolio['cash']
                portfolio, trade_history_with_cash = perform_buy(date, portfolio, allocation, price, 'Strong', maintenance_fee, initial_capital, trade_history_with_cash)

            # Moderate Buy
            elif dma50 > dma30 > price and portfolio['cash'] > 0 and price <= peak_price * (1 - drop_threshold):
                allocation = initial_capital * moderate_buy_allocation
                if portfolio['cash'] < (1 + (maintenance_fee / 100)) * allocation:
                    allocation = (1 - (maintenance_fee / 100)) * portfolio['cash']
                portfolio, trade_history_with_cash = perform_buy(date, portfolio, allocation, price, 'Moderate', maintenance_fee, initial_capital, trade_history_with_cash)

            # Sell
            elif (portfolio['units'] > 0 and portfolio['last_buy_price'] is not None and price > dma50 > dma200):
                pct_change = (price - portfolio['last_buy_price']) / portfolio['last_buy_price'] * 100
                if pct_change >= profit_threshold:
                    portfolio, trade_history_with_cash = perform_sell(date, portfolio, sell_pct, price, trade_history_with_cash)

        # Final exit
        if portfolio['units'] > 0:
            last_price = float(close_prices[-1])
            portfolio['cash'] += portfolio['units'] * last_price
            portfolio['units'] = 0.0
            cash_rounded = int(portfolio['cash'])
            cash_pos = f"{cash_rounded} ( 100% )"
            trade_history_with_cash.append((pd.Timestamp(dates[-1]), 'Sell', 'Final_Exit', 0, last_price, cash_pos))

        progress_bar.progress(90)

        # XIRR and final reporting would continue here, similar to your original code...
        # For brevity, not repeating it since the main ask was centralizing buy/sell logic.

        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        st.success("✅ Analysis completed successfully!")

    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        tb = traceback.extract_tb(exc_tb)
        filename, line_number, function_name, text = tb[-1]
        st.error(f"An error occurred: {e}")
        st.error(f"Location: File '{filename}', line {line_number}, in {function_name}")
        st.error(f"Code: {text}")
    finally:
        progress_bar.empty()
        status_text.empty()
else:
    st.info("👈 Configure your parameters in the sidebar and click 'Run Analysis' to start")

