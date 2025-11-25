import sqlite3
import pandas as pd
import sys
import os
from datetime import datetime

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger_config import log

DB_PATH = 'quant_data.db'

def init_db():
    """
    Initializes the database and creates tables if they don't exist.
    """
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # Create stock_prices table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS stock_prices (
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                PRIMARY KEY (ticker, date)
            )
        ''')

        # Create company_info table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS company_info (
                ticker TEXT PRIMARY KEY,
                company_name TEXT NOT NULL
            )
        ''')

        # Create backtest_reports table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS backtest_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                company_name TEXT,
                run_timestamp TEXT NOT NULL,
                strategy_params TEXT NOT NULL,
                performance_metrics TEXT NOT NULL,
                chart_image TEXT NOT NULL
            )
        ''')
        
        con.commit()
        log.info(f"Database initialized successfully at '{DB_PATH}'.")
    except sqlite3.Error as e:
        log.error(f"Database initialization error: {e}")
    finally:
        if con:
            con.close()

def save_prices_to_db(ticker: str, data: pd.DataFrame):
    """
    Saves a DataFrame of stock prices to the database.
    """
    if data.empty:
        return
        
    try:
        con = sqlite3.connect(DB_PATH)
        df_to_save = data.copy()
        df_to_save['ticker'] = ticker
        
        df_to_save.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low', 
            'Close': 'close', 'Volume': 'volume'
        }, inplace=True)
        
        df_to_save.index.name = 'date'
        df_to_save.reset_index(inplace=True)
        
        columns_to_save = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
        df_to_save = df_to_save[columns_to_save]
        
        df_to_save.to_sql('stock_prices', con, if_exists='append', index=False)
        log.info(f"Saved {len(df_to_save)} rows of price data for {ticker} to the database.")
    except Exception as e:
        log.error(f"Error saving price data for {ticker} to database: {e}")
    finally:
        if con:
            con.close()

def get_prices_from_db(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Retrieves stock prices from the database for a given ticker and date range.
    """
    try:
        con = sqlite3.connect(DB_PATH)
        query = f"""
            SELECT date, open, high, low, close, volume 
            FROM stock_prices 
            WHERE ticker = ? AND date BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, con, params=(ticker, start_date, end_date))
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df.dropna(subset=['date'], inplace=True)

            if pd.api.types.is_datetime64_any_dtype(df['date']) and df['date'].dt.tz is not None:
                df['date'] = df['date'].dt.tz_localize(None)

            df.set_index('date', inplace=True)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            df.rename(columns={
                'open': 'Open', 'high': 'High', 'low': 'Low', 
                'close': 'Close', 'volume': 'Volume'
            }, inplace=True)
            log.info(f"Retrieved {len(df)} rows for {ticker} from local database.")
        return df
    except Exception as e:
        log.error(f"Error getting prices for {ticker} from database: {e}")
        return pd.DataFrame()
    finally:
        if con:
            con.close()

def get_latest_date_from_db(ticker: str) -> str | None:
    """
    Gets the latest date for which data is available for a given ticker.
    """
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT MAX(date) FROM stock_prices WHERE ticker = ?", (ticker,))
        result = cur.fetchone()[0]
        return result
    except Exception as e:
        log.error(f"Error getting latest date for {ticker}: {e}")
        return None
    finally:
        if con:
            con.close()

def save_report_to_db(ticker: str, company_name: str, params: dict, metrics: dict, chart_image: str):
    """
    Saves a complete backtest report to the database.
    """
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        import json
        params_json = json.dumps(params)
        metrics_json = json.dumps(metrics)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute('''
            INSERT INTO backtest_reports (ticker, company_name, run_timestamp, strategy_params, performance_metrics, chart_image)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ticker, company_name, timestamp, params_json, metrics_json, chart_image))
        
        con.commit()
        log.info(f"Successfully saved backtest report for {ticker} to the database.")
    except Exception as e:
        log.error(f"Error saving report for {ticker} to database: {e}")
    finally:
        if con:
            con.close()

def get_all_reports_from_db() -> pd.DataFrame:
    """
    Retrieves all backtest reports from the database.
    """
    try:
        con = sqlite3.connect(DB_PATH)
        query = "SELECT id, ticker, company_name, run_timestamp, strategy_params, performance_metrics, chart_image FROM backtest_reports ORDER BY run_timestamp DESC"
        df = pd.read_sql_query(query, con)
        log.info(f"Retrieved {len(df)} reports from the database.")
        return df
    except Exception as e:
        log.error(f"Error getting reports from database: {e}")
        return pd.DataFrame()
    finally:
        if con:
            con.close()

if __name__ == '__main__':
    print("Initializing the database...")
    init_db()
    print("Database setup complete. You should see a 'quant_data.db' file.")
