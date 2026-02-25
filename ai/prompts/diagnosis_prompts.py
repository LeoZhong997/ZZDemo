"""
诊断类 Prompt 模板
定义智能诊断报告生成所需的各类 Prompt 模板
"""
from typing import Dict, Any, List, Optional


# ==================== 系统提示词 ====================

DIAGNOSIS_SYSTEM_PROMPT = """你是一个专业的外卖经营分析助手，具备以下能力：

1. **数据分析**：能够分析门店营收、订单量、转化率等核心经营指标
2. **对比分析**：能够进行门店对比、平台对比，找出差异和问题
3. **异常诊断**：能够识别数据异常并提供可能的原因分析
4. **趋势预测**：能够基于历史数据分析趋势
5. **决策建议**：能够提供可执行的运营改进建议

回答要求：
- 基于数据事实进行分析
- 提供具体数字支撑观点
- 建议要可落地执行
- 语言简洁专业
- 按优先级排序建议"""


# ==================== 诊断报告模板 ====================

DIAGNOSIS_REPORT_TEMPLATE = """请根据以下数据分析经营状况并生成诊断报告。

## 分析周期
{period}

{summary_section}
## 门店表现排名 (Top {top_n})
{store_ranking}

## 平台对比分析
{platform_comparison}

## 检测到的异常
{anomalies}

## 请输出以下内容：

### 1. 整体经营概况
（总结核心指标表现，用数据说明）

### 2. 门店分析
（分析表现最好和需改进的门店，说明原因）

### 3. 平台分析
（对比各平台表现，给出差异化策略建议）

### 4. 问题诊断
（分析异常原因，深入挖掘潜在问题）

### 5. 改进建议
（3-5条可执行建议，按优先级排序，每条建议说明预期效果）"""


# ==================== 门店对比模板 ====================

STORE_COMPARISON_TEMPLATE = """请对比分析以下门店的表现。

## 对比门店
{store_names}

## 对比数据
{comparison_data}

## 请输出以下内容：

### 1. 综合对比
（各门店的核心指标对比分析）

### 2. 优势分析
（每个门店的优势在哪里）

### 3. 差距分析
（表现较差门店的问题在哪里）

### 4. 改进建议
（针对每个门店的具体建议）"""


# ==================== 平台对比模板 ====================

PLATFORM_COMPARISON_TEMPLATE = """请分析以下平台的表现差异。

## 分析周期
{period}

## 平台数据
{platform_data}

## 请输出以下内容：

### 1. 平台概览
（各平台的核心指标对比）

### 2. 优势平台分析
（表现最好的平台及其原因）

### 3. 劣势平台分析
（表现较差的平台及其原因）

### 4. 平台策略建议
（针对各平台的差异化运营建议）"""


# ==================== 异常诊断模板 ====================

ANOMALY_DIAGNOSIS_TEMPLATE = """请分析以下异常数据并提供诊断。

## 异常概览
共检测到 {anomaly_count} 个异常

## 异常详情
{anomaly_details}

## 相关上下文
{context_data}

## 请输出以下内容：

### 1. 异常分类
（按严重程度和类型分类异常）

### 2. 根因分析
（分析每个异常的可能原因）

### 3. 影响评估
（异常对业务的影响程度）

### 4. 处理建议
（针对每个异常的处理方案）"""


# ==================== 趋势分析模板 ====================

TREND_ANALYSIS_TEMPLATE = """请分析以下数据的趋势。

## 分析指标
{metric}

## 日度数据
{daily_data}

## 趋势统计
{trend_stats}

## 请输出以下内容：

### 1. 趋势判断
（当前是上升、下降还是平稳趋势）

### 2. 波动分析
（分析数据波动情况）

### 3. 周期性特征
（是否有周期性规律）

### 4. 异常点分析
（如有异常值，分析可能原因）

### 5. 趋势预测
（对未来走势的预判）"""


# ==================== 简化诊断模板 ====================

QUICK_DIAGNOSIS_TEMPLATE = """请快速分析以下经营数据并给出关键洞察。

## 数据摘要
{data_summary}

## 请用简洁的语言回答：

1. **整体表现**：一句话总结
2. **亮点**：1-2个做得好的地方
3. **问题**：1-2个需要关注的问题
4. **建议**：1条最重要的建议"""


# ==================== 格式化辅助函数 ====================

def format_store_ranking(stores: List[Dict], top_n: int = 10) -> str:
    """
    格式化门店排名数据
    
    Args:
        stores: 门店数据列表
        top_n: 显示数量
        
    Returns:
        格式化的字符串
    """
    if not stores:
        return "暂无门店排名数据"
    
    lines = []
    for i, store in enumerate(stores[:top_n], 1):
        name = store.get('brand_store_name', '未知')
        income = store.get('actual_income', 0)
        orders = store.get('valid_order_count', 0)
        margin = store.get('margin_rate', 0)
        
        lines.append(
            f"{i}. **{name}**\n"
            f"   - 实收: ¥{income:,.0f}\n"
            f"   - 订单: {orders:,}\n"
            f"   - 到手率: {margin:.1f}%"
        )
    
    return '\n'.join(lines)


def format_platform_data(platforms: List[Dict]) -> str:
    """
    格式化平台数据
    
    Args:
        platforms: 平台数据列表
        
    Returns:
        格式化的字符串
    """
    if not platforms:
        return "暂无平台数据"
    
    lines = []
    for p in platforms:
        name = p.get('platform', '未知')
        income = p.get('actual_income', 0)
        share = p.get('revenue_share', 0)
        orders = p.get('valid_order_count', 0)
        margin = p.get('margin_rate', 0)
        
        lines.append(
            f"### {name}\n"
            f"- 实收: ¥{income:,.0f} (占比 {share:.1f}%)\n"
            f"- 订单: {orders:,}\n"
            f"- 到手率: {margin:.1f}%"
        )
    
    return '\n\n'.join(lines)


def format_anomalies(anomalies: List[Dict]) -> str:
    """
    格式化异常数据
    
    Args:
        anomalies: 异常列表
        
    Returns:
        格式化的字符串
    """
    if not anomalies:
        return "✅ 未检测到明显异常"
    
    lines = []
    for anomaly in anomalies:
        anomaly_type = anomaly.get('type', '未知类型')
        store = anomaly.get('store', '未知门店')
        metric = anomaly.get('metric', '未知指标')
        value = anomaly.get('value', 0)
        expected = anomaly.get('expected', 0)
        deviation = anomaly.get('deviation', 0)
        severity = anomaly.get('severity', '中')
        
        direction = "↓" if deviation < 0 else "↑"
        severity_icon = "🔴" if severity == "高" else "🟡" if severity == "中" else "🟢"
        
        lines.append(
            f"{severity_icon} **[{anomaly_type}]** {store} - {metric}\n"
            f"   - {direction} {abs(deviation):.1f}%\n"
            f"   - 实际值: {value:.2f}, 预期值: {expected:.2f}"
        )
    
    return '\n\n'.join(lines)


def format_summary_stats(stats: Dict) -> str:
    """
    格式化摘要统计
    
    Args:
        stats: 统计数据
        
    Returns:
        格式化的字符串
    """
    if not stats:
        return ""
    
    lines = ["## 数据摘要", ""]
    
    if 'date_range' in stats:
        dr = stats['date_range']
        lines.append(f"- **日期范围**: {dr.get('start', 'N/A')} 至 {dr.get('end', 'N/A')} ({dr.get('days', 0)} 天)")
    
    if 'stores' in stats:
        lines.append(f"- **门店数量**: {stats['stores'].get('count', 0)}")
    
    if 'platforms' in stats:
        platforms = stats['platforms']
        lines.append(f"- **平台**: {', '.join(platforms.get('list', []))}")
    
    if 'revenue' in stats:
        rev = stats['revenue']
        lines.append(f"- **总实收**: ¥{rev.get('total', 0):,.0f}")
        lines.append(f"- **平均日收**: ¥{rev.get('mean', 0):,.0f}")
    
    if 'orders' in stats:
        orders = stats['orders']
        lines.append(f"- **总订单**: {orders.get('total', 0):,}")
    
    lines.append("")
    return '\n'.join(lines)


def build_diagnosis_prompt(
    store_ranking: List[Dict],
    platform_comparison: List[Dict],
    anomalies: List[Dict],
    period: str,
    summary_stats: Dict = None,
    top_n: int = 10
) -> str:
    """
    构建诊断报告 Prompt
    
    Args:
        store_ranking: 门店排名数据
        platform_comparison: 平台对比数据
        anomalies: 异常列表
        period: 分析周期
        summary_stats: 摘要统计
        top_n: 显示门店数量
        
    Returns:
        构建好的 Prompt
    """
    # 格式化各部分数据
    summary_section = format_summary_stats(summary_stats) if summary_stats else ""
    store_ranking_str = format_store_ranking(store_ranking, top_n)
    platform_str = format_platform_data(platform_comparison)
    anomalies_str = format_anomalies(anomalies)
    
    # 填充模板
    prompt = DIAGNOSIS_REPORT_TEMPLATE.format(
        period=period,
        summary_section=summary_section,
        top_n=top_n,
        store_ranking=store_ranking_str,
        platform_comparison=platform_str,
        anomalies=anomalies_str
    )
    
    return prompt


def build_quick_diagnosis_prompt(data_summary: str) -> str:
    """
    构建快速诊断 Prompt
    
    Args:
        data_summary: 数据摘要
        
    Returns:
        构建好的 Prompt
    """
    return QUICK_DIAGNOSIS_TEMPLATE.format(data_summary=data_summary)


def build_store_comparison_prompt(
    comparison_data: List[Dict],
    store_names: List[str]
) -> str:
    """
    构建门店对比 Prompt
    
    Args:
        comparison_data: 对比数据
        store_names: 门店名称列表
        
    Returns:
        构建好的 Prompt
    """
    import json
    
    comparison_str = json.dumps(comparison_data, ensure_ascii=False, indent=2)
    
    return STORE_COMPARISON_TEMPLATE.format(
        store_names=', '.join(store_names),
        comparison_data=comparison_str
    )


def build_anomaly_diagnosis_prompt(
    anomalies: List[Dict],
    context_data: str = ""
) -> str:
    """
    构建异常诊断 Prompt
    
    Args:
        anomalies: 异常列表
        context_data: 上下文数据
        
    Returns:
        构建好的 Prompt
    """
    anomaly_details = format_anomalies(anomalies)
    context = context_data if context_data else "无额外上下文"
    
    return ANOMALY_DIAGNOSIS_TEMPLATE.format(
        anomaly_count=len(anomalies),
        anomaly_details=anomaly_details,
        context_data=context
    )