import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger_config import log
from data.database import get_prices_from_db, save_prices_to_db, get_latest_date_from_db

def fetch_data(ticker: str, start_date: str, end_date: str) -> tuple[pd.DataFrame, str]:
    """
    Fetches historical stock data and company name, prioritizing the local database.
    If data is missing, it fetches from Yahoo Finance and updates the database.
    """
    log.info(f"--- Data request for {ticker} from {start_date} to {end_date} ---")
    
    # 1. Try to fetch all data from the database first
    data_from_db = get_prices_from_db(ticker, start_date, end_date)
    # Ensure data from DB is tz-naive for consistent comparisons
    if not data_from_db.empty and pd.api.types.is_datetime64_any_dtype(data_from_db.index) and data_from_db.index.tz is not None:
        data_from_db.index = data_from_db.index.tz_localize(None)
    
    # Check if the data from DB is complete
    db_is_complete = False
    if not data_from_db.empty:
        # Ensure comparison date is tz-naive
        comparison_end_date = pd.to_datetime(end_date).tz_localize(None) - pd.Timedelta(days=1)
        if data_from_db.index.max() >= comparison_end_date:
            db_is_complete = True

    if db_is_complete:
        log.info(f"Found complete data for {ticker} in the local database.")
        # We still need the company name, let's fetch it quickly. A better implementation might cache this too.
        try:
            company_name = yf.Ticker(ticker).info.get('longName', ticker)
        except Exception:
            company_name = ticker # Default to ticker on error
        return data_from_db, company_name

    # 2. If data is not complete, determine what's missing
    latest_date_in_db = get_latest_date_from_db(ticker)
    fetch_start_date_str = latest_date_in_db if latest_date_in_db else start_date
    if latest_date_in_db:
         # Fetch data from the day after the last recorded date, ensuring tz-naive for conversion
         fetch_start_date_dt = pd.to_datetime(latest_date_in_db).tz_localize(None) + timedelta(days=1)
         fetch_start_date_str = fetch_start_date_dt.strftime('%Y-%m-%d')

    log.info(f"Local data for {ticker} is incomplete. Fetching new data from yfinance starting from {fetch_start_date_str}.")
    
    # 3. Fetch new data from yfinance
    try:
        stock = yf.Ticker(ticker)
        company_name = stock.info.get('longName', ticker)
        
        # Fetching a slightly larger range to be safe
        new_data = stock.history(start=fetch_start_date_str, end=end_date)
        
        # IMPORTANT: Localize yfinance data index to tz-naive before saving/processing
        if not new_data.empty and new_data.index.tz is not None:
            new_data.index = new_data.index.tz_localize(None)
        
        if new_data.empty:
            log.warning(f"No new data found for {ticker} from yfinance.")
        else:
            # 4. Save the new data to the database
            save_prices_to_db(ticker, new_data)
            
        # 5. Retrieve the complete, combined data from the database
        final_data = get_prices_from_db(ticker, start_date, end_date)
        # Ensure final data is tz-naive
        if not final_data.empty and final_data.index.tz is not None:
            final_data.index = final_data.index.tz_localize(None)

        log.info("--- Data request fulfilled ---")
        return final_data, company_name

    except Exception as e:
        log.error(f"Error fetching data for {ticker} from yfinance: {e}")
        log.info("--- Data request fulfilled with error ---")
        return pd.DataFrame(), ticker # Return ticker as name on error

if __name__ == '__main__':
    # Example usage:
    ticker_symbol = 'NVDA' # Using a different ticker to test
    start = '2022-01-01'
    end = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n--- First fetch for {ticker_symbol} ---")
    stock_data, company_name = fetch_data(ticker_symbol, start_date=start, end_date=end)
    if not stock_data.empty:
        print(f"Fetch successful for {company_name}. Data rows: {len(stock_data)}")
        print("Head of data:")
        print(stock_data.head())
    
    print(f"\n--- Second fetch for {ticker_symbol} (should be faster and from DB) ---")
    stock_data, company_name = fetch_data(ticker_symbol, start_date=start, end_date=end)
    if not stock_data.empty:
        print(f"Fetch successful for {company_name}. Data rows: {len(stock_data)}")
        print("Tail of data:")
        print(stock_data.tail())
