# Basic Quantitative Trading Project

This project is a simple, educational quantitative trading backtesting framework written in Python. It provides a foundational structure for fetching financial data, implementing a trading strategy, and evaluating its performance on historical data.

## Features

- **Modular Structure**: The code is organized into distinct modules for data fetching, strategy logic, and backtesting.
- **Data Fetching**: Downloads historical OHLCV (Open, High, Low, Close, Volume) data from Yahoo Finance.
- **Trading Strategy**: Implements a Simple Moving Average (SMA) Crossover strategy.
  - A **buy signal** is generated when the short-term moving average crosses above the long-term moving average.
  - A **sell signal** is generated when the short-term moving average crosses below the long-term moving average.
- **Backtesting Engine**: A vectorized backtester simulates the strategy's performance and calculates key metrics.
- **Visualization**: Plots the equity curve and the trading signals overlaid on the price chart.

## Project Structure

```
quant_trading_project/
│
├── data/
│   └── fetcher.py        # Module for fetching financial data
│
├── strategies/
│   └── sma_crossover.py  # Module for the SMA Crossover strategy logic
│
├── backtest/
│   └── engine.py         # Module for the backtesting simulation engine
│
├── main.py               # Main script to run the backtest and plot results
├── requirements.txt      # List of Python dependencies
└── README.md             # This file
```

## Setup and Installation

1.  **Clone the repository or download the source code.**

2.  **Navigate to the project directory:**
    ```sh
    cd quant_trading_project
    ```

3.  **Create a virtual environment (recommended):**
    ```sh
    python -m venv venv
    ```
    Activate it:
    - On Windows: `venv\Scripts\activate`
    - On macOS/Linux: `source venv/bin/activate`

4.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

## How to Run

To run the backtest, simply execute the `main.py` script from the project's root directory:

```sh
python main.py
```

The script will:
1.  Fetch the historical data for the configured ticker.
2.  Generate trading signals based on the SMA Crossover strategy.
3.  Run the backtest simulation.
4.  Print a summary of the performance metrics to the console.
5.  Display a plot showing the price, moving averages, buy/sell signals, and the portfolio's equity curve.

## Customization

You can easily customize the backtest parameters by editing the `Configuration` section in the `main.py` file:

```python
# --- Configuration ---
TICKER = 'AAPL'          # Stock ticker to backtest
START_DATE = '2018-01-01'  # Start date for historical data
END_DATE = '2023-01-01'    # End date for historical data
SHORT_WINDOW = 40        # Look-back period for the short SMA
LONG_WINDOW = 100        # Look-back period for the long SMA
INITIAL_CAPITAL = 100000.0 # Starting capital for the simulation
```

Feel free to change these values to test different assets, timeframes, or strategy parameters.
