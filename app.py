import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np
from datetime import datetime, timedelta
import time
import plotly.express as px

# ========== 数据库配置（使用统一配置）==========
from etl.config import get_connection_string, ALL_PLATFORMS

# ========== 数据库连接 ==========
@st.cache_resource
def get_database_engine():
    engine = create_engine(get_connection_string(), pool_size=5, max_overflow=10, pool_recycle=3600)
    return engine

@st.cache_data(ttl=600)
def get_store_list(platforms=None):
    try:
        engine = get_database_engine()
        conditions = []
        params = {}
        if platforms:
            placeholders = ','.join([f':platform_{i}' for i in range(len(platforms))])
            conditions.append(f"platform IN ({placeholders})")
            for i, platform in enumerate(platforms):
                params[f'platform_{i}'] = platform
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        query = f"""
        SELECT DISTINCT brand_store_name
        FROM daily_orders
        WHERE {where_clause}
        ORDER BY brand_store_name
        """
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            store_list = [row[0] for row in result if row[0]]
        return store_list
    except Exception as e:
        st.error(f"获取门店列表失败: {e}")
        return []

@st.cache_data(ttl=600)
def get_data(start_date, end_date, platforms, stores=None):
    try:
        engine = get_database_engine()
        conditions = []
        params = {}
        conditions.append("date BETWEEN :start_date AND :end_date")
        params['start_date'] = start_date
        params['end_date'] = end_date
        if platforms:
            placeholders = ','.join([f':platform_{i}' for i in range(len(platforms))])
            conditions.append(f"platform IN ({placeholders})")
            for i, platform in enumerate(platforms):
                params[f'platform_{i}'] = platform
        if stores:
            placeholders = ','.join([f':store_{i}' for i in range(len(stores))])
            conditions.append(f"brand_store_name IN ({placeholders})")
            for i, store in enumerate(stores):
                params[f'store_{i}'] = store
        where_clause = ' AND '.join(conditions)
        query = f"""
        SELECT * FROM daily_orders
        WHERE {where_clause}
        ORDER BY date DESC, platform
        """
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df
    except Exception as e:
        st.error(f"数据库查询失败: {e}")
        return pd.DataFrame()

def render_custom_metric_html(label, current_val, prev_val, is_rate=False):
    delta_val = current_val - prev_val
    if is_rate:
        delta_pct = delta_val
    else:
        delta_pct = delta_val / prev_val if prev_val != 0 else 0
    if is_rate:
        current_display = f"{current_val:.2f}%"
        prev_display = f"{prev_val:.2f}%"
    else:
        if label == "商家实收":
            current_display = f"¥{current_val:,.0f}"
            prev_display = f"¥{prev_val:,.0f}"
        else:
            current_display = f"{current_val:,.0f}"
            prev_display = f"{prev_val:,.0f}"
    if is_rate:
        delta_display = f"{delta_val:+.2f}pp"
    else:
        delta_display = f"{delta_val:+,.0f}"
    if delta_pct > 0:
        badge_bg = "#e6f4ea"
        badge_text = "#137333"
        arrow = "▲"
    elif delta_pct < 0:
        badge_bg = "#ffebeb"
        badge_text = "#d93025"
        arrow = "▼"
    else:
        badge_bg = "#f0f0f0"
        badge_text = "#666666"
        arrow = "─"
    if is_rate:
        badge_value = f"{delta_pct:+.2f}%"
    else:
        badge_value = f"{delta_pct:+.2f}%"
    html = f'''
    <div style="background: white; padding: 14px 18px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 100%; min-height: 130px;">
        <div style="font-size: 12px; color: #888888; margin-bottom: 6px;">{label}</div>
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 36px; font-weight: bold; color: #1a1a1a; line-height: 1.2;">{current_display}</div>
            <div style="background: {badge_bg}; color: {badge_text}; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600; white-space: nowrap;">{arrow} {badge_value}</div>
        </div>
        <div style="margin-top: 8px; font-size: 11px; color: #999999;">
            <span>上周: {prev_display}</span>
            <span style="margin-left: 10px;">差值: {delta_display}</span>
        </div>
    </div>
    '''
    return html

def calculate_period_comparison(current_data, previous_data):
    if current_data.empty:
        current_total_income = 0
        current_total_orders = 0
        current_total_turnover = 0
    else:
        valid_current = current_data[current_data['turnover'].notna()].copy()
        if not valid_current.empty:
            current_total_income = valid_current['actual_income'].sum()
            current_total_orders = valid_current['valid_orders'].sum()
            current_total_turnover = valid_current['turnover'].sum()
        else:
            current_total_income = 0
            current_total_orders = 0
            current_total_turnover = 0
    if previous_data.empty:
        previous_total_income = 0
        previous_total_orders = 0
        previous_total_turnover = 0
    else:
        valid_previous = previous_data[previous_data['turnover'].notna()].copy()
        if not valid_previous.empty:
            previous_total_income = valid_previous['actual_income'].sum()
            previous_total_orders = valid_previous['valid_orders'].sum()
            previous_total_turnover = valid_previous['turnover'].sum()
        else:
            previous_total_income = 0
            previous_total_orders = 0
            previous_total_turnover = 0
    if current_total_turnover > 0:
        current_net_rate = (current_total_income / current_total_turnover) * 100
    else:
        current_net_rate = 0
    if previous_total_turnover > 0:
        previous_net_rate = (previous_total_income / previous_total_turnover) * 100
    else:
        previous_net_rate = 0
    def calc_growth(current, previous):
        if previous == 0:
            return 0 if current == 0 else 100
        return ((current - previous) / previous) * 100
    orders_delta = calc_growth(current_total_orders, previous_total_orders)
    income_delta = calc_growth(current_total_income, previous_total_income)
    net_rate_delta = current_net_rate - previous_net_rate
    return {
        'current_total_income': current_total_income,
        'current_total_orders': current_total_orders,
        'current_net_rate': current_net_rate,
        'previous_total_orders': previous_total_orders,
        'previous_total_income': previous_total_income,
        'previous_net_rate': previous_net_rate,
        'orders_delta': orders_delta,
        'income_delta': income_delta,
        'net_rate_delta': net_rate_delta
    }

# ========== 页面配置 ==========
st.set_page_config(
    page_title="外卖数据看板",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 侧边栏 ==========
st.sidebar.header("📊 数据筛选")

st.sidebar.subheader("📅 日期范围")
engine = get_database_engine()
query_max_date = text("SELECT MAX(date) as max_date FROM daily_orders")
with engine.connect() as conn:
    result = conn.execute(query_max_date)
    max_date = result.scalar()
    if max_date:
        default_end_date = max_date
        default_start_date = max_date - timedelta(days=7)
    else:
        default_end_date = datetime.now().date()
        default_start_date = default_end_date - timedelta(days=7)

start_date = st.sidebar.date_input("开始日期", value=default_start_date, max_value=datetime.now().date())
end_date = st.sidebar.date_input("结束日期", value=default_end_date, max_value=datetime.now().date())

if start_date > end_date:
    st.sidebar.error("⚠️ 开始日期不能大于结束日期")
    st.stop()

st.sidebar.subheader("🏪 平台选择")
all_platforms = ALL_PLATFORMS
selected_platforms = st.sidebar.multiselect("选择平台", options=all_platforms, default=all_platforms)

if not selected_platforms:
    st.sidebar.warning("⚠️ 请至少选择一个平台")
    st.stop()

st.sidebar.subheader("🏬 门店选择")
store_list = get_store_list(selected_platforms)

if store_list:
    selected_stores = st.sidebar.multiselect("选择门店", options=store_list, default=None, help="留空表示选择所有门店")
else:
    st.sidebar.warning("没有可选择的门店")
    selected_stores = None

st.sidebar.markdown("---")
store_text = '全部' if not selected_stores else f'{len(selected_stores)} 家'
st.sidebar.info(f"""
**当前筛选条件:**

📅 日期: {start_date} ~ {end_date}

🏪 平台: {', '.join([p for p in selected_platforms if p])}

🏬 门店: {store_text}
""")

# ========== 主页面 ==========
st.title("🍔 外卖数据看板")
st.markdown("---")

days_diff = (end_date - start_date).days
previous_end_date = start_date - timedelta(days=1)
previous_start_date = previous_end_date - timedelta(days=days_diff)

with st.spinner("🔄 正在加载数据..."):
    current_df = get_data(start_date, end_date, selected_platforms, selected_stores)
    previous_df = get_data(previous_start_date, previous_end_date, selected_platforms, selected_stores)
    time.sleep(0.5)

if current_df.empty:
    st.warning("⚠️ 没有找到符合条件的数据")
    st.info("请调整日期范围或选择条件后重试")
else:
    st.success(f"✅ 数据加载成功！本期 {len(current_df)} 条记录，上一期 {len(previous_df)} 条记录")

    st.markdown("---")
    comparison = calculate_period_comparison(current_df, previous_df)

    st.markdown("**周累计**")
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            exposure_total = current_df['exposure_count'].sum() if not current_df.empty else 0
            st.metric(label="曝光", value=f"{exposure_total:,}")
        with col2:
            entry_rate = current_df['store_entry_rate'].mean() if not current_df.empty else 0
            st.metric(label="进店率", value=f"{entry_rate:.0f}%")
        with col3:
            order_rate = current_df['order_conversion_rate'].mean() if not current_df.empty else 0
            st.metric(label="下单率", value=f"{order_rate:.2f}%")
        with col4:
            if not current_df.empty and 'actual_income' in current_df.columns and 'turnover' in current_df.columns:
                valid_df = current_df[current_df['turnover'].notna() & current_df['actual_income'].notna()].copy()
                if not valid_df.empty:
                    total_actual_income = valid_df['actual_income'].sum()
                    total_turnover = valid_df['turnover'].sum()
                    net_rate = (total_actual_income / total_turnover * 100) if total_turnover > 0 else 0
                else:
                    net_rate = 0
            else:
                net_rate = 0
            st.metric(label="到手率", value=f"{net_rate:.2f}%")

    st.markdown("**周环比**")
    with st.container():
        col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 2])
        with col1:
            st.markdown(render_custom_metric_html("有效订单", comparison['current_total_orders'], comparison['previous_total_orders'], is_rate=False), unsafe_allow_html=True)
        with col2:
            st.markdown(render_custom_metric_html("商家实收", comparison['current_total_income'], comparison['previous_total_income'], is_rate=False), unsafe_allow_html=True)
        with col3:
            st.markdown(render_custom_metric_html("到手率", comparison['current_net_rate'], comparison['previous_net_rate'], is_rate=True), unsafe_allow_html=True)
        with col4:
            last_week_rate = comparison['current_net_rate'] - comparison['net_rate_delta']
            two_weeks_ago_rate = last_week_rate - comparison['net_rate_delta']
            history_html = f'''
            <div style="background: #f8f9fa; padding: 16px 18px; border-radius: 8px; border: 1px solid #e0e0e0; height: 100%; min-height: 130px;">
                <div style="font-size: 13px; font-weight: bold; color: #1a1a1a; margin-bottom: 12px; border-bottom: 1px solid #d1d5db; padding-bottom: 8px;">历史到手率</div>
                <div style="font-size: 13px; color: #666666; margin-bottom: 6px;">上周: <span style="font-weight: 600; color: #1a1a1a;">{last_week_rate:.2f}%</span></div>
                <div style="font-size: 13px; color: #666666; margin-bottom: 6px;">上上周: <span style="font-weight: 600; color: #1a1a1a;">{two_weeks_ago_rate:.2f}%</span></div>
            </div>
            '''
            st.markdown(history_html, unsafe_allow_html=True)

    st.markdown("---")
    tab1, tab2 = st.tabs(["📊 每日趋势", "📋 查看原始数据"])

    with tab1:
        st.subheader("每日趋势")
        
        # 按日期+平台汇总数据（解决多门店数据显示问题）
        daily_summary = current_df.groupby(['date', 'platform']).agg({
            'actual_income': 'sum',
            'valid_orders': 'sum',
            'turnover': 'sum'
        }).reset_index()
        
        with st.container():
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                fig_income = px.line(daily_summary, x='date', y='actual_income', color='platform', title='分平台营收趋势', labels={'date': '日期', 'actual_income': '商家实收', 'platform': '平台'})
                fig_income.update_layout(hovermode='x unified', legend=dict(orientation='h', yanchor='bottom', xanchor='right'), margin=dict(l=0, r=0, t=30, b=30))
                st.plotly_chart(fig_income, width='stretch', key='tab1_income_chart')
            with chart_col2:
                fig_orders = px.line(daily_summary, x='date', y='valid_orders', color='platform', title='分平台单量趋势', labels={'date': '日期', 'valid_orders': '有效订单', 'platform': '平台'})
                fig_orders.update_layout(hovermode='x unified', legend=dict(orientation='h', yanchor='bottom', xanchor='right'), margin=dict(l=0, r=0, t=30, b=30))
                st.plotly_chart(fig_orders, width='stretch', key='tab1_orders_chart')
        with st.container():
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                fig_orders_trend = px.bar(daily_summary, x='date', y='valid_orders', color='platform', title='订单趋势', labels={'date': '日期', 'valid_orders': '订单数', 'platform': '平台'})
                fig_orders_trend.update_layout(hovermode='x unified', legend=dict(orientation='h', yanchor='bottom', xanchor='right'), margin=dict(l=0, r=0, t=30, b=30), yaxis_title='订单数')
                st.plotly_chart(fig_orders_trend, width='stretch', key='tab1_orders_trend_chart')
            with chart_col2:
                income_by_platform_tab1 = daily_summary.groupby('platform')['actual_income'].sum().reset_index()
                fig_pie = px.pie(income_by_platform_tab1, values='actual_income', names='platform', title='各平台占比')
                fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=30))
                st.plotly_chart(fig_pie, width='stretch', key='tab1_pie_chart')
        with st.container():
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                fig_bar = px.bar(daily_summary, x='date', y='turnover', color='platform', title='营业额趋势', labels={'date': '日期', 'turnover': '营业额', 'platform': '平台'})
                fig_bar.update_layout(hovermode='x unified', legend=dict(orientation='h', yanchor='bottom', xanchor='right'), margin=dict(l=0, r=0, t=30, b=30), yaxis_title='营业额 (元)')
                st.plotly_chart(fig_bar, width='stretch', key='tab1_bar_chart')

    with tab2:
        st.subheader("平台占比分析")
        # 按平台汇总数据
        platform_summary = current_df.groupby('platform').agg({
            'actual_income': 'sum',
            'valid_orders': 'sum',
            'turnover': 'sum'
        }).reset_index()
        
        with st.container():
            pie_col1, pie_col2 = st.columns(2)
            with pie_col1:
                fig_pie = px.pie(platform_summary, values='actual_income', names='platform', title='各平台占比')
                fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=30))
                st.plotly_chart(fig_pie, width='stretch', key='tab3_pie_chart')
            with pie_col2:
                fig_income_by_platform = px.bar(platform_summary, x='platform', y='actual_income', title='分平台营收', labels={'platform': '平台', 'actual_income': '营收'})
                fig_income_by_platform.update_layout(hovermode='x unified', legend=dict(orientation='h', yanchor='bottom', xanchor='right'), margin=dict(l=0, r=0, t=30, b=30))
                st.plotly_chart(fig_income_by_platform, width='stretch', key='tab3_bar_chart')
        with st.expander("📋 查看原始数据"):
            st.dataframe(current_df, width='stretch', height=400)

# 快速导航
st.markdown("---")
st.markdown("### 🚀 快速导航")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📊 周报数据", use_container_width=True):
        st.switch_page("pages/1_周报数据.py")
with col2:
    if st.button("🔗 门店映射", use_container_width=True):
        st.switch_page("pages/store_mapping_simple.py")
with col3:
    if st.info("💡 更多功能请在左侧边栏切换页面"):
        pass

# 页脚
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    🍔 外卖数据看板 | 基于 Streamlit & MySQL 构建 | 最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
""", unsafe_allow_html=True)