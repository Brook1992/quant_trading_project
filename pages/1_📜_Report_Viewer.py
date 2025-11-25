import streamlit as st
import pandas as pd
import json
import base64
import sys
import os

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.database import get_all_reports_from_db

st.set_page_config(
    page_title="回测报告查看器 (Backtest Report Viewer)",
    page_icon="📜",
    layout="wide"
)

st.title("📜 回测报告查看器 (Backtest Report Viewer)")

if st.button("🔄 刷新报告 (Refresh Reports)"):
    st.toast('报告已刷新！')

st.info("这里展示了所有已保存的回测运行记录。点击展开查看详情。")

# --- Load Reports ---
reports_df = get_all_reports_from_db()

if reports_df.empty:
    st.warning("数据库中没有找到任何回测报告。请返回主页运行一次新的回测。")
else:
    # --- Display Reports ---
    for index, row in reports_df.iterrows():
        st.divider()
        
        # --- Summary View (in a collapsible expander) ---
        metrics = json.loads(row['performance_metrics'])
        params = json.loads(row['strategy_params'])
        
        summary_header = f"**{row['company_name']} ({row['ticker']})** - 回测于 {row['run_timestamp']}"
        
        with st.expander(summary_header):
            st.write("#### 核心性能指标 (Key Performance Metrics)")
            
            # Display key metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("总收益率 (Total Return)", f"{metrics.get('total_return_pct', 0):.2f}%")
            col2.metric("夏普比率 (Sharpe Ratio)", f"{metrics.get('sharpe_ratio', 0):.2f}")
            col3.metric("最大回撤 (Max Drawdown)", f"{metrics.get('max_drawdown_pct', 0):.2f}%")
            col4.metric("胜率 (Win Rate)", f"{metrics.get('win_rate_pct', 0):.2f}%")

            # --- Detailed View ---
            st.write("#### 回测图表 (Backtest Chart)")
            st.image(f"data:image/png;base64,{row['chart_image']}", use_column_width=True)

            tab1, tab2 = st.tabs(["所有性能指标 (All Metrics)", "策略参数 (Strategy Parameters)"])
            
            with tab1:
                st.dataframe(pd.DataFrame.from_dict(metrics, orient='index', columns=['Value']))

            with tab2:
                st.dataframe(pd.DataFrame.from_dict(params, orient='index', columns=['Value']))
