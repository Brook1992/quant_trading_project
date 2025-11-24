import pandas as pd
import numpy as np

def run_backtest(data: pd.DataFrame, initial_capital: float = 100000.0):
    """
    Runs a vectorized backtest on the trading strategy.

    Args:
        data (pd.DataFrame): DataFrame containing 'Close' prices and 'positions' signals
                             (+1 for buy, -1 for sell).
        initial_capital (float): The starting capital for the backtest.

    Returns:
        pd.DataFrame: A DataFrame representing the portfolio's value over time.
        dict: A dictionary containing key performance metrics.
    """
    if 'Close' not in data.columns or 'positions' not in data.columns:
        raise ValueError("Input DataFrame must have 'Close' and 'positions' columns.")

    portfolio = pd.DataFrame(index=data.index)
    portfolio['close'] = data['Close']
    portfolio['positions'] = data['positions']

    # Calculate the number of shares to trade
    # This is a simplified model: we invest the full capital on a buy signal
    positions_df = portfolio['positions'].to_frame()
    positions_df['cash_change'] = -positions_df['positions'] * portfolio['close']
    
    # Simulate portfolio holdings
    portfolio['cash'] = initial_capital + positions_df['cash_change'].cumsum()
    
    # Calculate the number of shares held
    # Note: .ffill() propagates the last valid observation forward
    portfolio['shares'] = portfolio['positions'].cumsum().ffill()
    
    # Calculate the market value of the equity holdings
    portfolio['holdings_value'] = portfolio['shares'] * portfolio['close']
    
    # Calculate total portfolio value
    portfolio['total_value'] = portfolio['cash'] + portfolio['holdings_value']
    
    # Calculate portfolio returns
    portfolio['returns'] = portfolio['total_value'].pct_change().fillna(0)

    print("Backtest simulation complete.")

    # --- Performance Metrics ---
    total_return = (portfolio['total_value'][-1] / initial_capital) - 1
    
    # Calculate Sharpe Ratio (assuming risk-free rate is 0)
    # Using a 252-day trading year
    annualized_return = portfolio['returns'].mean() * 252
    annualized_std_dev = portfolio['returns'].std() * np.sqrt(252)
    sharpe_ratio = annualized_return / annualized_std_dev if annualized_std_dev != 0 else 0

    # Calculate Max Drawdown
    cumulative_returns = (1 + portfolio['returns']).cumprod()
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min()

    # --- Trade Analysis ---
    positions = portfolio['positions'].loc[portfolio['positions'] != 0]
    trades = []
    entry_price = 0
    entry_date = None

    for date, pos in positions.items():
        if pos == 1: # Entry
            if entry_price == 0:
                entry_price = portfolio.loc[date, 'close']
                entry_date = date
        elif pos == -1: # Exit
            if entry_price != 0:
                exit_price = portfolio.loc[date, 'close']
                profit = (exit_price - entry_price) / entry_price
                trades.append(profit)
                # Reset for next trade
                entry_price = 0
                entry_date = None
    
    total_trades = len(trades)
    if total_trades > 0:
        winning_trades = [t for t in trades if t > 0]
        losing_trades = [t for t in trades if t < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        average_profit = sum(winning_trades) / len(winning_trades) if len(winning_trades) > 0 else 0
        average_loss = abs(sum(losing_trades) / len(losing_trades)) if len(losing_trades) > 0 else 0
        profit_loss_ratio = average_profit / average_loss if average_loss > 0 else float('inf')
    else:
        win_rate = 0
        profit_loss_ratio = 0

    stats = {
        'initial_capital': initial_capital,
        'final_portfolio_value': portfolio['total_value'][-1],
        'total_return_pct': total_return * 100,
        'annualized_return': annualized_return,
        'annualized_std_dev': annualized_std_dev,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown_pct': max_drawdown * 100,
        'total_trades': total_trades,
        'win_rate_pct': win_rate * 100,
        'profit_loss_ratio': profit_loss_ratio,
    }

    return portfolio, stats

if __name__ == '__main__':
    # Example Usage
    price_data = pd.DataFrame({
        'Close': np.random.randn(252).cumsum() + 100
    }, index=pd.date_range(start='2022-01-01', periods=252))
    
    # Create dummy positions for testing
    price_data['positions'] = 0.0
    price_data.iloc[20, price_data.columns.get_loc('positions')] = 1.0  # Buy
    price_data.iloc[80, price_data.columns.get_loc('positions')] = -1.0 # Sell
    price_data.iloc[150, price_data.columns.get_loc('positions')] = 1.0 # Buy
    price_data.iloc[220, price_data.columns.get_loc('positions')] = -1.0# Sell

    portfolio_results, performance_stats = run_backtest(price_data, initial_capital=100000.0)

    print("\n--- Portfolio Simulation ---")
    print(portfolio_results.tail())

    print("\n--- Performance Stats ---")
    for key, value in performance_stats.items():
        print(f"{key.replace('_', ' ').title()}: {value:.2f}")
