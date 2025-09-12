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

# Allow custom ticker input
use_custom = st.sidebar.checkbox("Use custom ticker")
if use_custom:
    ticker = st.sidebar.text_input("Enter ticker symbol", value="0P0001BAYU.BO")
else:
    selected_fund = st.sidebar.selectbox("Select Fund", list(ticker_options.keys()))
    ticker = ticker_options[selected_fund]["symbol"]

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
total_capital = st.sidebar.number_input("Total Capital (₹)", min_value=10000, max_value=500000000, value=60000000, step=10000)
sell_pct = st.sidebar.slider("Sell percentage (%)", min_value=0, max_value=20, value=5) / 100
strong_buy_allocation = st.sidebar.slider("Strong Buy allocation (%)", min_value=1, max_value=20, value=4) / 100
moderate_buy_allocation = st.sidebar.slider("Moderate Buy allocation (%)", min_value=1, max_value=10, value=2) / 100
profit_threshold = st.sidebar.slider("Profit threshold for selling (%)", min_value=1, max_value=20, value=9)
daily_interest_rate = profit_threshold / 100 / 365

# Run analysis button
if st.sidebar.button("🚀 Run Analysis", type="primary"):
    
    # Calculate dates
    end_date = (end_date_input + timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = start_date_input
    start_date_moving = (start_date - timedelta(days=365)).strftime("%Y-%m-%d") # For calculation of 180 days back..
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Fetch data
        status_text.text("Downloading market data...")
        progress_bar.progress(10)
        
        data = yf.download(ticker, start=start_date_moving, end=end_date, progress=False)
        
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
        initial_capital = round(total_capital * ticker_options[selected_fund]["percent"] / 100)
        portfolio = {
            'cash': initial_capital,
            'units': 0,
            'last_buy_price': None,
            'history': []
        }
        
        # Apply trading rules
        status_text.text(f"Applying trading strategy...for {selected_fund} with initial amount {initial_capital}")
        progress_bar.progress(70)
        
        # Lists to store history data with cash position
        trade_history_with_cash = []
        
        # Convert to arrays
        dates = data.index.to_numpy()
        close_prices = data['Close'].values
        dma30_values = data['30DMA'].values
        dma50_values = data['50DMA'].values
        dma200_values = data['200DMA'].values

        initial_price = 0
        for i in range(len(dates)):
            date = dates[i]
            
            #Skip past dates.
            if pd.Timestamp(date) < start_date:
                initial_price = close_prices[i]
                continue
            
            price = close_prices[i]
            dma30 = dma30_values[i]
            dma50 = dma50_values[i]
            dma200 = dma200_values[i]
            
            date = pd.Timestamp(date)

            interest_income = portfolio['cash'] * daily_interest_rate
            portfolio['cash'] += interest_income
            trade_history_with_cash.append((date, 'Interest', 'f{profit_threshold}%ge', interest_income, 1, int(portfolio['cash'])))
            
            # Strong Buy: 200DMA > 50DMA > Price
            if dma200 > dma50 > price and portfolio['cash'] > 0:
                allocation = portfolio['cash'] * strong_buy_allocation
                units = allocation / price
                if units >= 1:
                    portfolio['units'] += units
                    buy_amt = units * price
                    portfolio['cash'] -= buy_amt
                    portfolio['last_buy_price'] = price
                    #['Date', 'Action', 'Type', 'Units', 'Price', 'Cash Position']
                    cash_rounded = int(portfolio['cash'])
                    cash_pct = int(100*portfolio['cash']/initial_capital)
                    cash_pos = f"{cash_rounded} ( {cash_pct}% )"
                    trade_history_with_cash.append((date, 'Buy', 'Strong', units, price,  cash_pos ))
                    #0.65% for maintenance fees
                    portfolio['cash'] -= buy_amt * .0065
                    trade_history_with_cash.append((date, 'Maintenance', 'Fees %ge', 0.65,  (buy_amt * .0065), int(portfolio['cash']) ))
            
            # Moderate Buy: 50DMA > 30DMA > Price
            elif dma50 > dma30 > price and portfolio['cash'] > 0:
                allocation = portfolio['cash'] * moderate_buy_allocation
                units = allocation / price
                if units >= 1:
                    portfolio['units'] += units
                    buy_amt = units * price
                    portfolio['cash'] -= buy_amt
                    portfolio['last_buy_price'] = price
                    cash_rounded = int(portfolio['cash'])
                    cash_pct = int(100*portfolio['cash']/initial_capital)
                    cash_pos = f"{cash_rounded} ( {cash_pct}% )"
                    trade_history_with_cash.append((date, 'Buy', 'Moderate', units, price, cash_pos ))
                    #0.65% for maintenance fees
                    portfolio['cash'] -= buy_amt * .0065
                    trade_history_with_cash.append((date, 'Maintenance', 'Fees %ge', 0.65,  (buy_amt * .0065), int(portfolio['cash']) ))
            
            # Sell if conditions met
            elif (portfolio['units'] > 0 and 
                  portfolio['last_buy_price'] is not None and
                  price > dma50 > dma200):
                
                pct_change = (price - portfolio['last_buy_price']) / portfolio['last_buy_price'] * 100
                
                if pct_change >= profit_threshold:
                    units_to_sell = portfolio['units'] * sell_pct
                    if units_to_sell >= 1 :
                        portfolio['units'] -= units_to_sell
                        sell_amt = units_to_sell * price
                        portfolio['cash'] += sell_amt
                        cash_rounded = int(portfolio['cash'])
                        cash_pct = int(100*portfolio['cash']/initial_capital)
                        cash_pos = f"{cash_rounded} ( {cash_pct}% )"
                        trade_history_with_cash.append((date, 'Sell', 'Profit_Taking', units_to_sell, price, cash_pos ))

        
        # Close remaining positions
        if portfolio['units'] > 0:
            last_price = float(close_prices[-1])
            portfolio['cash'] += portfolio['units'] * last_price
            cash_rounded = int(portfolio['cash'])
            cash_pct = int(100*portfolio['cash']/initial_capital)
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
        status_text.text("Analysis complete for {selected_fund} with initial amount {initial_capital}!")
        
        # Display results
        st.success("✅ Analysis completed successfully!")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_return = portfolio['cash'][0] - initial_capital
            return_pct = (portfolio['cash'][0] / initial_capital - 1) * 100
            return_pct_rounded = f"{return_pct:.2f}%"
            st.metric("Total Return", f"₹{total_return:.0f}", f"{return_pct_rounded}")
        
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
        buy_hold_return = ( (initial_capital/initial_price) * (final_price) ) - initial_capital
        total_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        total_years = total_days / 365.25
        buy_hold_annualized = ((final_price / initial_price) ** (1/total_years) - 1) * 100
        
        #  Buy & Hold via XIRR ---
        bh_cash_flows = [
            -initial_capital,
            portfolio['cash']
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
            st.metric("Buy & Hold Return", f"₹{buy_hold_return[0]:.0f}")
        with comp_col2:
            st.metric("Buy & Hold XIRR (Annualized)", f"{bh_xirr_pct:.2f}%")
        with comp_col3:
            strat_xirr_pct = xirr_value * 100
            outperformance = strat_xirr_pct - bh_xirr_pct
            st.metric("Strategy Outperformance", f"{outperformance:.2f}%")

        st.subheader("💰 Investment Details")
        st.write(f"**Symbol:** {selected_fund}     ,    **Invested Capital** {initial_capital}")
        
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
