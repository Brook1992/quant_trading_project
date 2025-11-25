import pandas as pd
import numpy as np
import pandas_ta as ta # 导入 pandas_ta 库用于计算技术指标
from llm.gemini_service import get_sentiment # 导入新的服务
from logger_config import log # 导入集中的日志记录器

# --- Mock News Headlines ---
# In a real-world scenario, you would fetch these from a news API
mock_news = {
    '2018-03-15': "AAPL supplier reports record chip production, hinting at strong iPhone sales.", # Positive
    '2018-08-05': "Trade tensions with China escalate, threatening AAPL's supply chain.", # Negative
    '2019-11-20': "AAPL unveils groundbreaking new M-series chip to rave reviews.", # Positive
    '2020-09-01': "Analysts downgrade AAPL stock citing saturation in the smartphone market.", # Negative
    '2021-05-10': "AAPL announces 100 billion dollar stock buyback program.", # Positive
    '2021-05-24': "Reports of production cuts for iPhone 14 surface amid demand fears.", # Negative
}

def generate_signals(data: pd.DataFrame, short_window: int, long_window: int, adx_threshold: int = 25) -> pd.DataFrame:
    """
    为SMA交叉策略生成交易信号，并通过新闻头条的情感分析进行增强，并加入ADX趋势过滤器。
    参数:
        data (pd.DataFrame): 包含 'Open', 'High', 'Low', 'Close' 列的股票数据。
        short_window (int): 短期移动平均线的周期。
        long_window (int): 长期移动平均线的周期。
        adx_threshold (int): ADX指标的阈值。ADX低于此值时不进行交易。
    返回:
        pd.DataFrame: 包含交易信号和指标的DataFrame。
    """
    if not all(col in data.columns for col in ['Open', 'High', 'Low', 'Close']):
        raise ValueError("Input DataFrame must have 'Open', 'High', 'Low', 'Close' columns for ADX calculation.")
    if short_window >= long_window:
        raise ValueError("Short window must be smaller than long window.")

    signals = data.copy()
    signals['short_mavg'] = signals['Close'].rolling(window=short_window, min_periods=1).mean()
    signals['long_mavg'] = signals['Close'].rolling(window=long_window, min_periods=1).mean()

    # Calculate ADX (计算ADX指标)
    # ADX通常需要 'High', 'Low', 'Close' 列
    adx = ta.adx(signals['High'], signals['Low'], signals['Close'], append=True)
    signals['ADX'] = adx[f'ADX_14'] # 默认周期为14，取ADX值

    # Create a signal when the short moving average crosses the long moving average
    signals['signal'] = 0.0
    signals.loc[signals.index[short_window:], 'signal'] = np.where(
        signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0
    )

    # Generate trading orders by taking the difference of the signal
    signals['positions'] = signals['signal'].diff()

    # --- ADX Trend Filter (ADX趋势过滤器) ---
    # 如果ADX低于阈值，则将交易信号置为0，避免在盘整市场中交易
    signals.loc[signals['ADX'] < adx_threshold, 'positions'] = 0.0
    log.info(f"ADX filter applied with threshold: {adx_threshold}.")

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
