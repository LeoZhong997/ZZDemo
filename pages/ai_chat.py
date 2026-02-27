"""
AI 对话助手页面
提供自然语言问答、多轮对话、快捷问题功能
"""
import streamlit as st
import pandas as pd
import sys
import os
import logging
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.engines.qa_engine import QAEngine
from ai.core.llm_adapter import get_llm_adapter
from ai.config import get_ai_config, validate_ai_config
from etl.config.config import get_connection_string
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

# ========== 页面配置 ==========
st.set_page_config(
    page_title="AI 经营助手",
    page_icon="💬",
    layout="wide"
)

# ========== Session State 初始化 ==========
def init_session_state():
    """初始化 Session State"""
    if "qa_engine" not in st.session_state:
        st.session_state.qa_engine = None
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    
    if "data_context" not in st.session_state:
        st.session_state.data_context = {}
    
    if "llm_tested" not in st.session_state:
        st.session_state.llm_tested = False
    
    if "llm_status" not in st.session_state:
        st.session_state.llm_status = None


# ========== 数据库连接 ==========
@st.cache_resource
def get_db_engine():
    """获取数据库引擎"""
    return create_engine(get_connection_string(), pool_size=5, max_overflow=10, pool_recycle=3600)


# ========== 数据加载 ==========
@st.cache_data(ttl=300)
def load_data(start_date, end_date, platforms=None, stores=None):
    """
    加载数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        platforms: 平台列表
        stores: 门店列表
        
    Returns:
        DataFrame
    """
    try:
        engine = get_db_engine()
        
        conditions = ["date BETWEEN :start_date AND :end_date"]
        params = {"start_date": str(start_date), "end_date": str(end_date)}
        
        if platforms:
            placeholders = ','.join([f':platform_{i}' for i in range(len(platforms))])
            conditions.append(f"platform IN ({placeholders})")
            for i, p in enumerate(platforms):
                params[f'platform_{i}'] = p
        
        if stores:
            placeholders = ','.join([f':store_{i}' for i in range(len(stores))])
            conditions.append(f"brand_store_name IN ({placeholders})")
            for i, s in enumerate(stores):
                params[f'store_{i}'] = s
        
        where_clause = ' AND '.join(conditions)
        query = f"SELECT * FROM daily_orders WHERE {where_clause} ORDER BY date DESC"
        
        df = pd.read_sql(text(query), engine, params=params)
        
        return df
        
    except Exception as e:
        logger.error(f"数据加载失败: {e}")
        st.error(f"数据加载失败: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_available_platforms():
    """获取可用平台列表"""
    try:
        engine = get_db_engine()
        query = "SELECT DISTINCT platform FROM daily_orders WHERE platform IS NOT NULL"
        result = pd.read_sql(text(query), engine)
        return result['platform'].tolist()
    except:
        return []


@st.cache_data(ttl=600)
def get_available_stores():
    """获取可用门店列表"""
    try:
        engine = get_db_engine()
        query = "SELECT DISTINCT brand_store_name FROM daily_orders WHERE brand_store_name IS NOT NULL"
        result = pd.read_sql(text(query), engine)
        return result['brand_store_name'].tolist()
    except:
        return []


# ========== LLM 测试 ==========
def test_llm_connection():
    """测试 LLM 连接"""
    try:
        adapter = get_llm_adapter()
        result = adapter.test_connection()
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}


# ========== 侧边栏 ==========
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # LLM 连接测试
        st.subheader("🔗 LLM 连接")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("测试连接", use_container_width=True):
                with st.spinner("测试中..."):
                    result = test_llm_connection()
                    st.session_state.llm_tested = True
                    st.session_state.llm_status = result
        
        with col2:
            if st.session_state.llm_tested:
                if st.session_state.llm_status and st.session_state.llm_status.get("success"):
                    st.success("✓")
                else:
                    st.error("✗")
        
        # 显示 LLM 状态
        if st.session_state.llm_tested and st.session_state.llm_status:
            status = st.session_state.llm_status
            if status.get("success"):
                st.caption(f"延迟: {status.get('latency_ms', 0)}ms")
            else:
                st.error(f"连接失败: {status.get('message', '未知错误')}")
        
        st.divider()
        
        # 数据上下文配置
        st.subheader("📊 数据上下文")
        
        # 日期选择
        today = datetime.now()
        default_start = today - timedelta(days=7)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=default_start,
                key="chat_start_date"
            )
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=today,
                key="chat_end_date"
            )
        
        # 平台选择
        platforms = get_available_platforms()
        selected_platforms = st.multiselect(
            "平台",
            options=platforms,
            default=platforms,
            key="chat_platforms"
        )
        
        # 门店选择
        stores = get_available_stores()
        selected_stores = st.multiselect(
            "门店",
            options=stores,
            default=None,
            key="chat_stores",
            placeholder="全部门店"
        )
        
        # 加载数据按钮
        if st.button("📥 加载数据", use_container_width=True, type="primary"):
            with st.spinner("加载数据中..."):
                df = load_data(start_date, end_date, selected_platforms, selected_stores)
                
                if not df.empty:
                    # 初始化 QA Engine
                    st.session_state.qa_engine = QAEngine()
                    result = st.session_state.qa_engine.set_data_context(df)
                    
                    st.session_state.data_loaded = True
                    st.session_state.data_context = result.get("data_context", {})
                    st.session_state.messages = []  # 清除旧对话
                    
                    st.success(f"已加载 {len(df)} 条数据")
                else:
                    st.warning("没有找到符合条件的数据")
        
        # 数据状态
        if st.session_state.data_loaded:
            st.divider()
            st.subheader("📈 数据概览")
            
            ctx = st.session_state.data_context
            if ctx:
                if ctx.get("date_range"):
                    dr = ctx["date_range"]
                    st.caption(f"📅 {dr.get('start', '')} 至 {dr.get('end', '')}")
                
                if ctx.get("revenue"):
                    st.metric("总实收", f"¥{ctx['revenue'].get('total', 0):,.0f}")
                
                if ctx.get("store_count"):
                    st.metric("门店数", ctx["store_count"])
                
                if ctx.get("platforms"):
                    st.caption(f"平台: {', '.join(ctx['platforms'])}")
        
        st.divider()
        
        # 对话控制
        st.subheader("💬 对话控制")
        
        if st.button("🗑️ 清除对话", use_container_width=True):
            if st.session_state.qa_engine:
                st.session_state.qa_engine.clear_context()
            st.session_state.messages = []
            st.rerun()


# ========== 主区域 ==========
def render_chat_area():
    """渲染聊天区域"""
    st.title("💬 AI 经营助手")
    st.markdown("基于您的经营数据，AI 助手可以回答问题、分析趋势、提供建议。")
    
    # 检查数据是否加载
    if not st.session_state.data_loaded:
        st.info("👈 请先在侧边栏加载数据，然后开始对话。")
        
        # 显示使用说明
        with st.expander("📖 使用说明"):
            st.markdown("""
            ### 如何使用 AI 经营助手
            
            1. **配置数据上下文**
               - 在左侧侧边栏选择日期范围
               - 选择要分析的平台和门店
               - 点击「加载数据」按钮
            
            2. **开始对话**
               - 直接输入您的问题
               - 或点击下方的快捷问题按钮
            
            3. **支持的问答类型**
               - 📊 经营状况总结
               - 🏆 门店表现分析
               - 📱 平台对比分析
               - 💡 改进建议
               - ⚠️ 异常问题分析
               - 📈 趋势预测
            
            4. **多轮对话**
               - 支持上下文对话
               - 可以追问细节
               - 点击「清除对话」重新开始
            """)
        return
    
    # 显示对话历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 快捷问题
    if st.session_state.qa_engine:
        suggested = st.session_state.qa_engine.get_suggested_questions()
        
        if suggested:
            st.markdown("💡 **快捷问题**")
            cols = st.columns(min(len(suggested), 4))
            
            for i, q in enumerate(suggested[:4]):
                with cols[i]:
                    if st.button(q["label"], key=f"quick_{q['type']}"):
                        # 添加用户消息
                        st.session_state.messages.append({
                            "role": "user",
                            "content": q["label"]
                        })
                        
                        # 获取 AI 回复
                        with st.chat_message("assistant"):
                            with st.spinner("思考中..."):
                                response = st.session_state.qa_engine.quick_question(q["type"])
                            st.markdown(response)
                        
                        # 添加助手消息
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response
                        })
                        
                        st.rerun()
    
    # 用户输入
    if prompt := st.chat_input("输入您的问题..."):
        # 检查 QA Engine
        if not st.session_state.qa_engine:
            st.error("请先加载数据")
            return
        
        # 添加用户消息
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 获取 AI 回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = st.session_state.qa_engine.ask(prompt)
            st.markdown(response)
        
        # 添加助手消息
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })


# ========== 主函数 ==========
def main():
    """主函数"""
    init_session_state()
    render_sidebar()
    render_chat_area()


if __name__ == "__main__":
    main()