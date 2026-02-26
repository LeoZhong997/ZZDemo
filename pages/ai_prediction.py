"""
AI 营收预测分析页面
提供营收预测、趋势分析、节假日效应分析功能
"""
import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import sys
import os
import plotly.graph_objects as go
import plotly.express as px

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.config.config import get_connection_string, ALL_PLATFORMS
from ai.engines.prediction_engine import PredictionEngine, predict_revenue, analyze_trend
from ai.core.llm_adapter import get_llm_adapter
from ai.config import get_ai_config, validate_ai_config
from ai.analytics.data_aggregator import DataAggregator
from ai.analytics.time_series import TimeSeriesAnalyzer


# ========== 页面配置 ==========
st.set_page_config(
    page_title="AI 营收预测",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ========== 数据库连接 ==========
@st.cache_resource
def get_database_engine():
    engine = create_engine(get_connection_string(), pool_size=5, max_overflow=10, pool_recycle=3600)
    return engine


@st.cache_data(ttl=600)
def get_store_list(platforms=None):
    """获取门店列表"""
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
    """获取数据"""
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


# ========== 侧边栏 ==========
st.sidebar.header("📈 AI 预测配置")

# 日期范围
st.sidebar.subheader("📅 历史数据范围")
engine = get_database_engine()
query_max_date = text("SELECT MAX(date) as max_date FROM daily_orders")
with engine.connect() as conn:
    result = conn.execute(query_max_date)
    max_date = result.scalar()
    if max_date:
        default_end_date = max_date
        default_start_date = max_date - timedelta(days=30)  # 默认30天历史数据
    else:
        default_end_date = datetime.now().date()
        default_start_date = default_end_date - timedelta(days=30)

start_date = st.sidebar.date_input("开始日期", value=default_start_date, max_value=datetime.now().date())
end_date = st.sidebar.date_input("结束日期", value=default_end_date, max_value=datetime.now().date())

if start_date > end_date:
    st.sidebar.error("⚠️ 开始日期不能大于结束日期")
    st.stop()

# 预测参数
st.sidebar.subheader("🔮 预测参数")
prediction_days = st.sidebar.select_slider(
    "预测天数",
    options=[7, 14, 21, 30],
    value=7,
    help="选择要预测的未来天数"
)

# 平台选择
st.sidebar.subheader("🏪 平台选择")
selected_platforms = st.sidebar.multiselect("选择平台", options=ALL_PLATFORMS, default=ALL_PLATFORMS)

if not selected_platforms:
    st.sidebar.warning("⚠️ 请至少选择一个平台")
    st.stop()

# 门店选择
st.sidebar.subheader("🏬 门店选择")
store_list = get_store_list(selected_platforms)
selected_stores = st.sidebar.multiselect("选择门店", options=store_list, default=None, 
                                          help="留空表示选择所有门店")

# LLM 配置
st.sidebar.subheader("🔧 LLM 配置")

# 测试 LLM 连接
if st.sidebar.button("🔗 测试 LLM 连接", use_container_width=True):
    with st.spinner("测试连接中..."):
        try:
            adapter = get_llm_adapter()
            result = adapter.test_connection()
            if result.get('success'):
                st.sidebar.success(f"✅ 连接成功！延迟: {result.get('latency_ms', 0)}ms")
            else:
                st.sidebar.error(f"❌ 连接失败: {result.get('message', '未知错误')}")
        except Exception as e:
            st.sidebar.error(f"❌ 连接异常: {str(e)}")

# 显示配置状态
config_validation = validate_ai_config()
if not config_validation.get('valid', True):
    st.sidebar.warning("⚠️ 配置问题:")
    for error in config_validation.get('errors', []):
        st.sidebar.error(f"- {error}")

st.sidebar.markdown("---")

# 当前筛选条件
store_text = '全部' if not selected_stores else f'{len(selected_stores)} 家'
st.sidebar.info(f"""
**当前配置:**

📅 历史数据: {start_date} ~ {end_date}

🔮 预测天数: {prediction_days} 天

🏪 平台: {', '.join([p for p in selected_platforms if p])}

🏬 门店: {store_text}
""")


# ========== 主页面 ==========
st.title("📈 AI 营收预测分析")

st.markdown("""
本页面利用 AI 大模型结合时间序列分析，对未来营收进行预测。

**功能说明：**
- 🔮 **营收预测** - 基于历史趋势预测未来营收
- 📉 **趋势分析** - 分析数据变化趋势和周期性
- 🎉 **节假日效应** - 分析节假日对营收的影响
- 🏪 **门店对比** - 对比各门店预测表现
""")

st.markdown("---")

# 加载数据
with st.spinner("🔄 正在加载数据..."):
    df = get_data(start_date, end_date, selected_platforms, selected_stores)
    time.sleep(0.3)

if df.empty:
    st.warning("⚠️ 没有找到符合条件的数据")
    st.info("请调整日期范围或选择条件后重试")
else:
    st.success(f"✅ 数据加载成功！共 {len(df)} 条记录，{df['date'].nunique()} 天数据")
    
    # ========== 数据概览 ==========
    with st.expander("📋 数据概览", expanded=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("总实收", f"¥{df['actual_income'].sum():,.0f}")
        with col2:
            st.metric("总订单", f"{df['valid_orders'].sum():,}")
        with col3:
            st.metric("日均营收", f"¥{df['actual_income'].sum() / df['date'].nunique():,.0f}")
        with col4:
            st.metric("门店数", f"{df['brand_store_name'].nunique()}")
        with col5:
            st.metric("平台数", f"{df['platform'].nunique()}")
    
    st.markdown("---")
    
    # ========== 历史趋势图表 ==========
    st.markdown("### 📊 历史数据趋势")
    
    # 聚合日度数据
    time_series = TimeSeriesAnalyzer()
    daily_data = time_series.aggregate_daily(df)
    
    if not daily_data.empty:
        # 绘制趋势图
        fig = go.Figure()
        
        # 历史数据线
        fig.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['actual_income'],
            mode='lines+markers',
            name='历史营收',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        # 添加移动平均线
        if len(daily_data) >= 7:
            daily_data['ma_7'] = daily_data['actual_income'].rolling(window=7, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=daily_data['date'],
                y=daily_data['ma_7'],
                mode='lines',
                name='7日移动平均',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
        
        fig.update_layout(
            title="历史营收趋势",
            xaxis_title="日期",
            yaxis_title="营收 (¥)",
            hovermode='x unified',
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========== Tabs：不同预测功能 ==========
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔮 营收预测", "📉 趋势分析", "🎉 节假日效应", "🏪 门店预测"
    ])
    
    # Tab 1: 营收预测
    with tab1:
        st.subheader("🔮 营收预测")
        
        col_left, col_center, col_right = st.columns([1, 2, 1])
        
        with col_center:
            generate_prediction_btn = st.button(
                "🚀 生成营收预测",
                type="primary",
                use_container_width=True,
                key="generate_prediction"
            )
        
        if generate_prediction_btn or 'prediction_result' in st.session_state:
            if generate_prediction_btn:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: 数据分析
                    status_text.text("📊 正在分析历史数据...")
                    progress_bar.progress(20)
                    
                    # Step 2: 模型预测
                    status_text.text("🔢 正在计算预测值...")
                    progress_bar.progress(50)
                    
                    # Step 3: AI 分析
                    status_text.text("🤖 AI 正在生成分析报告...")
                    progress_bar.progress(80)
                    
                    # 初始化预测引擎
                    prediction_engine = PredictionEngine()
                    
                    # 生成预测
                    result = prediction_engine.predict_revenue(df, days=prediction_days)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ 预测完成！")
                    time.sleep(0.3)
                    
                    st.session_state['prediction_result'] = result
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ 预测生成失败: {str(e)}")
                    st.info("请检查 LLM 配置是否正确，或稍后重试。")
            
            # 显示预测结果
            if 'prediction_result' in st.session_state:
                result = st.session_state['prediction_result']
                
                if not result.get('success', False):
                    st.error(f"❌ {result.get('analysis', '预测失败')}")
                else:
                    # 预测指标卡片
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_pred = result.get('total_predicted', 0)
                        st.metric("预测总营收", f"¥{total_pred:,.0f}")
                    
                    with col2:
                        daily_avg = result.get('daily_avg_predicted', 0)
                        st.metric("预测日均营收", f"¥{daily_avg:,.0f}")
                    
                    with col3:
                        trend = result.get('trend', '未知')
                        trend_icon = "📈" if trend == "上升" else ("📉" if trend == "下降" else "➡️")
                        st.metric("趋势方向", f"{trend_icon} {trend}")
                    
                    with col4:
                        confidence = result.get('confidence', 0)
                        st.metric("置信度", f"{confidence:.0%}")
                    
                    st.markdown("---")
                    
                    # 预测图表
                    predictions = result.get('predictions', [])
                    
                    if predictions:
                        # 创建预测图表
                        fig = go.Figure()
                        
                        # 历史数据
                        fig.add_trace(go.Scatter(
                            x=daily_data['date'],
                            y=daily_data['actual_income'],
                            mode='lines+markers',
                            name='历史数据',
                            line=dict(color='#1f77b4', width=2)
                        ))
                        
                        # 预测数据
                        pred_dates = [p['date'] for p in predictions]
                        pred_values = [p['predicted_value'] for p in predictions]
                        
                        fig.add_trace(go.Scatter(
                            x=pd.to_datetime(pred_dates),
                            y=pred_values,
                            mode='lines+markers',
                            name='预测值',
                            line=dict(color='#2ca02c', width=2, dash='dot'),
                            marker=dict(size=8, symbol='diamond')
                        ))
                        
                        # 置信区间
                        if 'confidence_lower' in predictions[0]:
                            lower = [p['confidence_lower'] for p in predictions]
                            upper = [p['confidence_upper'] for p in predictions]
                            
                            fig.add_trace(go.Scatter(
                                x=pd.to_datetime(pred_dates),
                                y=upper,
                                mode='lines',
                                line=dict(color='#2ca02c', width=0),
                                showlegend=False
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=pd.to_datetime(pred_dates),
                                y=lower,
                                mode='lines',
                                fill='tonexty',
                                fillcolor='rgba(44, 160, 44, 0.2)',
                                line=dict(color='#2ca02c', width=0),
                                name='置信区间'
                            ))
                        
                        fig.update_layout(
                            title="营收预测趋势图",
                            xaxis_title="日期",
                            yaxis_title="营收 (¥)",
                            hovermode='x unified',
                            height=450,
                            margin=dict(l=0, r=0, t=40, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 预测详情表格
                        with st.expander("📋 预测详情数据", expanded=False):
                            pred_df = pd.DataFrame(predictions)
                            pred_df['predicted_value'] = pred_df['predicted_value'].apply(lambda x: f"¥{x:,.0f}")
                            if 'confidence_lower' in pred_df.columns:
                                pred_df['confidence_lower'] = pred_df['confidence_lower'].apply(lambda x: f"¥{x:,.0f}")
                                pred_df['confidence_upper'] = pred_df['confidence_upper'].apply(lambda x: f"¥{x:,.0f}")
                            st.dataframe(pred_df, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    
                    # AI 分析
                    st.subheader("💡 AI 分析解读")
                    analysis = result.get('analysis', '')
                    if analysis:
                        st.markdown(analysis)
                    else:
                        st.info("暂无 AI 分析结果")
    
    # Tab 2: 趋势分析
    with tab2:
        st.subheader("📉 趋势分析")
        
        # 指标选择
        metric = st.selectbox(
            "选择分析指标",
            options=['actual_income', 'valid_orders', 'net_margin_rate'],
            format_func=lambda x: {'actual_income': '实收', 'valid_orders': '订单数', 'net_margin_rate': '到手率'}.get(x, x),
            key="trend_metric"
        )
        
        if st.button("📊 生成趋势分析", type="primary", key="generate_trend"):
            with st.spinner("正在分析趋势..."):
                try:
                    prediction_engine = PredictionEngine()
                    trend_result = prediction_engine.analyze_trend(df, metric=metric)
                    st.session_state['trend_result'] = trend_result
                except Exception as e:
                    st.error(f"趋势分析失败: {str(e)}")
        
        if 'trend_result' in st.session_state:
            trend_result = st.session_state['trend_result']
            
            if trend_result.get('success'):
                # 趋势统计
                col1, col2, col3 = st.columns(3)
                
                trend_stats = trend_result.get('trend', {})
                with col1:
                    direction = trend_stats.get('direction', '未知')
                    st.metric("趋势方向", direction)
                
                with col2:
                    strength = trend_stats.get('strength', 0)
                    st.metric("趋势强度", f"{strength:.2%}")
                
                with col3:
                    r_squared = trend_stats.get('r_squared', 0)
                    st.metric("拟合度 (R²)", f"{r_squared:.4f}")
                
                # 周期性分析
                seasonality = trend_result.get('seasonality', {})
                if seasonality.get('has_weekly_pattern'):
                    st.markdown("#### 📅 周期性规律")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("高峰日", seasonality.get('peak_day', '未知'))
                    with col2:
                        st.metric("低谷日", seasonality.get('low_day', '未知'))
                    with col3:
                        st.metric("周末效应", seasonality.get('weekend_effect_label', '未知'))
                    
                    # 各日均值柱状图
                    weekday_avg = seasonality.get('weekday_avg', {})
                    if weekday_avg:
                        fig = px.bar(
                            x=list(weekday_avg.keys()),
                            y=list(weekday_avg.values()),
                            labels={'x': '星期', 'y': '平均营收 (¥)'},
                            title="各日平均营收"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # AI 分析
                st.markdown("#### 💡 AI 分析")
                st.markdown(trend_result.get('analysis', '暂无分析'))
            else:
                st.error(trend_result.get('analysis', '分析失败'))
    
    # Tab 3: 节假日效应
    with tab3:
        st.subheader("🎉 节假日效应分析")
        st.markdown("分析节假日、特殊日期对营收的影响")
        
        # 节假日输入
        col1, col2 = st.columns([1, 2])
        
        with col1:
            holiday_name = st.text_input("节假日名称", value="节假日", key="holiday_name")
        
        with col2:
            # 使用日历多选
            holiday_dates_list = st.date_input(
                "选择节假日日期（可多选）",
                value=[],
                key="holiday_dates",
                help="点击日期可多选节假日日期"
            )
        
        if st.button("📊 分析节假日效应", type="primary", key="generate_holiday"):
            # 处理日期（单个日期或日期列表）
            if isinstance(holiday_dates_list, (list, tuple)):
                holiday_dates = [str(d) for d in holiday_dates_list]
            else:
                holiday_dates = [str(holiday_dates_list)] if holiday_dates_list else []
            
            if not holiday_dates:
                st.warning("请从日历选择节假日日期")
            else:
                with st.spinner("正在分析节假日效应..."):
                    try:
                        prediction_engine = PredictionEngine()
                        holiday_result = prediction_engine.analyze_holiday_effect(
                            df, 
                            holiday_dates=holiday_dates,
                            holiday_name=holiday_name
                        )
                        st.session_state['holiday_result'] = holiday_result
                    except Exception as e:
                        st.error(f"节假日效应分析失败: {str(e)}")
        
        if 'holiday_result' in st.session_state:
            holiday_result = st.session_state['holiday_result']
            
            if holiday_result.get('success'):
                impact = holiday_result.get('holiday_impact', {})
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("节假日平均营收", f"¥{impact.get('holiday_avg', 0):,.0f}")
                
                with col2:
                    st.metric("普通日平均营收", f"¥{impact.get('normal_avg', 0):,.0f}")
                
                with col3:
                    effect_ratio = impact.get('effect_ratio', 1)
                    st.metric("效应系数", f"{effect_ratio:.2f}")
                
                with col4:
                    lift = impact.get('lift_percentage', 0)
                    st.metric("提升幅度", f"{lift:+.1f}%")
                
                # AI 分析
                st.markdown("#### 💡 AI 分析")
                st.markdown(holiday_result.get('analysis', '暂无分析'))
            else:
                st.error(holiday_result.get('analysis', '分析失败'))
    
    # Tab 4: 门店预测
    with tab4:
        st.subheader("🏪 门店预测对比")
        
        top_n = st.slider("显示门店数量", min_value=5, max_value=20, value=10)
        
        if st.button("📊 生成门店预测", type="primary", key="generate_store_pred"):
            with st.spinner("正在预测各门店..."):
                try:
                    prediction_engine = PredictionEngine()
                    store_result = prediction_engine.predict_by_store(df, days=prediction_days, top_n=top_n)
                    st.session_state['store_pred_result'] = store_result
                except Exception as e:
                    st.error(f"门店预测失败: {str(e)}")
        
        if 'store_pred_result' in st.session_state:
            store_result = st.session_state['store_pred_result']
            
            if store_result.get('success'):
                # 整体统计
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("预测门店数", store_result.get('total_stores', 0))
                
                with col2:
                    st.metric("预测总营收", f"¥{store_result.get('total_predicted', 0):,.0f}")
                
                with col3:
                    st.metric("整体趋势", store_result.get('overall_trend', '未知'))
                
                with col4:
                    growth = store_result.get('growth_stores', 0)
                    decline = store_result.get('decline_stores', 0)
                    st.metric("增长/下降门店", f"{growth} / {decline}")
                
                # 门店预测表格
                store_predictions = store_result.get('store_predictions', [])
                
                if store_predictions:
                    st.markdown("#### 📊 门店预测排名")
                    
                    store_df = pd.DataFrame(store_predictions)
                    
                    # 只选择需要的列
                    display_columns = ['store_name', 'predicted_total', 'predicted_daily_avg', 'trend', 'confidence']
                    store_df = store_df[[col for col in display_columns if col in store_df.columns]]
                    
                    # 格式化数值
                    store_df['predicted_total'] = store_df['predicted_total'].apply(lambda x: f"¥{x:,.0f}")
                    store_df['predicted_daily_avg'] = store_df['predicted_daily_avg'].apply(lambda x: f"¥{x:,.0f}")
                    store_df['confidence'] = store_df['confidence'].apply(lambda x: f"{x:.0%}")
                    
                    store_df.columns = ['门店名称', '预测总营收', '预测日均', '趋势', '置信度']
                    st.dataframe(store_df, use_container_width=True, hide_index=True)
                    
                    # 预测柱状图
                    fig = px.bar(
                        store_predictions[:10],
                        x='store_name',
                        y='predicted_total',
                        color='trend',
                        title="门店预测营收排名",
                        labels={'store_name': '门店', 'predicted_total': '预测营收 (¥)', 'trend': '趋势'}
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                
                # AI 分析
                st.markdown("#### 💡 AI 分析")
                st.markdown(store_result.get('analysis', '暂无分析'))
            else:
                st.error(store_result.get('analysis', '预测失败'))


# 页脚
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    📈 AI 营收预测 | 基于智谱 GLM 大模型 + 时间序列分析 | 最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
""", unsafe_allow_html=True)