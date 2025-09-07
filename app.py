import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import fsolve
from datetime import datetime, timedelta
import pyxirr

# ----------------------------
# Parameters
#   "Nippon India Small Cap": "0P0000XVFY.BO",
#    "Motilal Oswal Midcap": "0P0001BAYU.BO",
#    "Quant Infrastructure": "0P0001BA3M.BO",
#    "Parag Parikh Flexi Cap": "0P0000YWL0.BO"
# ----------------------------
ticker = "0P0001BAYU.BO"
look_back_days=-365*1
end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") # Changed to today + 1 day
start_date = (datetime.now() + timedelta(days=look_back_days)).strftime("%Y-%m-%d" )
initial_capital = 100000
sell_pct = 0.05  # Sell only 5% of holdings

# ----------------------------
# Fetch historical data
# ----------------------------
print(f"Downloading data for {ticker}...")
data = yf.download(ticker, start=start_date, end=end_date)
print(f"Downloaded {len(data)} days of data")

# ----------------------------
# Calculate 50DMA and 200DMA
# ----------------------------
data['30DMA'] = data['Close'].rolling(window=30).mean()
data['50DMA'] = data['Close'].rolling(window=50).mean()
data['200DMA'] = data['Close'].rolling(window=200).mean()

# Remove rows where moving averages are NaN
data = data.dropna()
print(f"Data after removing NaN values: {len(data)} days")

# Convert to numpy arrays for easier scalar access
dates = data.index.to_numpy()
close_prices = data['Close'].values
dma30_values = data['30DMA'].values
dma50_values = data['50DMA'].values
dma200_values = data['200DMA'].values

# ----------------------------
# Initialize Portfolio
# ----------------------------
portfolio = {
    'cash': initial_capital,
    'units': 0,
    'last_buy_price': None,
    'history': []
}

# ----------------------------
# Apply Trading Rules
# ----------------------------
print("Applying trading rules...")
trade_count = 0

for i in range(len(dates)):
    date = dates[i]
    price = close_prices[i]
    dma30 = dma30_values[i]
    dma50 = dma50_values[i]
    dma200 = dma200_values[i]
    
    # Convert numpy.datetime64 to pandas Timestamp for consistency
    date = pd.Timestamp(date)
    
    # Strong Buy: 200DMA > 50DMA > Price (strong downtrend, oversold)
    if dma200 > dma50 > price and portfolio['cash'] > 0:
        allocation = portfolio['cash'] * 0.10
        units = allocation / price
        if units > 0:
            portfolio['units'] += units
            portfolio['cash'] -= units * price
            portfolio['last_buy_price'] = price
            portfolio['history'].append((date, 'Buy', units, price, 'Strong'))
            trade_count += 1
            print(f"{date.strftime('%Y-%m-%d')}: Strong Buy - {units} units at ₹{price}")
    
    # Moderate Buy: 50DMA > 200DMA > Price (mild correction in uptrend)
    elif dma50 > dma30 > price and portfolio['cash'] > 0:
        allocation = portfolio['cash'] * 0.02
        units = allocation / price
        if units > 0:
            portfolio['units'] += units
            portfolio['cash'] -= units * price
            portfolio['last_buy_price'] = price
            portfolio['history'].append((date, 'Buy', units, price, 'Moderate'))
            trade_count += 1
            print(f"{date.strftime('%Y-%m-%d')}: Moderate Buy - {units} units at ₹{price}")
    
    # Sell 5% if price < 50DMA < 200DMA and 8% gain from last buy
    elif (portfolio['units'] > 0 and 
          portfolio['last_buy_price'] is not None and
          price < dma50 < dma200):
        
        pct_change = (price - portfolio['last_buy_price']) / portfolio['last_buy_price'] * 100
        
        if pct_change >= 8:
            units_to_sell = portfolio['units'] * sell_pct
            portfolio['units'] -= units_to_sell
            portfolio['cash'] += units_to_sell * price
            portfolio['history'].append((date, 'Sell', units_to_sell, price, 'Profit_Taking'))
            trade_count += 1
            print(f"{date.strftime('%Y-%m-%d')}: Sell - {units_to_sell} units at ₹{price} ({pct_change}% gain)")

print(f"Total trades executed: {trade_count}")

# ----------------------------
# Close all remaining positions
# ----------------------------
if portfolio['units'] > 0:
    last_price = float(close_prices[-1])
    final_units = float(portfolio['units'])
    portfolio['cash'] += portfolio['units'] * last_price
    portfolio['history'].append((pd.Timestamp(dates[-1]), 'Sell', portfolio['units'], last_price, 'Final_Exit'))
    portfolio['units'] = 0
    print(f"Final exit: Sold {final_units} units at ₹{last_price}")

# ----------------------------
# Prepare cash flows for XIRR
# ----------------------------
cash_flows = []
cash_dates = []

# Add initial investment as negative cash flow
#cash_flows.append(-initial_capital)
#cash_dates.append(pd.to_datetime(start_date))

print(f"\nCash flows for XIRR calculation:")
print(f"Initial investment: -₹{initial_capital} on {start_date}")

# Add all buy/sell transactions
for h in portfolio['history']:
    date, action, units, price = h[:4]
    if action == 'Buy':
        cash_flow = -units * price  # Negative for outflows
        cash_flows.append(cash_flow)
        cash_dates.append(date)
        print(f"{action}: -₹{abs(cash_flow)} on {date.strftime('%Y-%m-%d')}")
    elif action == 'Sell':
        cash_flow = units * price  # Positive for inflows
        cash_flows.append(cash_flow)
        cash_dates.append(date)
        print(f"{action}: +₹{cash_flow} on {date.strftime('%Y-%m-%d')}")

# Add final portfolio value as positive cash flow if no final exit recorded
if len([h for h in portfolio['history'] if 'Final_Exit' in str(h)]) == 0:
    cash_flows.append(portfolio['cash'])
    cash_dates.append(pd.Timestamp(dates[-1]))

# ----------------------------
# XIRR calculation
# ----------------------------
def calculate_xirr(cash_flows, dates):
    """
    Calculate XIRR using pyxirr
    """
    print ( "DEBUG Calculate XIRR using pyxirr")
    print ( cash_flows ) 
    if len(cash_flows) < 2:
        return 0
    try:
        # pyxirr.xirr expects a list of dates and a list of cash flows
        return pyxirr.xirr(dates, cash_flows)
    except Exception as e:
        print(f"Error calculating XIRR: {e}")
        return 0

# Calculate XIRR
try:
    xirr_value = calculate_xirr(cash_flows, cash_dates)
except ValueError:
    print("XIRR calculation failed. Check cash flow values.")
    xirr_value = 0 # Fallback to 0 or another suitable value


# ----------------------------
# Results Summary
# ----------------------------
print(f"\n{'='*50}")
print("PORTFOLIO PERFORMANCE SUMMARY")
print(f"{'='*50}")
print(f"Initial Capital: ₹{initial_capital}")
print(f"Final Cash: ₹{portfolio['cash']}")
print(f"Total Return: ₹{portfolio['cash'] - initial_capital}")
print(f"Absolute Return: {(portfolio['cash'] / initial_capital - 1) * 100}%")
print(f"XIRR (Annualized): {xirr_value * 100}%")

# Calculate period details
start_dt = pd.to_datetime(start_date)
end_dt = pd.to_datetime(end_date)
total_days = (end_dt - start_dt).days
total_years = total_days / 365.25

print(f"Investment Period: {total_days} days ({total_years} years)")
print(f"Total Trades: {len(portfolio['history'])}")

# Calculate buy and hold return for comparison
if len(close_prices) > 0:
    initial_price = close_prices[0]
    final_price = close_prices[-1]
    buy_hold_return = (final_price / initial_price - 1) * 100
    buy_hold_annualized = ((final_price / initial_price) ** (1/total_years) - 1) * 100
    
    print(f"\nBuy & Hold Return: {buy_hold_return}%")
    print(f"Buy & Hold Annualized: {buy_hold_annualized}%")
    print(f"Strategy vs Buy & Hold: {xirr_value * 100 - buy_hold_annualized}% difference")

# ----------------------------
# Trade Analysis
# ----------------------------
print(f"\n{'='*50}")
print("TRADE ANALYSIS")
print(f"{'='*50}")

buy_trades = [h for h in portfolio['history'] if h[1] == 'Buy']
sell_trades = [h for h in portfolio['history'] if h[1] == 'Sell']

print(f"Buy Trades: {len(buy_trades)}")
print(f"Sell Trades: {len(sell_trades)}")

if buy_trades:
    strong_buys = [h for h in buy_trades if len(h) > 4 and h[4] == 'Strong']
    moderate_buys = [h for h in buy_trades if len(h) > 4 and h[4] == 'Moderate']
    print(f"  - Strong Buys: {len(strong_buys)}")
    print(f"  - Moderate Buys: {len(moderate_buys)}")

print(f"\nFinal Holdings: {portfolio['units']} units")
print(f"Final Cash: ₹{portfolio['cash']}")

# Show recent trades
if portfolio['history']:
    print(f"\nRecent Trades:")
    for h in portfolio['history'][-5:]:  # Show last 5 trades
        date, action, units, price = h[:4]
        trade_type = h[4] if len(h) > 4 else "N/A"
        units_val = float(units) if hasattr(units, '__iter__') and not isinstance(units, str) else units
        price_val = float(price) if hasattr(price, '__iter__') and not isinstance(price, str) else price
        print(f"  {date.strftime('%Y-%m-%d')}: {action} {units_val} units at ₹{price_val} ({trade_type})")

# ----------------------------
# Additional Statistics
# ----------------------------
print(f"\n{'='*50}")
print("ADDITIONAL STATISTICS")
print(f"{'='*50}")

if len(cash_flows) > 1:
    total_invested = sum(abs(cf) for cf in cash_flows if cf < 0)
    total_returned = sum(cf for cf in cash_flows if cf > 0)
    print(f"Total Invested: ₹{total_invested}")
    print(f"Total Returned: ₹{total_returned}")
    print(f"Net Cash Flow: ₹{total_returned - total_invested}")

# Price statistics
print(f"\nPrice Statistics:")
print(f"Starting Price: ₹{close_prices[0]}")
print(f"Ending Price: ₹{close_prices[-1]}")
print(f"Price Change: {((close_prices[-1] / close_prices[0]) - 1) * 100}%")
print(f"Max Price: ₹{max(close_prices)}")
print(f"Min Price: ₹{min(close_prices)}")

def calculate_backtest(data, initial_capital, sell_pct, interest_rate):
    """
    Performs a stock backtest and returns portfolio details.
    """
    
    # Calculate DMAs (ensure this matches the logic in your app)
    data['30DMA'] = data['Close'].rolling(window=30).mean()
    data['50DMA'] = data['Close'].rolling(window=50).mean()
    data['200DMA'] = data['Close'].rolling(window=200).mean()

    # Backtesting Logic (Keep your original logic from here)
    data['buy_signal'] = (data['30DMA'] > data['50DMA']) & (data['50DMA'] > data['200DMA'])
    data['sell_signal'] = (data['30DMA'] < data['50DMA']) | (data['50DMA'] < data['200DMA'])

    # Initialize portfolio
    portfolio = {
        'cash': initial_capital,
        'units': 0,
        'history': []
    }
    cash_flows = [initial_capital]

    # ... (Your original backtesting loop)

    # Return the portfolio and cash flows
    return portfolio, cash_flows

# Example of how to use this function locally
if __name__ == "__main__":
    ticker = "0P0001BAYU.BO"
    start_date = "2024-01-01"
    end_date = "2025-01-01"
    initial_capital = 100000
    sell_pct = 0.05
    interest_rate = 0.08

    data = yf.download(ticker, start=start_date, end=end_date)
    if not data.empty:
        portfolio, cash_flows = calculate_backtest(data, initial_capital, sell_pct, interest_rate)
        print("Backtest finished.")
        # ... (Your original print statements)
