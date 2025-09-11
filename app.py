import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pyxirr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Set page config
st.set_page_config(page_title="Portfolio Rebalancing Strategy", layout="wide")

# Title and description
st.title("📈 Portfolio Rebalancing Strategy Analysis")
st.markdown("""
This app analyzes a momentum-based trading strategy using moving averages.
Adjust the parameters below and click 'Run Analysis' to see the results.
""")

# Sidebar for parameters
st.sidebar.header("Strategy Parameters")

# Predefined tickers
ticker_options = {
    "Nippon India Small Cap": "0P0000XVFY.BO",
    "Motilal Oswal Midcap": "0P0001BAYU.BO",
    "Parag Parikh Flexi Cap": "0P0000YWL0.BO",
      "Abbott India": "ABBOTINDIA.NS",
      "Ashok Leyland": "ASHOKLEY.NS",
      "Bajaj Finance": "BAJFINANCE.NS",
      "Bharat Electronics": "BEL.NS",
      "Cholamandalam Finance": "CHOLAFIN.NS",
      "Data Patterns": "DATAPATTNS.NS",
      "Deepak Fertilisers": "DEEPAKFERT.NS",
      "Eicher Motors": "EICHERMOT.NS",
      "Godrej Industries": "GODREJIND.NS",
      "Hindustan Aeronautics": "HAL.NS",
      "HDFC Bank": "HDFCBANK.NS",
      "Kirloskar Engines": "KIRLOSENG.NS",
      "Larsen & Toubro": "LT.NS",
      "Max Healthcare": "MAXHEALTH.NS",
      "MCX India": "MCX.NS",
      "NBCC": "NBCC.NS",
      "Neuland Labs": "NEULANDLAB.NS",
      "Narayana Hrudayalaya": "NH.NS",
      "Nifty BeES": "NIFTYBEES.NS",
      "Zen Technologies": "ZENTEC.NS",
       "Gravita": "GRAVITA.NS"
}

# Allow custom ticker input
use_custom = st.sidebar.checkbox("Use custom ticker")
if use_custom:
    ticker = st.sidebar.text_input("Enter ticker symbol", value="0P0001BAYU.BO")
else:
    selected_fund = st.sidebar.selectbox("Select Fund", list(ticker_options.keys()))
    ticker = ticker_options[selected_fund]

from datetime import date

from datetime import datetime, timedelta

# Date range
st.sidebar.subheader("Date Range")

min_date = datetime.now() - timedelta(days=365*20)  # 20 years ago
max_date = datetime.now()  # Today

default_start = datetime(2024, 1, 1)
default_end = datetime.now()

start_date_input = st.sidebar.date_input("Start Date", value=default_start, min_value=min_date, max_value=max_date)
end_date_input = st.sidebar.date_input("End Date", value=default_end, min_value=min_date, max_value=max_date)

# Trading parameters
st.sidebar.subheader("Trading Parameters")
initial_capital = st.sidebar.number_input("Initial Capital (₹)", min_value=10000, max_value=10000000, value=1200000, step=10000)
sell_pct = st.sidebar.slider("Sell percentage (%)", min_value=0, max_value=20, value=5) / 100
strong_buy_allocation = st.sidebar.slider("Strong Buy allocation (%)", min_value=1, max_value=20, value=10) / 100
moderate_buy_allocation = st.sidebar.slider("Moderate Buy allocation (%)", min_value=1, max_value=10, value=2) / 100
profit_threshold = st.sidebar.slider("Profit threshold for selling (%)", min_value=1, max_value=20, value=9)

# Run analysis button
if st.sidebar.button("🚀 Run Analysis", type="primary"):
    
    # Calculate dates
    end_date = (end_date_input + timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (start_date_input - timedelta(days=365)).strftime("%Y-%m-%d") # For calculation of 180 days back..
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Fetch data
        status_text.text("Downloading market data...")
        progress_bar.progress(10)
        
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            st.error(f"No data found for ticker {ticker}")
            st.stop()
            
        progress_bar.progress(30)
        
        # Calculate moving averages
        status_text.text("Calculating moving averages...")
        data['30DMA'] = data['Close'].rolling(window=30).mean()
        data['50DMA'] = data['Close'].rolling(window=50).mean()
        data['200DMA'] = data['Close'].rolling(window=200).mean()
        
        # Remove NaN values
        data = data.dropna()
        
        if data.empty:
            st.error("Insufficient data after calculating moving averages")
            st.stop()
            
        progress_bar.progress(50)
        
        # Initialize portfolio
        portfolio = {
            'cash': initial_capital,
            'units': 0,
            'last_buy_price': None,
            'history': []
        }
        
        # Apply trading rules
        status_text.text("Applying trading strategy...")
        progress_bar.progress(70)
        
        # Lists to store history data with cash position
        trade_history_with_cash = []
        
        # Convert to arrays
        dates = data.index.to_numpy()
        close_prices = data['Close'].values
        dma30_values = data['30DMA'].values
        dma50_values = data['50DMA'].values
        dma200_values = data['200DMA'].values
        
        for i in range(len(dates)):
            date = dates[i]
            price = close_prices[i]
            dma30 = dma30_values[i]
            dma50 = dma50_values[i]
            dma200 = dma200_values[i]
            
            date = pd.Timestamp(date)
            
            # Strong Buy: 200DMA > 50DMA > Price
            if dma200 > dma50 > price and portfolio['cash'] > 0:
                allocation = portfolio['cash'] * strong_buy_allocation
                units = allocation / price
                if units > 0:
                    portfolio['units'] += units
                    portfolio['cash'] -= units * price
                    portfolio['last_buy_price'] = price
                    #['Date', 'Action', 'Type', 'Units', 'Price', 'Cash Position']
                    cash_rounded = int(portfolio['cash'][0])
                    cash_pct = int(100*portfolio['cash'][0]/initial_capital)
                    cash_pos = f"{cash_rounded} ( {cash_pct}% )"
                    trade_history_with_cash.append((date, 'Buy', 'Strong', units, price,  cash_pos ))
            
            # Moderate Buy: 50DMA > 30DMA > Price
            elif dma50 > dma30 > price and portfolio['cash'] > 0:
                allocation = portfolio['cash'] * moderate_buy_allocation
                units = allocation / price
                if units > 0:
                    portfolio['units'] += units
                    portfolio['cash'] -= units * price
                    portfolio['last_buy_price'] = price
                    cash_rounded = int(portfolio['cash'][0])
                    cash_pct = int(100*portfolio['cash'][0]/initial_capital)
                    cash_pos = f"{cash_rounded} ( {cash_pct}% )"
                    trade_history_with_cash.append((date, 'Buy', 'Moderate', units, price, cash_pos ))
            
            # Sell if conditions met
            elif (portfolio['units'] > 0 and 
                  portfolio['last_buy_price'] is not None and
                  price > dma50 > dma200):
                
                pct_change = (price - portfolio['last_buy_price']) / portfolio['last_buy_price'] * 100
                
                if pct_change >= profit_threshold:
                    units_to_sell = portfolio['units'] * sell_pct
                    if units_to_sell >= 1 :
                        portfolio['units'] -= units_to_sell
                        portfolio['cash'] += units_to_sell * price
                        cash_rounded = int(portfolio['cash'][0])
                        cash_pct = int(100*portfolio['cash'][0]/initial_capital)
                        cash_pos = f"{cash_rounded} ( {cash_pct}% )"
                        trade_history_with_cash.append((date, 'Sell', 'Profit_Taking', units_to_sell, price, cash_pos ))
        
        # Close remaining positions
        if portfolio['units'] > 0:
            last_price = float(close_prices[-1])
            portfolio['cash'] += portfolio['units'] * last_price
            cash_rounded = int(portfolio['cash'][0])
            cash_pct = int(100*portfolio['cash'][0]/initial_capital)
            cash_pos = f"{cash_rounded} ( {cash_pct}% )"
            trade_history_with_cash.append((pd.Timestamp(dates[-1]), 'Sell',  'Final_Exit', portfolio['units'], last_price, cash_pos ))
            portfolio['units'] = 0
        
        progress_bar.progress(90)
        
        # Calculate XIRR
        status_text.text("Calculating returns...")
        cash_flows = []
        cash_dates = []
        
        for h in trade_history_with_cash:
            date, action, type, units, price = h[:5]
            if action == 'Buy':
                cash_flow = -units * price
                cash_flows.append(cash_flow)
                cash_dates.append(date)
            elif action == 'Sell':
                cash_flow = units * price
                cash_flows.append(cash_flow)
                cash_dates.append(date)
        
        # Calculate XIRR
        xirr_value = 0
        if len(cash_flows) >= 2:
            try:
                xirr_value = pyxirr.xirr(cash_dates, cash_flows)
            except:
                xirr_value = 0
        
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        # Display results
        st.success("✅ Analysis completed successfully!")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_return = portfolio['cash'] - initial_capital
            return_pct = (portfolio['cash'] / initial_capital - 1) * 100
            st.metric("Total Return", f"₹{total_return[0]:.2f}", f"{return_pct}%")
        
        with col2:
            xirr_value_rounded = (xirr_value * 100)
            st.metric("XIRR (Annualized)", f"{round(xirr_value_rounded,2)}%")
        
        with col3:
            st.metric("Total Trades", len(trade_history_with_cash))
        
        with col4:
            st.metric("Final Value", f"₹{portfolio['cash'][0]:.2f}")
        
        # Buy and Hold comparison
        initial_price = close_prices[0]
        final_price = close_prices[-1]
        
        # --- Replace this chunk ---
        # buy_hold_return = (final_price / initial_price - 1) * 100
        # total_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        # total_years = total_days / 365.25
        # buy_hold_annualized = ((final_price / initial_price) ** (1/total_years) - 1) * 100
        
        #  Buy & Hold via XIRR ---
        bh_cash_flows = [
            -initial_capital,
            portfolio['cash'][0]
        ]
        bh_dates = [
            pd.to_datetime(dates[0]),
            pd.to_datetime(dates[-1])
        ]
        try:
            bh_xirr = pyxirr.xirr(bh_dates, bh_cash_flows)
        except Exception:
            bh_xirr = 0
        bh_xirr_pct = bh_xirr * 100

        #  End replacement ---
                
        st.subheader(" Strategy vs Buy & Hold")
        comp_col1, comp_col2, comp_col3 = st.columns(3)
        with comp_col1:
            # Optionally still show simple total return
            simple_bh_return = (final_price / initial_price - 1) * 100
            st.metric("Buy & Hold Return", f"{simple_bh_return[0]:.2f}%")
        with comp_col2:
            st.metric("Buy & Hold XIRR (Annualized)", f"{bh_xirr_pct:.2f}%")
        with comp_col3:
            strat_xirr_pct = xirr_value * 100
            outperformance = strat_xirr_pct - bh_xirr_pct
            st.metric("Strategy Outperformance", f"{outperformance:.2f}%")
        
        
        # Trade history
        if trade_history_with_cash:
            st.subheader("📋 Trade History")
            trade_df = pd.DataFrame(trade_history_with_cash, 
                                  columns=['Date', 'Action', 'Type', 'Units', 'Price', 'Cash Position'])

            # Convert numpy values to float for proper formatting
            trade_df['Units'] = trade_df['Units'].astype(float)
            trade_df['Price'] = trade_df['Price'].astype(float)
            trade_df['Value'] = trade_df['Units'] * trade_df['Price']
            
            # Round values for display
            trade_df['Units'] = trade_df['Units'].round(0)
            trade_df['Price'] = trade_df['Price'].round(1)
            trade_df['Value'] = trade_df['Value'].round(0)
            
            trade_df = trade_df.sort_values(by="Date", ascending=False)

            # format date nicely
            trade_df['Date'] = trade_df['Date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(trade_df, use_container_width=True)

            
            # Trade statistics
            st.subheader("📊 Trade Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                buy_trades = trade_df[trade_df['Action'] == 'Buy']
                sell_trades = trade_df[trade_df['Action'] == 'Sell']
                
                st.write(f"**Total Buy Trades:** {len(buy_trades)}")
                st.write(f"**Total Sell Trades:** {len(sell_trades)}")
                
                if len(buy_trades) > 0:
                    strong_buys = len(buy_trades[buy_trades['Type'] == 'Strong'])
                    moderate_buys = len(buy_trades[buy_trades['Type'] == 'Moderate'])
                    st.write(f"**Strong Buys:** {strong_buys}")
                    st.write(f"**Moderate Buys:** {moderate_buys}")
            
            with col2:
                if len(buy_trades) > 0:
                    total_invested = buy_trades['Value'].sum()
                    st.write(f"**Total Invested:** ₹{total_invested:,.2f}")
                
                if len(sell_trades) > 0:
                    total_received = sell_trades['Value'].sum()
                    st.write(f"**Total Received:** ₹{total_received:,.2f}")
                    
                    if len(buy_trades) > 0:
                        net_profit = total_received - total_invested
                        st.write(f"**Net Profit/Loss:** ₹{net_profit:,.2f}")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Please check your ticker symbol and try again.")
    
    finally:
        progress_bar.empty()
        status_text.empty()

else:
    st.info("👈 Configure your parameters in the sidebar and click 'Run Analysis' to start")
    
    # Show strategy explanation
    st.subheader("🎯 Strategy Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Buy Signals:**
        - **Strong Buy**: When 200DMA > 50DMA > Price (strong downtrend, oversold)
        - **Moderate Buy**: When 50DMA > 30DMA > Price (mild correction in uptrend)
        """)
    
    with col2:
        st.markdown("""
        **Sell Signals:**
        - Sell when Price < 50DMA < 200DMA and profit ≥ threshold
        - Partial selling (configurable percentage)
        - Final exit at end of period
        """)
    
    st.markdown("""
    **Key Features:**
    - Moving average-based momentum strategy
    - Risk management through partial selling
    - Configurable allocation percentages
    - XIRR calculation for annualized returns
    - Comparison with buy-and-hold strategy
    """)

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit • Data from Yahoo Finance*")
