"""
AI 经营诊断报告页面
提供智能诊断报告生成功能
"""
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.config.config import get_connection_string, ALL_PLATFORMS
from ai.engines.diagnosis_engine import DiagnosisEngine
from ai.core.llm_adapter import get_llm_adapter
from ai.config import get_ai_config, validate_ai_config
from ai.analytics.data_aggregator import DataAggregator
from ai.analytics.anomaly_detector import AnomalyDetector


# ========== 页面配置 ==========
st.set_page_config(
    page_title="AI 经营诊断",
    page_icon="🤖",
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
st.sidebar.header("🤖 AI 诊断配置")

# 日期范围
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
**当前筛选条件:**

📅 日期: {start_date} ~ {end_date}

🏪 平台: {', '.join([p for p in selected_platforms if p])}

🏬 门店: {store_text}
""")


# ========== 主页面 ==========
st.title("🤖 AI 经营诊断报告")

st.markdown("""
本页面利用 AI 大模型对您的经营数据进行智能分析，生成诊断报告。

**功能说明：**
- 📊 门店排名分析（自动计算）
- 📈 平台对比分析（自动计算）
- ⚠️ 异常检测告警（自动计算）
- 💡 AI 智能诊断建议（需手动触发）
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
    st.success(f"✅ 数据加载成功！共 {len(df)} 条记录")
    
    # ========== 第一部分：数据概览（保持展开）==========
    with st.expander("📋 数据概览", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总实收", f"¥{df['actual_income'].sum():,.0f}")
        with col2:
            st.metric("总订单", f"{df['valid_orders'].sum():,}")
        with col3:
            st.metric("门店数", f"{df['brand_store_name'].nunique()}")
        with col4:
            st.metric("平台数", f"{df['platform'].nunique()}")
    
    st.markdown("---")
    
    # ========== 第二部分：自动计算的分析模块（并排展示）==========
    st.markdown("### 📊 数据分析")
    
    # 自动计算数据
    aggregator = DataAggregator()
    detector = AnomalyDetector()
    
    store_ranking = aggregator.aggregate_by_store(df)
    platform_comparison = aggregator.aggregate_by_platform(df)
    anomalies = detector.detect(df)
    
    # 使用 tabs 并排展示三个模块
    tab1, tab2, tab3 = st.tabs([
        "📊 门店排名", "📈 平台对比", "⚠️ 异常告警"
    ])
    
    # Tab 1: 门店排名
    with tab1:
        st.subheader("📊 门店表现排名")
        if not store_ranking.empty:
            # 定义列名映射
            column_mapping = {
                'brand_store_name': '门店名称',
                'actual_income': '实收',
                'valid_orders': '有效订单',
                'margin_rate': '到手率%',
                'avg_order_value': '客单价',
                'total_orders': '总订单',
                'revenue_share': '营收占比%'
            }
            
            # 只选择存在的列
            display_columns = [c for c in column_mapping.keys() if c in store_ranking.columns]
            
            if display_columns:
                ranking_display = store_ranking[display_columns].head(10).copy()
                
                # 重命名列
                rename_dict = {c: column_mapping[c] for c in display_columns}
                ranking_display = ranking_display.rename(columns=rename_dict)
                
                # 格式化
                if '实收' in ranking_display.columns:
                    ranking_display['实收'] = ranking_display['实收'].apply(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "-")
                if '到手率%' in ranking_display.columns:
                    ranking_display['到手率%'] = ranking_display['到手率%'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
                if '客单价' in ranking_display.columns:
                    ranking_display['客单价'] = ranking_display['客单价'].apply(lambda x: f"¥{x:.1f}" if pd.notna(x) else "-")
                
                st.dataframe(ranking_display, use_container_width=True, hide_index=True)
        else:
            st.info("暂无门店排名数据")
    
    # Tab 2: 平台对比
    with tab2:
        st.subheader("📈 平台对比分析")
        if not platform_comparison.empty:
            # 定义列名映射
            platform_column_mapping = {
                'platform': '平台',
                'actual_income': '实收',
                'valid_orders': '订单数',
                'margin_rate': '到手率%',
                'revenue_share': '营收占比%'
            }
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 表格展示
                display_cols = [c for c in platform_column_mapping.keys() if c in platform_comparison.columns]
                
                if display_cols:
                    platform_display = platform_comparison[display_cols].copy()
                    
                    # 重命名列
                    rename_dict = {c: platform_column_mapping[c] for c in display_cols}
                    platform_display = platform_display.rename(columns=rename_dict)
                    
                    # 格式化
                    if '实收' in platform_display.columns:
                        platform_display['实收'] = platform_display['实收'].apply(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "-")
                    if '到手率%' in platform_display.columns:
                        platform_display['到手率%'] = platform_display['到手率%'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
                    if '营收占比%' in platform_display.columns:
                        platform_display['营收占比%'] = platform_display['营收占比%'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
                    
                    st.dataframe(platform_display, use_container_width=True, hide_index=True)
            
            with col2:
                # 展示营收占比数据
                st.markdown("**营收占比**")
                if 'revenue_share' in platform_comparison.columns and 'platform' in platform_comparison.columns:
                    for _, row in platform_comparison.iterrows():
                        pct = row['revenue_share']
                        platform = row['platform']
                        st.metric(platform, f"{pct:.1f}%")
        else:
            st.info("暂无平台对比数据")
    
    # Tab 3: 异常告警
    with tab3:
        st.subheader("⚠️ 异常告警")
        
        if anomalies:
            st.warning(f"检测到 {len(anomalies)} 个异常")
            
            for anomaly in anomalies:
                severity = anomaly.get('severity', '中')
                store = anomaly.get('store', '未知门店')
                metric = anomaly.get('metric', '未知指标')
                deviation = anomaly.get('deviation', 0)
                
                # 根据严重程度选择图标和颜色
                if severity == '高':
                    icon = "🔴"
                    box_type = "error"
                elif severity == '中':
                    icon = "🟡"
                    box_type = "warning"
                else:
                    icon = "🟢"
                    box_type = "info"
                
                direction = "↓" if deviation < 0 else "↑"
                message = f"{icon} **[{severity}]** {store} - {metric}: {direction} {abs(deviation):.1f}%"
                
                if box_type == "error":
                    st.error(message)
                elif box_type == "warning":
                    st.warning(message)
                else:
                    st.info(message)
        else:
            st.success("✅ 未检测到明显异常")
    
    st.markdown("---")
    
    # ========== 第三部分：AI 诊断总结（需手动触发）==========
    st.markdown("### 💡 AI 智能诊断")
    
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        generate_button = st.button(
            "🔍 生成 AI 诊断总结",
            type="primary",
            use_container_width=True
        )
    
    if generate_button:
        # 进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: 数据聚合
            status_text.text("📊 正在聚合数据...")
            progress_bar.progress(20)
            
            # Step 2: 异常检测
            status_text.text("⚠️ 正在检测异常...")
            progress_bar.progress(40)
            
            # Step 3: 构建 Prompt
            status_text.text("📝 正在构建分析提示...")
            progress_bar.progress(60)
            
            # Step 4: 调用 LLM
            status_text.text("🤖 AI 正在分析中，请稍候...")
            progress_bar.progress(80)
            
            # 初始化诊断引擎
            diagnosis_engine = DiagnosisEngine()
            
            # 生成报告
            period = f"{start_date} 至 {end_date}"
            report = diagnosis_engine.generate_full_diagnosis(df, period=period)
            
            progress_bar.progress(100)
            status_text.text("✅ 报告生成完成！")
            
            # 保存报告到 session state
            st.session_state['ai_diagnosis_report'] = report
            
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ 生成报告失败: {str(e)}")
            st.info("请检查 LLM 配置是否正确，或稍后重试。")
    
    # 显示 AI 诊断总结
    if 'ai_diagnosis_report' in st.session_state:
        report = st.session_state['ai_diagnosis_report']
        
        st.markdown("---")
        st.subheader("💡 AI 诊断总结")
        
        if not report.get('success', False):
            st.error(f"❌ {report.get('ai_summary', '报告生成失败')}")
        else:
            # 显示生成耗时
            elapsed_time = report.get('elapsed_time', 0)
            st.caption(f"⏱️ 生成耗时: {elapsed_time:.2f} 秒")
            
            # 显示 AI 分析结果
            ai_summary = report.get('ai_summary', '')
            if ai_summary:
                st.markdown(ai_summary)
            else:
                st.info("暂无 AI 分析结果")
            
            # 导出按钮
            st.markdown("---")
            if st.button("📋 复制报告内容"):
                st.code(ai_summary, language='markdown')
                st.success("报告内容已显示，可手动复制")


# 页脚
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    🤖 AI 经营诊断 | 基于智谱 GLM 大模型 | 最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
""", unsafe_allow_html=True)