import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import io
import base64

# Import project modules
from data.fetcher import fetch_data
from strategies.sma_crossover import generate_signals
from backtest.engine import run_backtest
from main import plot_results # We will reuse the plotting function

# --- Utility Function to Save Report ---
def save_report_to_html(stats: dict, fig, ticker: str) -> str:
    """
    Saves the backtest results to a ticker-specific HTML file.
    New results are prepended to the file's body to show the latest first.
    """
    report_dir = "backtest_reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    # Filename is now just the ticker
    filepath = os.path.join(report_dir, f"{ticker}.html")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. --- Create the HTML for the new entry ---
    # Convert plot to a base64 string
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    img_str = base64.b64encode(buf.getvalue()).decode()
    img_html = f'<img src="data:image/png;base64,{img_str}" alt="Backtest Chart" style="width:100%;">'

    # Format stats into an HTML table for the collapsible content
    stats_html = "<table><tr><th>Metric</th><th>Value</th></tr>"
    stats_map = {
        "最终资产 (Final Portfolio Value)": f"${stats['final_portfolio_value']:,.2f}",
        "总收益率 (Total Return)": f"{stats['total_return_pct']:.2f}%",
        "夏普比率 (Sharpe Ratio)": f"{stats['sharpe_ratio']:.2f}",
        "最大回撤 (Max Drawdown)": f"{stats['max_drawdown_pct']:.2f}%",
        "总交易次数 (Total Trades)": f"{stats['total_trades']}",
        "胜率 (Win Rate)": f"{stats['win_rate_pct']:.2f}%",
        "盈亏比 (Profit/Loss Ratio)": f"{stats['profit_loss_ratio']:.2f}"
    }
    for key, value in stats_map.items():
        stats_html += f"<tr><td>{key}</td><td>{value}</td></tr>"
    stats_html += "</table>"
    
    # Create the enhanced summary with key metrics
    summary_kpis = f"""
    <div class="summary-grid">
        <span class="summary-time"><strong>Run at:</strong> {timestamp}</span>
        <span class="summary-item"><strong>Return:</strong> {stats['total_return_pct']:.2f}%</span>
        <span class="summary-item"><strong>Sharpe:</strong> {stats['sharpe_ratio']:.2f}</span>
        <span class="summary-item"><strong>Drawdown:</strong> {stats['max_drawdown_pct']:.2f}%</span>
        <span class="summary-item"><strong>Win Rate:</strong> {stats['win_rate_pct']:.2f}%</span>
    </div>
    """

    # Create the collapsible HTML block for this specific backtest run
    new_entry_html = f"""
    <details>
        <summary>{summary_kpis}</summary>
        <div class="content">
            <h3>Performance Metrics</h3>
            {stats_html}
            <h3>Equity Curve & Trades</h3>
            {img_html}
        </div>
    </details>
    """

    # 2. --- Read existing file or create a new one ---
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Insert the new entry right after the main header
        insertion_point = f"<h1>Backtest Report for {ticker}</h1>"
        new_content = content.replace(insertion_point, f"{insertion_point}\n{new_entry_html}")
    else:
        # Create the HTML file from scratch
        new_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report for {ticker}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; background-color: #f9f9f9; }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        details {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px; overflow: hidden; }}
        summary {{ background-color: #f7f7f7; padding: 12px 16px; cursor: pointer; font-weight: bold; outline: none; }}
        summary:hover {{ background-color: #efefef; }}
        details[open] summary {{ border-bottom: 1px solid #ddd; }}
        .content {{ padding: 16px; background-color: #fff; }}
        h3 {{ color: #333; margin-top: 0; }}
        table {{ border-collapse: collapse; width: 60%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #e0e0e0; padding: 10px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: 600; }}
        img {{ max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .summary-grid {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }}
        .summary-time {{ flex-grow: 1; }}
        .summary-item {{ margin-left: 20px; font-size: 0.9em; color: #555; }}
        .summary-item strong {{ color: #000; }}
    </style>
</head>
<body>
    <h1>Backtest Report for {ticker}</h1>
    {new_entry_html}
</body>
</html>
        """

    # 3. --- Write the final content back to the file ---
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return filepath

# --- Page Configuration ---
st.set_page_config(
    page_title="量化交易回测平台 (Quantitative Trading Backtest Platform)",
    page_icon="📈",
    layout="wide"
)

# --- Sidebar for Inputs ---
st.sidebar.header("⚙️ 参数配置 (Configuration)")

# Predefined list of popular tickers
popular_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "BRK-B", "JPM", "V", "PG"]

ticker = st.sidebar.selectbox(
    "股票代码 (Ticker)", 
    popular_tickers,
    index=0, # Default to AAPL
    help="""从列表中选择一个股票代码，或在输入框中输入自定义代码。
          (Select a ticker from the list, or type a custom one in the text input below.)"""
)

# Optional: Allow user to input a custom ticker if not in the list (or always)
custom_ticker_option = st.sidebar.checkbox("输入自定义股票代码 (Enter Custom Ticker)", value=False)
if custom_ticker_option:
    custom_ticker = st.sidebar.text_input(
        "自定义股票代码 (Custom Ticker)",
        "",
        help="""如果您想回测列表中未包含的股票，请在此处输入。"""
    )
    if custom_ticker:
        ticker = custom_ticker

start_date = st.sidebar.date_input(
    "开始日期 (Start Date)", 
    date(2018, 1, 1)
)

end_date = st.sidebar.date_input(
    "结束日期 (End Date)", 
    date(2023, 1, 1)
)

short_window = st.sidebar.number_input(
    "短期均线窗口 (Short Window)", 
    min_value=5, max_value=100, value=40, step=1,
    help="用于计算短期简单移动平均线的周期天数。"
)

long_window = st.sidebar.number_input(
    "长期均线窗口 (Long Window)", 
    min_value=20, max_value=250, value=100, step=1,
    help="用于计算长期简单移动平均线的周期天数。"
)

initial_capital = st.sidebar.number_input(
    "初始资金 (Initial Capital)", 
    min_value=1000, max_value=10000000, value=100000, step=1000
)

# --- Main Content ---
st.title("📈 量化交易回测平台")
st.caption("Quantitative Trading Backtest Platform")

if st.sidebar.button("🚀 运行回测 (Run Backtest)"):
    if not ticker:
        st.error("请输入一个股票代码。(Please enter a ticker.)")
    elif short_window >= long_window:
        st.error("短期均线窗口必须小于长期均线窗口。(Short window must be smaller than long window.)")
    else:
        with st.spinner("正在执行回测... (Running backtest...)"):
            # 1. Fetch Data
            st.write(f"**1. 获取数据 (Fetching Data) for {ticker}...**")
            stock_data = fetch_data(ticker, str(start_date), str(end_date))

            if stock_data.empty:
                st.error("无法获取该股票代码的数据，请检查代码或日期范围。")
            else:
                st.success(f"成功获取 {len(stock_data)} 天的数据。(Successfully fetched {len(stock_data)} days of data.)")
                
                # 2. Generate Signals (with LLM)
                st.write(f"**2. 生成交易信号 (Generating Signals)...**")
                # Note: Sentiment analysis logs will print to the console where streamlit is running
                signals_data = generate_signals(stock_data, short_window=short_window, long_window=long_window)
                st.success("交易信号生成完毕。(Trading signals generated.)")
                
                # 3. Run Backtest
                st.write(f"**3. 执行回测模拟 (Running Backtest Simulation)...**")
                portfolio, stats = run_backtest(signals_data, initial_capital=initial_capital)
                st.success("回测模拟完成。(Backtest simulation complete.)")

                # 4. Display Results
                st.subheader("📊 回测性能指标 (Backtest Performance Metrics)")
                
                # Display metrics in two rows
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("最终资产 (Final Value)", f"${stats['final_portfolio_value']:,.2f}")
                col2.metric("总收益率 (Total Return)", f"{stats['total_return_pct']:.2f}%")
                col3.metric("夏普比率 (Sharpe Ratio)", f"{stats['sharpe_ratio']:.2f}")
                col4.metric("最大回撤 (Max Drawdown)", f"{stats['max_drawdown_pct']:.2f}%")

                col5, col6, col7, _ = st.columns(4)
                col5.metric("总交易次数 (Total Trades)", f"{stats['total_trades']}")
                col6.metric("胜率 (Win Rate)", f"{stats['win_rate_pct']:.2f}%")
                col7.metric("盈亏比 (P/L Ratio)", f"{stats['profit_loss_ratio']:.2f}")

                st.subheader("📈 交易图表 (Charts)")
                fig = plot_results(portfolio, signals_data, ticker)
                st.pyplot(fig)

                # 5. Save the report
                st.write(f"**4. 保存回测报告 (Saving Backtest Report)...**")
                report_path = save_report_to_html(stats, fig, ticker)
                st.success(f"回测报告已保存至: (Report saved to:) `{report_path}`")

else:
    st.info("请在左侧配置参数并点击 '运行回测'。(Please configure the parameters on the left and click 'Run Backtest'.)")
