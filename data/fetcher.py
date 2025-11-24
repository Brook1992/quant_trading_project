import yfinance as yf
import pandas as pd
from logger_config import log # Import the centralized logger

def fetch_data(ticker: str, start_date: str, end_date: str) -> tuple[pd.DataFrame, str]:
    """
    Fetches historical stock data and company name from Yahoo Finance.
    Returns a tuple containing the DataFrame and the company name.
    """
    log.info(f"--- Fetching stock data for {ticker} ---")
    log.info(f"URL (conceptual): Yahoo Finance API")
    log.info(f"Request Parameters: ticker={ticker}, start_date={start_date}, end_date={end_date}")
    
    try:
        stock = yf.Ticker(ticker)
        company_name = stock.info.get('longName', ticker) # Safely get company name, default to ticker
        
        data = stock.history(start=start_date, end=end_date)
        
        if data.empty:
            log.warning(f"No data found for ticker {ticker} from {start_date} to {end_date}.")
            log.info("--- Stock data fetch end ---")
            return pd.DataFrame(), company_name
        
        log.info(f"Successfully fetched {len(data)} rows of data for {ticker} ({company_name}).")
        log.info("--- Stock data fetch end ---")
        return data, company_name
    except Exception as e:
        log.error(f"Error fetching data for {ticker}: {e}")
        log.info("--- Stock data fetch end ---")
        return pd.DataFrame(), ticker # Return ticker as name on error

if __name__ == '__main__':
    # Example usage:
    ticker_symbol = 'AAPL'
    start = '2020-01-01'
    end = '2023-01-01'
    
    stock_data, company_name = fetch_data(ticker_symbol, start_date=start, end_date=end)
    
    if not stock_data.empty:
        print(f"\nFetch successful for {company_name}. See logs for details.")
        print("Head of data:")
        print(stock_data.head())
