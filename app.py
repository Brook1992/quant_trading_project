import streamlit as st # 导入 Streamlit 库, 用于创建Web应用
import pandas as pd     # 导入 Pandas 库, 用于数据处理和分析 (DataFrame)
from datetime import date, datetime # 导入日期和时间处理模块
import os               # 导入 OS 模块, 用于操作系统交互, 如文件路径操作
import io               # 导入 IO 模块, 用于处理流数据, 如将图表保存到内存
import base64           # 导入 base64 模块, 用于编码/解码数据, 以便在HTML中嵌入图片
import json             # 导入 json 模块, 用于将字典转换为JSON字符串

# Import project modules (导入项目内部模块)
from data.fetcher import fetch_data                 # 从 data.fetcher 导入 fetch_data 函数, 用于获取股票数据
from data.database import save_report_to_db         # 从 data.database 导入 save_report_to_db 函数
from strategies.sma_crossover import generate_signals # 从 strategies.sma_crossover 导入 generate_signals 函数, 用于生成交易信号
from backtest.engine import run_backtest             # 从 backtest.engine 导入 run_backtest 函数, 用于执行回测引擎
from main import plot_results                       # 从 main 导入 plot_results 函数, 复用其绘图功能

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

adx_threshold = st.sidebar.number_input(
    "ADX 阈值 (ADX Threshold)", # ADX阈值输入框标签
    min_value=0, max_value=50, value=25, step=1, # 最小值、最大值、默认值、步长
    help="""ADX (Average Directional Index) 阈值。当ADX低于此值时，策略不进行交易，以避免盘整市场。
          (ADX threshold. Strategy avoids trading in sideways markets when ADX is below this value.)"""
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
                signals_data = generate_signals(stock_data, short_window=short_window, long_window=long_window, adx_threshold=adx_threshold) # 调用函数生成交易信号
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

                # 5. Save the report to the database (保存报告到数据库)
                st.write(f"**5. 保存回测报告 (Saving Backtest Report)...**")
                
                # Convert plot to a base64 string for DB storage
                buf = io.BytesIO()
                fig.savefig(buf, format='png', bbox_inches='tight')
                chart_image_str = base64.b64encode(buf.getvalue()).decode()
                
                # Gather strategy parameters into a dictionary
                strategy_params = {
                    "short_window": short_window,
                    "long_window": long_window,
                    "adx_threshold": adx_threshold,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "initial_capital": initial_capital
                }
                
                # The 'stats' dictionary is already our performance metrics dict
                
                # Save the complete report to the database
                save_report_to_db(ticker, company_name, strategy_params, stats, chart_image_str)
                st.success(f"回测报告已成功保存至数据库。(Report successfully saved to database.)")

else:
    st.info("请在左侧配置参数并点击 '运行回测'。(Please configure the parameters on the left and click 'Run Backtest'.)") # 默认提示信息，指导用户操作
