import streamlit as st # 导入 Streamlit 库, 用于创建Web应用
import pandas as pd     # 导入 Pandas 库, 用于数据处理和分析 (DataFrame)
from datetime import date, datetime # 导入日期和时间处理模块
import os               # 导入 OS 模块, 用于操作系统交互, 如文件路径操作
import io               # 导入 IO 模块, 用于处理流数据, 如将图表保存到内存
import base64           # 导入 base64 模块, 用于编码/解码数据, 以便在HTML中嵌入图片

# Import project modules (导入项目内部模块)
from data.fetcher import fetch_data                 # 从 data.fetcher 导入 fetch_data 函数, 用于获取股票数据
from strategies.sma_crossover import generate_signals # 从 strategies.sma_crossover 导入 generate_signals 函数, 用于生成交易信号
from backtest.engine import run_backtest             # 从 backtest.engine 导入 run_backtest 函数, 用于执行回测引擎
from main import plot_results                       # 从 main 导入 plot_results 函数, 复用其绘图功能

# --- Utility Function to Save Report (保存报告的工具函数) ---
def save_report_to_html(stats: dict, fig, ticker: str, company_name: str) -> str:
    """
    功能: 将回测结果保存为特定股票的HTML报告文件。
    如果文件已存在, 新结果会预置(prepend)到文件主体顶部, 以显示最新的回测结果。
    参数:
        stats (dict): 回测统计数据字典。
        fig: Matplotlib 图表对象。
        ticker (str): 股票代码。
        company_name (str): 公司名称。
    返回:
        str: 保存的HTML文件路径。
    """
    report_dir = "backtest_reports" # 定义报告存储目录
    if not os.path.exists(report_dir):
        os.makedirs(report_dir) # 如果目录不存在, 则创建它

    # Filename is now just the ticker (报告文件名以股票代码命名)
    filepath = os.path.join(report_dir, f"{ticker}.html") # 构造完整的报告文件路径
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 获取当前时间戳

    # 1. --- Create the HTML for the new entry (为新报告条目创建HTML内容) ---
    # Convert plot to a base64 string (将Matplotlib图表转换为Base64编码字符串, 以便嵌入到HTML中)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight') # 将图表保存到内存缓冲区(buffer)为PNG格式
    img_str = base64.b64encode(buf.getvalue()).decode() # 将缓冲区内容编码为base64字符串
    img_html = f'<img src="data:image/png;base64,{img_str}" alt="Backtest Chart" style="width:100%;">' # 构建图片HTML标签

    # Format stats into an HTML table for the collapsible content (将统计数据格式化为HTML表格, 用于可折叠内容)
    stats_html = "<table><tr><th>Metric</th><th>Value</th></tr>" # 表格头部
    stats_map = { # 定义统计指标的中英文对照及格式
        "最终资产 (Final Portfolio Value)": f"${stats['final_portfolio_value']:,.2f}",
        "总收益率 (Total Return)": f"{stats['total_return_pct']:.2f}%",
        "夏普比率 (Sharpe Ratio)": f"{stats['sharpe_ratio']:.2f}",
        "最大回撤 (Max Drawdown)": f"{stats['max_drawdown_pct']:.2f}%",
        "总交易次数 (Total Trades)": f"{stats['total_trades']}",
        "胜率 (Win Rate)": f"{stats['win_rate_pct']:.2f}%",
        "盈亏比 (Profit/Loss Ratio)": f"{stats['profit_loss_ratio']:.2f}"
    }
    for key, value in stats_map.items():
        stats_html += f"<tr><td>{key}</td><td>{value}</td></tr>" # 遍历并添加表格行
    stats_html += "</table>" # 表格尾部
    
    # Create the enhanced summary with key metrics (创建包含关键指标的增强摘要)
    summary_kpis = f"""
    <div class="summary-grid">
        <span class="summary-time"><strong>Run at:</strong> {timestamp}</span>
        <span class="summary-item"><strong>Return:</strong> {stats['total_return_pct']:.2f}%</span>
        <span class="summary-item"><strong>Sharpe:</strong> {stats['sharpe_ratio']:.2f}</span>
        <span class="summary-item"><strong>Drawdown:</strong> {stats['max_drawdown_pct']:.2f}%</span>
        <span class="summary-item"><strong>Win Rate:</strong> {stats['win_rate_pct']:.2f}%</span>
    </div>
    """

    # Create the collapsible HTML block for this specific backtest run (为本次回测运行创建可折叠的HTML块)
    new_entry_html = f"""
    <details>
        <summary>{summary_kpis}</summary>
        <div class="content">
            <h3>Performance Metrics (性能指标)</h3>
            {stats_html}
            <h3>Equity Curve & Trades (净值曲线与交易)</h3>
            {img_html}
        </div>
    </details>
    """

    # 2. --- Read existing file or create a new one (读取现有文件或创建新文件) ---
    if os.path.exists(filepath): # 检查报告文件是否已存在
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read() # 读取现有文件内容
        
        # Insert the new entry right after the main header (在新报告头部后插入新条目)
        insertion_point_v1 = f"<h1>Backtest Report for {ticker} (回测报告)</h1>"
        insertion_point_v2 = f"<h1>Backtest Report for {company_name} ({ticker})</h1>"
        
        # Handle both old and new header formats for backward compatibility
        if insertion_point_v2 in content:
             new_content = content.replace(insertion_point_v2, f"{insertion_point_v2}\n{new_entry_html}")
        else:
             new_content = content.replace(insertion_point_v1, f"<h1>Backtest Report for {company_name} ({ticker})</h1>\n{new_entry_html}")
    else:
        # Create the HTML file from scratch (从头开始创建HTML文件)
        new_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report for {company_name} ({ticker})</title>
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
    <h1>Backtest Report for {company_name} ({ticker})</h1>
    {new_entry_html}
</body>
</html>
        """

    # 3. --- Write the final content back to the file (将最终内容写回文件) ---
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content) # 写入(覆盖)更新后的HTML内容
    
    return filepath # 返回生成的报告文件路径

# --- Page Configuration (页面配置) ---
st.set_page_config(
    page_title="量化交易回测平台 (Quantitative Trading Backtest Platform)", # 浏览器标签页标题
    page_icon="📈", # 浏览器标签页图标
    layout="wide" # 页面布局为宽屏模式
)

# --- Sidebar for Inputs (侧边栏输入区域) ---
st.sidebar.header("⚙️ 参数配置 (Configuration)") # 侧边栏标题: 参数配置

# Predefined list of popular tickers (预定义的常用股票代码列表)
popular_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "BRK-B", "JPM", "V", "PG"]

# 股票代码选择框 (Selectbox for Ticker)
ticker = st.sidebar.selectbox(
    "股票代码 (Ticker)", # 显示给用户的标签
    popular_tickers, # 可选列表
    index=0, # 默认选中第一个 (AAPL)
    help="""从列表中选择一个股票代码，或在输入框中输入自定义代码。
          (Select a ticker from the list, or type a custom one in the text input below.)"""
)

# Optional: Allow user to input a custom ticker if not in the list (or always) (可选: 允许用户输入自定义股票代码)
custom_ticker_option = st.sidebar.checkbox("输入自定义股票代码 (Enter Custom Ticker)", value=False) # 自定义代码复选框
if custom_ticker_option:
    custom_ticker = st.sidebar.text_input(
        "自定义股票代码 (Custom Ticker)", # 自定义代码输入框标签
        "", # 默认值为空
        help="""如果您想回测列表中未包含的股票，请在此处输入。""" # 帮助信息
    )
    if custom_ticker:
        ticker = custom_ticker # 如果输入了自定义代码, 则更新使用的股票代码

start_date = st.sidebar.date_input(
    "开始日期 (Start Date)", # 开始日期选择器标签
    date(2018, 1, 1) # 默认开始日期
)

end_date = st.sidebar.date_input(
    "结束日期 (End Date)", # 结束日期选择器标签
    date(2023, 1, 1) # 默认结束日期
)

short_window = st.sidebar.number_input(
    "短期均线窗口 (Short Window)", # 短期均线窗口输入框标签
    min_value=5, max_value=100, value=40, step=1, # 最小值、最大值、默认值、步长
    help="用于计算短期简单移动平均线的周期天数。" # 帮助信息
)

long_window = st.sidebar.number_input(
    "长期均线窗口 (Long Window)", # 长期均线窗口输入框标签
    min_value=20, max_value=250, value=100, step=1, # 最小值、最大值、默认值、步长
    help="用于计算长期简单移动平均线的周期天数。" # 帮助信息
)

initial_capital = st.sidebar.number_input(
    "初始资金 (Initial Capital)", # 初始资金输入框标签
    min_value=1000, max_value=10000000, value=100000, step=1000 # 最小值、最大值、默认值、步长
)

# --- Main Content (主内容区域) ---
st.title("📈 量化交易回测平台") # 页面主标题
st.caption("Quantitative Trading Backtest Platform") # 页面副标题

# 当点击侧边栏的 "运行回测" 按钮时执行以下代码块
if st.sidebar.button("🚀 运行回测 (Run Backtest)"):
    # 输入参数验证 (Input Parameter Validation)
    if not ticker:
        st.error("请输入一个股票代码。(Please enter a ticker.)") # 显示错误信息
    elif short_window >= long_window:
        st.error("短期均线窗口必须小于长期均线窗口。(Short window must be smaller than long window.)") # 显示错误信息
    else:
        # 使用 Streamlit 的 spinner (加载动画) 显示回测进度
        with st.spinner("正在执行回测... (Running backtest..."):
            # 1. Fetch Data (获取数据)
            st.write(f"**1. 获取数据 (Fetching Data) for {ticker}...**")
            stock_data, company_name = fetch_data(ticker, str(start_date), str(end_date)) # 调用函数获取股票数据

            if stock_data.empty: # 检查是否成功获取数据
                st.error("无法获取该股票代码的数据，请检查代码或日期范围。") # 如果数据为空, 显示错误信息
            else:
                st.success(f"成功获取 {company_name} ({ticker}) 在 {len(stock_data)} 天内的数据。(Successfully fetched {len(stock_data)} days of data for {company_name} ({ticker}).)") # 显示成功信息
                
                # 2. Generate Signals (with LLM) (生成交易信号 (包含LLM))
                st.write(f"**2. 生成交易信号 (Generating Signals)...**") # 提示用户正在生成信号
                # Note: Sentiment analysis logs will print to the console where streamlit is running (注意: 情感分析日志会打印到Streamlit运行的控制台)
                signals_data = generate_signals(stock_data, short_window=short_window, long_window=long_window) # 调用函数生成交易信号
                st.success("交易信号生成完毕。(Trading signals generated.)") # 显示成功信息
                
                # 3. Run Backtest (执行回测模拟)
                st.write(f"**3. 执行回测模拟 (Running Backtest Simulation)...**") # 提示用户正在执行回测
                portfolio, stats = run_backtest(signals_data, initial_capital=initial_capital) # 调用函数运行回测
                st.success("回测模拟完成。(Backtest simulation complete.)") # 显示成功信息

                # 4. Display Results (显示结果)
                st.subheader("📊 回测性能指标 (Backtest Performance Metrics)") # 子标题: 性能指标
                
                # Display metrics in two rows (在两行中显示关键指标)
                col1, col2, col3, col4 = st.columns(4) # 创建4列布局
                col1.metric("最终资产 (Final Value)", f"${stats['final_portfolio_value']:,.2f}") # 显示最终资产
                col2.metric("总收益率 (Total Return)", f"{stats['total_return_pct']:.2f}%") # 显示总收益率
                col3.metric("夏普比率 (Sharpe Ratio)", f"{stats['sharpe_ratio']:.2f}") # 显示夏普比率
                col4.metric("最大回撤 (Max Drawdown)", f"{stats['max_drawdown_pct']:.2f}%") # 显示最大回撤

                col5, col6, col7, _ = st.columns(4) # 创建4列布局 (忽略第四列)
                col5.metric("总交易次数 (Total Trades)", f"{stats['total_trades']}") # 显示总交易次数
                col6.metric("胜率 (Win Rate)", f"{stats['win_rate_pct']:.2f}%") # 显示胜率
                col7.metric("盈亏比 (P/L Ratio)", f"{stats['profit_loss_ratio']:.2f}") # 显示盈亏比

                st.subheader("📈 交易图表 (Charts)") # 子标题: 交易图表
                fig = plot_results(portfolio, signals_data, ticker, company_name) # 调用绘图函数生成图表
                st.pyplot(fig) # 在Streamlit应用中显示Matplotlib图表

                # 5. Save the report (保存报告)
                st.write(f"**4. 保存回测报告 (Saving Backtest Report)...**") # 提示用户正在保存报告
                report_path = save_report_to_html(stats, fig, ticker, company_name) # 调用函数保存报告到HTML文件
                st.success(f"回测报告已保存至: (Report saved to:) `{report_path}`") # 显示报告保存路径

else:
    st.info("请在左侧配置参数并点击 '运行回测'。(Please configure the parameters on the left and click 'Run Backtest'.)") # 默认提示信息，指导用户操作
