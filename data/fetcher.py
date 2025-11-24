import yfinance as yf
import pandas as pd
from logger_config import log # Import the centralized logger

def fetch_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches historical stock data from Yahoo Finance.
    """
    log.info(f"--- Fetching stock data for {ticker} ---")
    log.info(f"URL (conceptual): Yahoo Finance API")
    log.info(f"Request Parameters: ticker={ticker}, start_date={start_date}, end_date={end_date}")
    
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            log.warning(f"No data found for ticker {ticker} from {start_date} to {end_date}.")
            log.info("--- Stock data fetch end ---")
            return pd.DataFrame()
        
        log.info(f"Successfully fetched {len(data)} rows of data for {ticker}.")
        log.info("--- Stock data fetch end ---")
        return data
    except Exception as e:
        log.error(f"Error fetching data for {ticker}: {e}")
        log.info("--- Stock data fetch end ---")
        return pd.DataFrame()

if __name__ == '__main__':
    # Example usage:
    ticker_symbol = 'AAPL'
    start = '2020-01-01'
    end = '2023-01-01'
    
    stock_data = fetch_data(ticker_symbol, start_date=start, end_date=end)
    
    if not stock_data.empty:
        print("\nFetch successful. See logs for details.")
        print("Head of data:")
        print(stock_data.head())
