import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np
from datetime import datetime, timedelta
import time

# ========== 数据库配置（使用统一配置）==========
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_connection_string, ALL_PLATFORMS

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

# ========== 页面配置 ==========
st.set_page_config(
    page_title="周报数据",
    page_icon="📈",
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
st.title("📈 周报数据")

with st.spinner("🔄 正在加载数据..."):
    current_df = get_data(start_date, end_date, selected_platforms, selected_stores)
    time.sleep(0.3)

if current_df.empty:
    st.warning("⚠️ 没有找到符合条件的数据")
    st.info("请调整日期范围或选择条件后重试")
else:
    st.success(f"✅ 数据加载成功！共 {len(current_df)} 条记录")
    
    st.markdown("---")
    st.subheader("每日汇总数据")

    # Step 1: 数据聚合与排序
    weekday_map = {0: '星期日', 1: '星期一', 2: '星期二', 3: '星期三', 4: '星期四', 5: '星期五', 6: '星期六'}

    # 按 date 分组求和（不包含 real_actual_income）
    df_daily = current_df.groupby('date')[['turnover', 'actual_income', 'valid_orders', 'customer_paid', 'invalid_orders']].sum().reset_index()

    # 立即按 date 升序排序
    df_daily = df_daily.sort_values('date', ascending=True)

    # 将 date 列转换为字符串格式 YYYY-MM-DD（先确保是datetime类型）
    df_daily['date_str'] = pd.to_datetime(df_daily['date']).dt.strftime('%Y-%m-%d')

    # 计算每日的"到手率"（处理分母为0）
    df_daily['net_margin_rate'] = (df_daily['actual_income'] / df_daily['turnover'].replace(0, np.nan) * 100).fillna(0)

    # 计算每日的"实付单均价"（处理分母为0）
    df_daily['avg_paid_price'] = (df_daily['customer_paid'] / df_daily['valid_orders'].replace(0, np.nan)).fillna(0)

    # 生成中文"星期"列
    df_daily['weekday'] = pd.to_datetime(df_daily['date']).dt.dayofweek.map(weekday_map)

    # Step 2: 构建合计行
    # 计算所有行的 Sum
    total_turnover = df_daily['turnover'].sum()
    total_actual_income = df_daily['actual_income'].sum()
    total_valid_orders = df_daily['valid_orders'].sum()
    total_invalid_orders = df_daily['invalid_orders'].sum()
    total_customer_paid = df_daily['customer_paid'].sum()

    # 重新计算合计比率
    total_net_margin_rate = (total_actual_income / total_turnover * 100) if total_turnover > 0 else 0
    total_avg_paid_price = (total_customer_paid / total_valid_orders) if total_valid_orders > 0 else 0

    # 创建合计行 DataFrame，date_str 设为 "合计"，weekday 设为 ""
    total_row = pd.DataFrame({
        'date_str': ['合计'],
        'weekday': [''],
        'turnover': [total_turnover],
        'actual_income': [total_actual_income],
        'net_margin_rate': [total_net_margin_rate],
        'valid_orders': [total_valid_orders],
        'avg_paid_price': [total_avg_paid_price],
        'invalid_orders': [total_invalid_orders]
    })

    # Step 3: 拼接与清洗
    # 使用 pd.concat 拼接，保持日期顺序在前面，合计在最后
    df_result = pd.concat([df_daily, total_row], ignore_index=True)

    # 只保留需要的列并重命名
    df_result = df_result[['date_str', 'weekday', 'turnover', 'actual_income', 'net_margin_rate', 'valid_orders', 'avg_paid_price', 'invalid_orders']]
    df_result.columns = ['日期', '星期', '营业额', '商家实收', '到手率', '有效订单', '实付单均价', '无效订单']

    # 使用 .fillna(0) 填充空值
    df_result = df_result.fillna(0)

    column_config = {
        '日期': st.column_config.TextColumn('日期', width='small'),
        '星期': st.column_config.TextColumn('星期', width='small', disabled=True),
        '营业额': st.column_config.NumberColumn('营业额', format='%.2f'),
        '商家实收': st.column_config.NumberColumn('商家实收', format='%.2f'),
        '到手率': st.column_config.NumberColumn('到手率', format='%.2f%%'),
        '有效订单': st.column_config.NumberColumn('有效订单', format='%d'),
        '实付单均价': st.column_config.NumberColumn('实付单均价', format='%.2f'),
        '无效订单': st.column_config.NumberColumn('无效订单', format='%d')
    }
    st.dataframe(df_result, width='stretch', hide_index=True, column_config=column_config, height=500)

    st.markdown("---")
    st.subheader("门店核心指标")

    # 第一步：每日数据的聚合
    # 按"日期"分组
    agg_dict = {
        'store_score': 'mean',
        'new_merchant_score': 'mean',
        'five_min_reply_rate': 'mean',
        'one_min_reply_rate': 'mean',
        'meal_completion_report_rate': 'mean',
        'merchant_cancelled_orders': 'sum',
        'basic_duration': 'mean',
        'bad_review_reply_rate_score': 'mean'
    }
    df_store_agg = current_df.groupby('date').agg(agg_dict).reset_index()

    # 排序与格式化：立即按日期升序排列
    df_store_agg = df_store_agg.sort_values('date', ascending=True)

    # 将日期转为字符串格式 YYYY-MM-DD
    df_store_agg['date_str'] = pd.to_datetime(df_store_agg['date']).dt.strftime('%Y-%m-%d')

    # 加上中文"星期"
    df_store_agg['weekday'] = pd.to_datetime(df_store_agg['date']).dt.dayofweek.map(weekday_map)

    # 第二步：单独计算合计行
    # 对于"商责取消订单"：计算所有日期的总和
    total_merchant_cancelled_orders = df_store_agg['merchant_cancelled_orders'].sum()

    # 对于"评分/回复率/时长"等所有其他字段：计算所有日期的平均值
    total_store_score = df_store_agg['store_score'].mean()
    total_new_merchant_score = df_store_agg['new_merchant_score'].mean()
    total_five_min_reply_rate = df_store_agg['five_min_reply_rate'].mean()
    total_one_min_reply_rate = df_store_agg['one_min_reply_rate'].mean()
    total_meal_completion_rate = df_store_agg['meal_completion_report_rate'].mean()
    total_basic_duration = df_store_agg['basic_duration'].mean()
    total_bad_review_score = df_store_agg['bad_review_reply_rate_score'].mean()

    # 打包成一行，日期列填"合计"，星期列留空
    total_store_row = pd.DataFrame({
        'date_str': ['合计'],
        'weekday': [''],
        'store_score': [total_store_score],
        'new_merchant_score': [total_new_merchant_score],
        'five_min_reply_rate': [total_five_min_reply_rate],
        'one_min_reply_rate': [total_one_min_reply_rate],
        'meal_completion_report_rate': [total_meal_completion_rate],
        'merchant_cancelled_orders': [total_merchant_cancelled_orders],
        'basic_duration': [total_basic_duration],
        'bad_review_reply_rate_score': [total_bad_review_score]
    })

    # 第三步：拼接与列筛选
    # 把"每日明细"放在上面，"合计行"接在下面
    df_store_result = pd.concat([df_store_agg, total_store_row], ignore_index=True)

    # 只保留指定的列并重命名
    df_store_result = df_store_result[['date_str', 'weekday', 'store_score', 'new_merchant_score', 'five_min_reply_rate', 'one_min_reply_rate', 'meal_completion_report_rate', 'merchant_cancelled_orders', 'basic_duration', 'bad_review_reply_rate_score']]
    df_store_result.columns = ['日期', '星期', '店铺分', '新商家评分', '5分钟在线联系回复率', '1分钟在线联系回复率', '出餐完成上报率', '商责取消订单', '基础营业时长', '差评回复率得分']

    # 填充空值为 0
    df_store_result = df_store_result.fillna(0)

    # 第四步：前端展示配置
    column_config_store = {
        '日期': st.column_config.TextColumn('日期', width='small'),
        '星期': st.column_config.TextColumn('星期', width='small', disabled=True),
        '店铺分': st.column_config.NumberColumn('店铺分', format='%.2f'),
        '新商家评分': st.column_config.NumberColumn('新商家评分', format='%.2f'),
        '5分钟在线联系回复率': st.column_config.NumberColumn('5分钟在线联系回复率', format='%.2f%%'),
        '1分钟在线联系回复率': st.column_config.NumberColumn('1分钟在线联系回复率', format='%.2f%%'),
        '出餐完成上报率': st.column_config.NumberColumn('出餐完成上报率', format='%.2f%%'),
        '商责取消订单': st.column_config.NumberColumn('商责取消订单', format='%d'),
        '基础营业时长': st.column_config.NumberColumn('基础营业时长', format='%.2f'),
        '差评回复率得分': st.column_config.NumberColumn('差评回复率得分', format='%d')
    }
    st.dataframe(df_store_result, width='stretch', hide_index=True, column_config=column_config_store, height=400)

    st.markdown("---")
    st.subheader("线上过程指标")
    
    df_online = current_df.copy()
    df_online = pd.DataFrame(df_online)
    df_online['weekday'] = pd.to_datetime(df_online['date']).dt.dayofweek.map(weekday_map)
    df_online_agg = df_online.groupby('date')[['exposure_count', 'entry_count', 'order_people', 'order_conversion_rate', 'promotion_cost', 'real_actual_income', 'uv']].agg({
        'exposure_count': 'sum', 'entry_count': 'sum', 'order_people': 'sum',
        'order_conversion_rate': 'mean', 'promotion_cost': 'sum',
        'real_actual_income': 'sum', 'uv': 'sum'
    }).reset_index()
    
    # 格式化日期
    df_online_agg['date_str'] = pd.to_datetime(df_online_agg['date']).dt.strftime('%Y-%m-%d')
    df_online_agg['weekday'] = pd.to_datetime(df_online_agg['date']).dt.dayofweek.map(weekday_map)
    
    total_exposure = df_online['exposure_count'].sum()
    total_entry = df_online['entry_count'].sum()
    total_order_people = df_online['order_people'].sum()
    total_promotion = df_online['promotion_cost'].sum()
    total_real_income = df_online['real_actual_income'].sum()
    total_uv = df_online['uv'].sum()
    total_store_entry_rate = (total_entry / total_exposure * 100) if total_exposure > 0 else 0
    total_order_conversion_rate = (total_order_people / total_entry * 100) if total_entry > 0 else 0
    total_roi = (total_real_income / total_promotion) if total_promotion > 0 else 0
    
    total_online_row = pd.DataFrame({
        'date_str': ['总计'], 'weekday': [''], 'exposure_count': [total_exposure],
        'entry_count': [total_entry], 'store_entry_rate': [total_store_entry_rate],
        'order_people': [total_order_people], 'order_conversion_rate': [total_order_conversion_rate],
        'promotion_cost': [total_promotion], 'real_actual_income': [total_real_income],
        'roi': [total_roi], 'uv': [total_uv]
    })
    
    # 选择需要的列并重命名
    df_online_display = df_online_agg[['date_str', 'weekday', 'exposure_count', 'entry_count', 'store_entry_rate', 'order_people', 'order_conversion_rate', 'promotion_cost', 'real_actual_income', 'roi', 'uv']].copy()
    total_online_row.columns = ['日期', '星期', '曝光人数', '入店人数', '入店转化率', '下单人数', '下单转化率', '推广花费', '产出', 'ROI', 'UV']
    df_online_display.columns = ['日期', '星期', '曝光人数', '入店人数', '入店转化率', '下单人数', '下单转化率', '推广花费', '产出', 'ROI', 'UV']
    
    df_online_result = pd.concat([df_online_display, total_online_row], ignore_index=True)
    
    column_config_online = {
        '日期': st.column_config.TextColumn('日期', width='small'),
        '星期': st.column_config.TextColumn('星期', width='small', disabled=True),
        'exposure_count': st.column_config.NumberColumn('曝光人数', format='%d'),
        'entry_count': st.column_config.NumberColumn('入店人数', format='%d'),
        'store_entry_rate': st.column_config.NumberColumn('入店转化率', format='%.2f%%'),
        'order_people': st.column_config.NumberColumn('下单人数', format='%d'),
        'order_conversion_rate': st.column_config.NumberColumn('下单转化率', format='%.2f%%'),
        'promotion_cost': st.column_config.NumberColumn('推广花费', format='%.2f'),
        'real_actual_income': st.column_config.NumberColumn('产出', format='%.2f'),
        'roi': st.column_config.NumberColumn('ROI', format='%.2f'),
        'uv': st.column_config.NumberColumn('UV', format='%d')
    }
    st.dataframe(df_online_result, width='stretch', hide_index=True, column_config=column_config_online, height=400)

# 页脚
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    📈 周报数据 | 基于 Streamlit & MySQL 构建 | 最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
""", unsafe_allow_html=True)