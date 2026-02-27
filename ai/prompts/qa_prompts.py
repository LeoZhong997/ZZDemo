"""
QA 问答 Prompt 模板
提供智能问答相关的 Prompt 构建
"""
from typing import Dict, Any, List, Optional


# ========== 系统提示词 ==========
QA_SYSTEM_PROMPT = """你是一个专业的外卖经营分析助手，基于用户提供的数据回答问题。

## 你的职责
1. 回答关于外卖经营数据的问题
2. 提供数据驱动的分析和建议
3. 帮助用户理解门店、平台表现
4. 发现数据中的问题和机会

## 回答原则
- **数据优先**：回答要有数据支撑，引用具体数字
- **简洁明了**：直接回答问题，避免冗长
- **可操作**：提供建议时要具体、可执行
- **诚实**：如果数据不足以回答，明确说明

## 数据说明
用户会提供当前分析的数据上下文，包括：
- 日期范围
- 门店数据
- 平台数据
- 核心指标统计

请基于这些数据回答问题。如果问题超出了数据范围，请诚实说明。"""


# ========== Prompt 构建函数 ==========

def build_qa_prompt(question: str, 
                    data_context: Dict[str, Any],
                    conversation_history: List[Dict] = None) -> str:
    """
    构建 QA 问答 Prompt
    
    Args:
        question: 用户问题
        data_context: 数据上下文
        conversation_history: 对话历史（可选）
        
    Returns:
        构建好的 Prompt
    """
    parts = []
    
    # 添加数据上下文
    parts.append("## 当前数据上下文\n")
    parts.append(_format_data_context(data_context))
    
    # 添加对话历史摘要（如果有）
    if conversation_history and len(conversation_history) > 0:
        parts.append("\n## 对话历史\n")
        parts.append(_format_conversation_history(conversation_history))
    
    # 添加当前问题
    parts.append(f"\n## 用户问题\n{question}")
    
    return "\n".join(parts)


def build_qa_prompt_with_dataframe(question: str,
                                    df_summary: Dict[str, Any],
                                    store_data: List[Dict] = None,
                                    platform_data: List[Dict] = None) -> str:
    """
    基于 DataFrame 摘要构建 QA Prompt
    
    Args:
        question: 用户问题
        df_summary: DataFrame 摘要统计
        store_data: 门店数据（可选）
        platform_data: 平台数据（可选）
        
    Returns:
        构建好的 Prompt
    """
    parts = []
    
    # 数据概览
    parts.append("## 数据概览\n")
    
    if df_summary:
        # 日期范围
        if 'date_range' in df_summary:
            dr = df_summary['date_range']
            parts.append(f"- **日期范围**: {dr.get('start', '')} 至 {dr.get('end', '')}")
        
        # 收入统计
        if 'revenue' in df_summary:
            rev = df_summary['revenue']
            parts.append(f"- **总实收**: ¥{rev.get('total', 0):,.0f}")
            if rev.get('avg'):
                parts.append(f"- **日均实收**: ¥{rev.get('avg', 0):,.0f}")
        
        # 订单统计
        if 'orders' in df_summary:
            orders = df_summary['orders']
            parts.append(f"- **总订单数**: {orders.get('total', 0):,}")
            if orders.get('avg'):
                parts.append(f"- **日均订单**: {orders.get('avg', 0):,.1f}")
        
        # 门店和平台
        if 'stores' in df_summary:
            parts.append(f"- **门店数量**: {df_summary['stores'].get('count', 0)}")
        
        if 'platforms' in df_summary:
            platforms = df_summary['platforms'].get('list', [])
            parts.append(f"- **平台**: {', '.join(platforms)}")
    
    # 门店数据
    if store_data and len(store_data) > 0:
        parts.append("\n## 门店表现 (Top 5)\n")
        for i, store in enumerate(store_data[:5], 1):
            parts.append(f"{i}. **{store.get('brand_store_name', '未知')}**")
            parts.append(f"   - 实收: ¥{store.get('actual_income', 0):,.0f}")
            parts.append(f"   - 订单: {store.get('valid_order_count', 0):,}")
            if store.get('margin_rate'):
                parts.append(f"   - 到手率: {store.get('margin_rate', 0):.1f}%")
    
    # 平台数据
    if platform_data and len(platform_data) > 0:
        parts.append("\n## 平台对比\n")
        for plat in platform_data:
            parts.append(f"- **{plat.get('platform', '未知')}**: "
                        f"实收 ¥{plat.get('actual_income', 0):,.0f}, "
                        f"订单 {plat.get('valid_order_count', 0):,}")
    
    # 用户问题
    parts.append(f"\n## 用户问题\n{question}")
    
    return "\n".join(parts)


def build_quick_question_prompt(question_type: str, 
                                 data_context: Dict[str, Any]) -> str:
    """
    构建快捷问题的 Prompt
    
    Args:
        question_type: 问题类型 (revenue_down/best_store/suggestions 等)
        data_context: 数据上下文
        
    Returns:
        构建好的 Prompt
    """
    # 预定义的问题模板
    question_templates = {
        "revenue_down": "为什么这周实收下降了？请分析可能的原因并给出改进建议。",
        "best_store": "哪个门店表现最好？请分析其成功因素。",
        "worst_store": "哪个门店表现最差？请分析问题并给出改进建议。",
        "platform_compare": "请对比各平台的表现，分析差异原因并给出策略建议。",
        "suggestions": "基于当前数据，给我3-5条可执行的改进建议。",
        "anomalies": "数据中有哪些异常或需要注意的问题？",
        "trend": "请分析近期的经营趋势，预测未来走势。",
        "summary": "请用简洁的语言总结本周的经营状况。"
    }
    
    question = question_templates.get(question_type, question_type)
    return build_qa_prompt(question, data_context)


def build_data_query_prompt(query_type: str,
                             params: Dict[str, Any] = None) -> str:
    """
    构建数据查询类 Prompt
    
    Args:
        query_type: 查询类型
        params: 查询参数
        
    Returns:
        构建好的 Prompt
    """
    params = params or {}
    
    query_templates = {
        "store_detail": f"请详细介绍 {params.get('store_name', '指定')} 门店的经营情况，"
                       f"包括收入、订单、转化率等关键指标。",
        
        "date_range": f"请分析 {params.get('start', '')} 至 {params.get('end', '')} 期间的数据，"
                     f"重点关注 {params.get('focus', '整体表现')}。",
        
        "metric_explain": f"请解释 {params.get('metric', '该指标')} 的含义，"
                         f"并结合当前数据分析其表现。",
        
        "comparison": f"请对比 {params.get('entity1', 'A')} 和 {params.get('entity2', 'B')} 的表现，"
                     f"分析差异原因。"
    }
    
    return query_templates.get(query_type, query_type)


# ========== 辅助函数 ==========

def _format_data_context(data_context: Dict[str, Any]) -> str:
    """
    格式化数据上下文
    
    Args:
        data_context: 数据上下文字典
        
    Returns:
        格式化的文本
    """
    lines = []
    
    if not data_context:
        return "（暂无数据上下文）"
    
    # 日期范围
    if 'date_range' in data_context:
        dr = data_context['date_range']
        lines.append(f"- **日期范围**: {dr.get('start', '')} 至 {dr.get('end', '')}")
    
    # 收入
    if 'revenue' in data_context:
        rev = data_context['revenue']
        lines.append(f"- **总实收**: ¥{rev.get('total', 0):,.0f}")
    
    # 订单
    if 'orders' in data_context:
        orders = data_context['orders']
        lines.append(f"- **总订单**: {orders.get('total', 0):,}")
    
    # 客单价
    if 'avg_order_value' in data_context:
        lines.append(f"- **平均客单价**: ¥{data_context['avg_order_value']:,.1f}")
    
    # 到手率
    if 'margin_rate' in data_context:
        lines.append(f"- **平均到手率**: {data_context['margin_rate']:.1f}%")
    
    # 门店数
    if 'store_count' in data_context:
        lines.append(f"- **门店数**: {data_context['store_count']}")
    
    # 平台
    if 'platforms' in data_context:
        lines.append(f"- **平台**: {', '.join(data_context['platforms'])}")
    
    # Top 门店
    if 'top_stores' in data_context:
        lines.append("\n**Top 5 门店**:")
        for store in data_context['top_stores'][:5]:
            lines.append(f"  - {store.get('name', '')}: ¥{store.get('revenue', 0):,.0f}")
    
    # 异常
    if 'anomalies' in data_context and data_context['anomalies']:
        lines.append("\n**检测到的异常**:")
        for anomaly in data_context['anomalies'][:3]:
            lines.append(f"  - {anomaly.get('description', '')}")
    
    return "\n".join(lines) if lines else "（暂无数据）"


def _format_conversation_history(history: List[Dict]) -> str:
    """
    格式化对话历史
    
    Args:
        history: 对话历史列表
        
    Returns:
        格式化的文本
    """
    lines = []
    
    # 只取最近3轮对话
    recent_history = history[-6:] if len(history) > 6 else history
    
    for msg in recent_history:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if role == 'user':
            lines.append(f"**用户**: {content[:100]}{'...' if len(content) > 100 else ''}")
        elif role == 'assistant':
            lines.append(f"**助手**: {content[:100]}{'...' if len(content) > 100 else ''}")
    
    return "\n".join(lines) if lines else "（无历史对话）"


def get_suggested_questions(data_context: Dict[str, Any] = None) -> List[Dict[str, str]]:
    """
    根据数据上下文生成建议的问题
    
    Args:
        data_context: 数据上下文
        
    Returns:
        建议问题列表，每项包含 label和 type
    """
    # 基础问题
    questions = [
        {"label": "📊 总结经营状况", "type": "summary"},
        {"label": "🏆 哪个门店表现最好？", "type": "best_store"},
        {"label": "💡 给我改进建议", "type": "suggestions"},
    ]
    
    # 根据数据上下文添加更多问题
    if data_context:
        # 如果有多个平台，添加平台对比问题
        platforms = data_context.get('platforms', [])
        if isinstance(platforms, list) and len(platforms) > 1:
            questions.append({"label": "📱 对比平台表现", "type": "platform_compare"})
        
        # 如果有异常，添加异常分析问题
        anomalies = data_context.get('anomalies', [])
        if anomalies:
            questions.append({"label": "⚠️ 分析异常问题", "type": "anomalies"})
        
        # 添加趋势分析问题
        if data_context.get('has_trend_data'):
            questions.append({"label": "📈 分析经营趋势", "type": "trend"})
    
    return questions