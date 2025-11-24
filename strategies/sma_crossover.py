import pandas as pd
import numpy as np
from llm.gemini_service import get_sentiment # Import the new service
from logger_config import log # Import the centralized logger

# --- Mock News Headlines ---
# In a real-world scenario, you would fetch these from a news API
mock_news = {
    '2018-03-15': "AAPL supplier reports record chip production, hinting at strong iPhone sales.", # Positive
    '2018-08-05': "Trade tensions with China escalate, threatening AAPL's supply chain.", # Negative
    '2019-11-20': "AAPL unveils groundbreaking new M-series chip to rave reviews.", # Positive
    '2020-09-01': "Analysts downgrade AAPL stock citing saturation in the smartphone market.", # Negative
    '2021-05-10': "AAPL announces 100 billion dollar stock buyback program.", # Positive
    '2022-10-25': "Reports of production cuts for iPhone 14 surface amid demand fears.", # Negative
}

def generate_signals(data: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """
    Generates trading signals for an SMA Crossover strategy, enhanced with
    sentiment analysis from news headlines.
    """
    if 'Close' not in data.columns:
        raise ValueError("Input DataFrame must have a 'Close' column.")
    if short_window >= long_window:
        raise ValueError("Short window must be smaller than long window.")

    signals = data.copy()
    signals['short_mavg'] = signals['Close'].rolling(window=short_window, min_periods=1).mean()
    signals['long_mavg'] = signals['Close'].rolling(window=long_window, min_periods=1).mean()

    # Create a signal when the short moving average crosses the long moving average
    signals['signal'] = 0.0
    signals.loc[signals.index[short_window:], 'signal'] = np.where(
        signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0
    )

    # Generate trading orders by taking the difference of the signal
    signals['positions'] = signals['signal'].diff()

    # --- LLM Integration ---
    # Add mock news to the dataframe
    signals['headlines'] = signals.index.strftime('%Y-%m-%d').map(mock_news)

    # Identify rows where a buy signal and a headline co-occur
    buy_signals_with_news = signals[(signals['positions'] == 1.0) & (signals['headlines'].notna())].index

    # Apply sentiment filter only on these specific rows
    for idx in buy_signals_with_news:
        headline = signals.loc[idx, 'headlines']
        log.info(f"Analyzing news for {idx.date()}: '{headline}'")
        sentiment = get_sentiment(headline)
        log.info(f"Sentiment for {idx.date()}: {sentiment}")

        # If sentiment is negative, cancel the buy signal
        if sentiment == 'Negative':
            signals.loc[idx, 'positions'] = 0.0
            log.info(f"-> Negative sentiment detected. Suppressing BUY signal for {idx.date()}.")

    log.info("Successfully generated trading signals with sentiment analysis.")
    return signals
