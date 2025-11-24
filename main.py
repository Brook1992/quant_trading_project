# 导入 matplotlib.pyplot 库, 这是Python中用于绘图的主要库, 通常简写为 plt
# 作用类似于Java中的JFreeChart或前端的D3.js, Chart.js
import matplotlib.pyplot as plt
# 导入 matplotlib.style 库, 用于设置图表的样式, 比如主题(暗色、亮色)
import matplotlib.style as style
# 从 matplotlib.font_manager 模块导入 FontProperties 类, 用于处理和指定图表中使用的字体
from matplotlib.font_manager import FontProperties

# 从当前项目的其他模块(文件夹)中导入需要的函数
# 这类似于 Java 中的 `import com.myproject.data.fetcher.fetchData;`
# 或者 JavaScript/TypeScript 中的 `import { fetch_data } from './data/fetcher';`

# 从 data 目录的 fetcher.py 文件中导入 fetch_data 函数
from data.fetcher import fetch_data
# 从 strategies 目录的 sma_crossover.py 文件中导入 generate_signals 函数
from strategies.sma_crossover import generate_signals
# 从 backtest 目录的 engine.py 文件中导入 run_backtest 函数
from backtest.engine import run_backtest

# --- 定义绘图函数 ---
# def 是 Python 中定义函数的关键字
# portfolio: 'pd.DataFrame' 是类型提示(type hint), 表示 portfolio 参数期望是 pandas DataFrame 类型。这对代码可读性有好处, 但Python解释器本身不强制要求。
# 这类似于 TypeScript 中的 `function plot_results(portfolio: pd.DataFrame, ...)`
def plot_results(portfolio: 'pd.DataFrame', signals: 'pd.DataFrame', ticker: str):
    """
    这是一个函数文档字符串(docstring), 用来解释函数的作用。
    功能: 绘制回测结果图表, 标签同时支持中英文。
    这个版本直接从文件路径加载字体, 以修复可能的编码问题。
    """
    # --- 加载中文字体 ---
    # `try...except` 块用于异常处理, 类似于 Java/JavaScript 中的 `try...catch`
    try:
        # 定义中文字体(SimHei)在Windows系统中的常见路径
        font_path = 'C:/Windows/Fonts/SimHei.ttf'
        # 使用 FontProperties 加载指定路径和大小的字体, 用于图表中的中文显示
        chinese_font = FontProperties(fname=font_path, size=12)
        # 为图表主标题创建一个更大号的字体
        title_font = FontProperties(fname=font_path, size=18)
    except FileNotFoundError: # 如果在 try 块中发生 FileNotFoundError (文件未找到)异常
        # 打印一个警告信息到控制台
        print("Warning: SimHei.ttf font not found in C:/Windows/Fonts/. Chinese characters may not display correctly.")
        # 如果找不到指定的字体, 则回退到默认字体, 这可能导致中文显示为方框
        chinese_font = FontProperties(size=12)
        title_font = FontProperties(size=18)

    # 设置图表使用的样式/主题, 'seaborn-v0_8-darkgrid' 是一个深色网格背景的主题
    style.use('seaborn-v0_8-darkgrid')
    
    # 创建一个包含两个子图(ax1, ax2)的图表(fig)
    # plt.subplots(2, 1, ...) 表示创建一个2行1列的网格布局
    # figsize=(14, 12) 设置整个图表的尺寸(宽14英寸, 高12英寸)
    # gridspec_kw={'height_ratios': [3, 1]} 指定上下两个子图的高度比例为3:1
    # sharex=True 表示两个子图共享同一个X轴(即日期轴), 这样缩放或平移时会同步
    fig, (ax1, ax2) = plt.subplots(
        2, 1, 
        figsize=(14, 12), 
        gridspec_kw={'height_ratios': [3, 1]},
        sharex=True
    )
    # 为整个图表设置主标题
    # f'...' 是Python的f-string格式化字符串, 类似于JavaScript的模板字符串 `${}`
    # fontproperties=title_font 应用我们之前定义的大号中文字体
    fig.suptitle(f'SMA Crossover Backtest Results for {ticker} / {ticker} SMA交叉策略回测结果', fontproperties=title_font)

    # --- 第一个子图 (ax1): 绘制股价, 均线和买卖信号 ---
    # ax1.plot(...) 是在第一个子图上绘线
    # signals.index 是X轴数据(日期), signals['Close'] 是Y轴数据(收盘价)
    ax1.plot(signals.index, signals['Close'], label='Close Price / 收盘价', color='skyblue', linewidth=1.5)
    ax1.plot(signals.index, signals['short_mavg'], label='Short SMA / 短期均线', color='orange', linestyle='--', linewidth=1.2)
    ax1.plot(signals.index, signals['long_mavg'], label='Long SMA / 长期均线', color='purple', linestyle='--', linewidth=1.2)
    
    # 从信号数据中筛选出所有买入信号的行
    # signals['positions'] == 1.0 是一个条件, 返回一个布尔值的序列
    # signals[...] 使用这个布尔序列来过滤DataFrame, 只保留值为True的行
    buy_signals = signals[signals['positions'] == 1.0]
    # 在图上标记买入点。这里不在是画线, 而是画标记(marker)
    # '^' 表示使用向上的三角形作为标记
    # markersize=10 设置标记的大小, color='g' 设置为绿色
    ax1.plot(buy_signals.index, signals['short_mavg'][buy_signals.index],
             '^', markersize=10, color='g', lw=0, label='Buy Signal / 买入信号')

    # 筛选出所有卖出信号的行
    sell_signals = signals[signals['positions'] == -1.0]
    # 在图上标记卖出点
    # 'v' 表示使用向下的三角形作为标记, color='r' 设置为红色
    ax1.plot(sell_signals.index, signals['short_mavg'][sell_signals.index],
             'v', markersize=10, color='r', lw=0, label='Sell Signal / 卖出信号')

    # 设置第一个子图的标题和Y轴标签, 并应用中文字体
    ax1.set_title('Stock Price, Moving Averages, and Trading Signals / 股价, 移动均线, 和交易信号', fontproperties=chinese_font)
    ax1.set_ylabel('Price (USD) / 价格 (美元)', fontproperties=chinese_font)
    # 显示图例 (就是解释每条线或标记代表什么的小框)
    ax1.legend(loc='upper left', prop=chinese_font)
    # 显示网格线
    ax1.grid(True)

    # --- 第二个子图 (ax2): 绘制投资组合净值曲线 (资金变化) ---
    # ax2.plot(...) 在第二个子图上绘线
    ax2.plot(portfolio.index, portfolio['total_value'], label='Portfolio Value / 投资组合价值', color='green', linewidth=1.5)
    # 设置第二个子图的标题, X轴和Y轴的标签
    ax2.set_title('Portfolio Equity Curve / 投资组合净值曲线', fontproperties=chinese_font)
    ax2.set_xlabel('Date / 日期', fontproperties=chinese_font)
    ax2.set_ylabel('Portfolio Value (USD) / 投资组合价值 (美元)', fontproperties=chinese_font)
    # 显示图例和网格
    ax2.legend(loc='upper left', prop=chinese_font)
    ax2.grid(True)
    
    # 自动调整子图参数, 使之填充整个图表区域, 防止标签重叠
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # 返回创建好的图表对象(fig)。这使得其他函数可以复用这个图表, 比如在Streamlit应用中显示它
    return fig

# --- 定义主函数 ---
# 这是程序的逻辑主干
def main():
    """
    主函数, 用于执行整个回测流程。
    """
    # --- 配置参数 ---
    # 在这里定义回测需要的所有可调参数
    # Python 中没有 `const` 关键字, 通常用全大写变量名来表示这是一个不应被修改的常量(约定俗成)
    TICKER = 'AAPL'          # 股票代码 (苹果公司)
    START_DATE = '2018-01-01'  # 回测开始日期
    END_DATE = '2023-01-01'    # 回测结束日期
    SHORT_WINDOW = 40        # 短期移动平均线的计算窗口(天数)
    LONG_WINDOW = 100        # 长期移动平均线的计算窗口(天数)
    INITIAL_CAPITAL = 100000.0 # 初始模拟资金 (10万美元), 最后的 .0 表示这是一个浮点数

    # --- 执行流程 ---
    # 1. 获取数据
    # 调用我们从 data.fetcher 模块导入的 fetch_data 函数
    # 将上面定义的配置参数作为函数的实际参数传入
    stock_data = fetch_data(TICKER, START_DATE, END_DATE)

    # 检查返回的数据是否为空。在Python中, pandas的DataFrame有一个 .empty 属性
    if stock_data.empty:
        # 如果数据为空, 打印错误信息并用 return 提前结束 main 函数
        print("Could not retrieve data. Exiting.")
        return

    # 2. 生成信号
    # 调用我们从 strategies.sma_crossover 模块导入的 generate_signals 函数
    # 第一个参数是上一步获取的股票数据, 后面的参数是均线窗口配置
    signals_data = generate_signals(stock_data, short_window=SHORT_WINDOW, long_window=LONG_WINDOW)
    print(f"Signals generated, data rows: {len(signals_data)}") # Debug info

    # 3. 运行回测
    # 调用我们从 backtest.engine 模块导入的 run_backtest 函数
    # 它会返回两个结果: portfolio (记录每日资金状况) 和 stats (最终的统计数据)
    # Python函数可以返回多个值, 通常以元组(tuple)的形式
    portfolio, stats = run_backtest(signals_data, initial_capital=INITIAL_CAPITAL)
    print(f"Backtest completed, portfolio data rows: {len(portfolio)}") # Debug info

    # --- 输出结果 ---
    # 打印最终的性能统计数据
    print("\n--- Backtest Performance ---")
    # 遍历(loop over) stats 字典中的每一个键值对
    # .items() 方法类似于 Java中 Map的 entrySet()
    for key, value in stats.items():
        # 使用 f-string 格式化输出
        # {key.replace('_', ' ').title():<25} -> 拿key, 把下划线替换成空格, 每个单词首字母大写, 然后左对齐并占25个字符宽度
        # {value:,.2f} -> 拿value, 使用逗号做千位分隔符, 并保留两位小数
        print(f"{key.replace('_', ' ').title():<25}: {value:,.2f}")
    print("----------------------------\n")

    # 4. 绘制结果图表
    # 在脚本作为普通python脚本运行时, 这几行会打印提示信息并显示图表
    print("\nDisplaying plot window. Please close the plot window to exit the program.")
    
    # 调用本文件中定义的 plot_results 函数, 获取图表对象
    fig = plot_results(portfolio, signals_data, TICKER)
    # plt.show() 会暂停程序, 并弹出一个窗口显示上面创建的所有图表
    plt.show() # 当直接运行 main.py 时, 显示图表


# --- 程序入口 ---
# 这是一个Python脚本的经典写法
# 当这个 .py 文件被直接执行时 (例如, 在命令行中运行 `python main.py`),
# Python解释器会把特殊变量 `__name__` 设置为 `'__main__'`
# 如果这个文件被其他 .py 文件作为模块导入时, `__name__` 会是模块名 (即 'main')
# 所以, `if __name__ == '__main__':` 这行代码确保 `main()` 函数只在直接执行此文件时才被调用
# 这相当于Java程序中的 `public static void main(String[] args)` 方法
if __name__ == '__main__':
    main() # 调用上面定义的 main 函数, 程序开始执行
