"""
深度诊断 Prompt 模板
按照 data-analysis-demo.md 规范设计的深度分析报告模板
"""
from typing import Dict, Any, List, Optional


# ==================== 系统提示词 ====================

DEEP_DIAGNOSIS_SYSTEM_PROMPT = """你是一位拥有 10 年经验的资深外卖运营专家和数据分析师。你擅长通过多维度的运营数据（实收、到手率、非异率、回复率、评分等）诊断门店健康度，识别潜在风险，并基于平台算法逻辑（美团/饿了么/京东）提供可落地的优化策略。

你的分析风格客观、数据驱动，且能敏锐捕捉文字描述中的"隐性风险"（如：食安问题、服务态度的具体案例）。

## 分析能力
1. **数据清洗与异常检测**：识别红线指标（商责、回复率、评分、食安）
2. **多维度诊断**：财务健康度、运营合规性、口碑与质量、活动有效性
3. **根因分析与关联挖掘**：寻找指标间的因果关系
4. **行动建议生成**：输出 SMART 计划（具体、可衡量、可达成、相关、有时限）

## 回答要求
- 基于数据事实进行分析
- 提供具体数字支撑观点
- 建议要可落地执行
- 语言简洁专业
- 按优先级排序建议
- 使用指定的 Markdown 格式输出"""


# ==================== 深度诊断报告模板 ====================

DEEP_DIAGNOSIS_TEMPLATE = """请根据以下数据进行外卖运营深度分析，并按指定格式输出报告。

## 分析周期
{period}

{events_section}
## 数据摘要
{summary_stats}

## 门店健康度评级
{health_report}

## 红线指标检测结果
{redline_report}

## 转化漏斗断点分析
{breakpoint_report}

## 请严格按照以下 Markdown 格式输出分析报告：

---

# 📊 {period} 外卖运营深度分析报告

## 核心概览 (Executive Summary)

**整体表现**：[一句话总结本周大盘趋势，如：整体实收微涨，但商责率显著上升，需警惕。]

**红黑榜**：
- 🏆 **最佳门店**：[店名] （理由：...）
- 🔴 **高危门店**：[店名] （理由：...）

---

## 门店详细诊断表

| 门店 | 平台 | 状态 | 核心问题 (Top 3) | 关键数据异常 | 风险等级 |
|------|------|------|-----------------|-------------|---------|
{diagnosis_table}

*(注：仅列出有问题的门店，正常门店略过或合并简述)*

---

## 深度问题剖析 (Deep Dive)

### 🚨 共性风险预警
{common_risks}

### 💡 典型案例复盘
{case_analysis}

---

## 针对性行动清单 (Action Plan)

*(按优先级排序，指定责任人和截止时间)*

| 优先级 | 涉及门店 | 行动项 (What) | 执行标准/话术 (How) | 预期目标 |
|--------|---------|--------------|-------------------|---------|
{action_table}

---

## 战略建议 (Strategic Insights)

### 成本与毛利
[基于到手率和活动数据的建议]

### 产品与体验
[基于差评和食安反馈的建议]

### 管理与培训
[基于人为失误的分析建议]

---"""


# ==================== 门店诊断表模板 ====================

STORE_DIAGNOSIS_ROW_TEMPLATE = "| {store} | {platform} | {status} | {issues} | {anomalies} | {risk_level} |"


# ==================== 行动清单模板 ====================

ACTION_ROW_TEMPLATE = "| {priority} | {stores} | {action} | {how} | {expected} |"


# ==================== 根因分析模板 ====================

ROOT_CAUSE_TEMPLATE = """请分析以下问题的根本原因：

## 问题描述
{issue_description}

## 相关数据
{related_data}

## 请输出：

### 1. 问题定位
（这个问题的本质是什么）

### 2. 根因分析
（使用"5个为什么"方法深挖根本原因）

### 3. 关联影响
（这个问题会影响哪些其他指标）

### 4. 解决方案
（针对性的解决方案）"""


# ==================== 格式化辅助函数 ====================

def format_events_section(events: List[Dict] = None) -> str:
    """
    格式化特殊事件/备注部分
    
    Args:
        events: 事件列表
        
    Returns:
        格式化的字符串
    """
    if not events:
        return ""
    
    lines = ["## 特殊事件/备注", ""]
    
    for event in events:
        store = event.get('store_name', '全局')
        event_type = event.get('event_type', '')
        description = event.get('description', '')
        date = event.get('date', '')
        
        lines.append(f"- **{store}** ({date}): [{event_type}] {description}")
    
    lines.append("")
    return '\n'.join(lines)


def format_summary_stats(stats: Dict) -> str:
    """
    格式化数据摘要
    
    Args:
        stats: 统计数据
        
    Returns:
        格式化的字符串
    """
    if not stats:
        return "暂无数据"
    
    lines = []
    
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
    
    return '\n'.join(lines)


def format_health_report(health_data: Dict) -> str:
    """
    格式化健康度报告
    
    Args:
        health_data: 健康度数据
        
    Returns:
        格式化的字符串
    """
    if not health_data or not health_data.get('success'):
        return "暂无健康度数据"
    
    lines = []
    
    # 信号灯分布
    dist = health_data.get('traffic_light_distribution', {})
    lines.append(f"- 🟢 健康: {dist.get('green', 0)} 家")
    lines.append(f"- 🟡 需关注: {dist.get('yellow', 0)} 家")
    lines.append(f"- 🔴 高危: {dist.get('red', 0)} 家")
    lines.append(f"- **平均健康度**: {health_data.get('average_health_score', 0):.1f} 分")
    
    return '\n'.join(lines)


def format_redline_report(redline_data: Dict) -> str:
    """
    格式化红线检测报告
    
    Args:
        redline_data: 红线检测数据
        
    Returns:
        格式化的字符串
    """
    if not redline_data or not redline_data.get('success'):
        return "✅ 未检测到红线违规"
    
    summary = redline_data.get('summary', {})
    
    lines = []
    lines.append(f"- **违规总数**: {summary.get('total', 0)} 项")
    lines.append(f"- 🔴 高严重度: {summary.get('by_severity', {}).get('high', 0)} 项")
    lines.append(f"- 🟡 中严重度: {summary.get('by_severity', {}).get('medium', 0)} 项")
    lines.append(f"- 🟢 低严重度: {summary.get('by_severity', {}).get('low', 0)} 项")
    
    # 高风险门店
    high_risk = redline_data.get('high_risk_stores', [])
    if high_risk:
        lines.append("")
        lines.append("**高风险门店**:")
        for store in high_risk[:5]:
            lines.append(f"- {store['store']}: 风险分数 {store['risk_score']} ({', '.join(store['top_issues'])})")
    
    return '\n'.join(lines)


def format_breakpoint_report(breakpoint_data: Dict) -> str:
    """
    格式化断点分析报告
    
    Args:
        breakpoint_data: 断点分析数据
        
    Returns:
        格式化的字符串
    """
    if not breakpoint_data or not breakpoint_data.get('success'):
        return "暂无断点分析数据"
    
    summary = breakpoint_data.get('summary', {})
    
    lines = []
    lines.append(f"- **存在断点的门店**: {summary.get('stores_with_breakpoints', 0)} / {summary.get('total_stores', 0)}")
    
    by_type = summary.get('by_breakpoint_type', {})
    if by_type:
        lines.append("")
        lines.append("**断点类型分布**:")
        type_names = {
            'exposure_to_entry': '曝光-进店断点',
            'entry_to_order': '进店-下单断点',
            'order_to_income': '下单-实收断点（毛利问题）'
        }
        for bp_type, count in by_type.items():
            lines.append(f"- {type_names.get(bp_type, bp_type)}: {count} 家")
    
    return '\n'.join(lines)


def format_diagnosis_table(health_data: Dict, redline_data: Dict) -> str:
    """
    格式化门店诊断表
    
    Args:
        health_data: 健康度数据
        redline_data: 红线检测数据
        
    Returns:
        Markdown 表格字符串
    """
    if not health_data or not health_data.get('success'):
        return "| 暂无数据 | - | - | - | - | - |"
    
    rows = []
    
    # 获取门店排名
    ranking = health_data.get('store_ranking', [])
    by_store = redline_data.get('by_store', {})
    
    for store_info in ranking:
        store_name = store_info.get('brand_store_name', '')
        traffic_light = store_info.get('traffic_light', '🟢')
        health_score = store_info.get('health_score', 0)
        
        # 只显示有问题（黄灯或红灯）的门店
        if traffic_light == '🟢':
            continue
        
        # 获取该门店的红线违规
        violations = by_store.get(store_name, [])
        
        # 核心问题（最多3个）
        issues = [v['name'] for v in violations[:3]]
        issues_str = '<br>'.join(issues) if issues else '综合评分偏低'
        
        # 关键数据异常
        anomalies = []
        for v in violations[:2]:
            anomalies.append(f"{v['name']}: {v.get('description', '')}")
        anomalies_str = '<br>'.join(anomalies) if anomalies else '-'
        
        # 风险等级
        if traffic_light == '🔴':
            risk_level = '高'
        elif traffic_light == '🟡':
            risk_level = '中'
        else:
            risk_level = '低'
        
        row = STORE_DIAGNOSIS_ROW_TEMPLATE.format(
            store=store_name,
            platform='MT/ELM',  # 可以后续细化
            status=traffic_light,
            issues=issues_str,
            anomalies=anomalies_str,
            risk_level=risk_level
        )
        rows.append(row)
    
    if not rows:
        return "| 所有门店状态正常 ✅ | - | 🟢 | - | - | 低 |"
    
    return '\n'.join(rows)


def format_action_table(recommendations: List[Dict]) -> str:
    """
    格式化行动清单表格
    
    Args:
        recommendations: 建议列表
        
    Returns:
        Markdown 表格字符串
    """
    if not recommendations:
        return "| - | - | 暂无紧急行动项 | - | - |"
    
    rows = []
    for rec in recommendations[:10]:  # 最多10条
        row = ACTION_ROW_TEMPLATE.format(
            priority=rec.get('priority', 'P2'),
            stores=rec.get('stores', '相关门店'),
            action=rec.get('action', rec.get('issue', '')),
            how=rec.get('how', rec.get('action', '')),
            expected=rec.get('expected_result', rec.get('expected', ''))
        )
        rows.append(row)
    
    return '\n'.join(rows)


def format_common_risks(redline_data: Dict, breakpoint_data: Dict) -> str:
    """
    格式化共性风险预警
    
    Args:
        redline_data: 红线检测数据
        breakpoint_data: 断点分析数据
        
    Returns:
        格式化的字符串
    """
    lines = []
    
    # 从红线数据提取共性风险
    if redline_data and redline_data.get('success'):
        by_type = redline_data.get('by_type', {})
        
        type_names = {
            'merchant_responsibility': '商责订单',
            'merchant_cancellation_rate': '商责取消率',
            'reply_rate_5min': '5分钟回复率',
            'reply_rate_1min': '1分钟回复率',
            'store_score': '店铺评分',
            'store_score_critical': '店铺评分(严重)',
            'food_safety': '食安负反馈',
            'product_satisfaction': '商品满意度',
            'packaging_satisfaction': '包装满意度'
        }
        
        for v_type, violations in by_type.items():
            if len(violations) >= 2:  # 至少2家店有同样问题
                type_name = type_names.get(v_type, v_type)
                stores = [v['store'] for v in violations]
                lines.append(f"1. **{type_name}**：涉及 {len(violations)} 家店（{', '.join(stores[:3])}{'...' if len(stores) > 3 else ''}）")
    
    if not lines:
        lines.append("暂未发现明显的共性风险")
    
    return '\n'.join(lines)


def format_case_analysis(redline_data: Dict, events: List[Dict] = None) -> str:
    """
    格式化典型案例复盘
    
    Args:
        redline_data: 红线检测数据
        events: 事件列表
        
    Returns:
        格式化的字符串
    """
    lines = []
    
    # 如果有用户输入的事件，优先展示
    if events:
        for event in events[:2]:  # 最多2个案例
            lines.append(f"**案例**: {event.get('store_name', '')} - {event.get('description', '')}")
            lines.append(f"- **事件类型**: {event.get('event_type', '')}")
            lines.append("")
    
    # 从红线数据提取典型案例
    if redline_data and redline_data.get('success'):
        high_risk = redline_data.get('high_risk_stores', [])
        
        for store in high_risk[:2]:
            if store['has_high_severity']:
                lines.append(f"**案例**: {store['store']} - 多项红线违规")
                lines.append(f"- **主要问题**: {', '.join(store['top_issues'])}")
                lines.append(f"- **风险分数**: {store['risk_score']}")
                lines.append("")
    
    if not lines:
        lines.append("暂无典型案例需要复盘")
    
    return '\n'.join(lines)


def build_deep_diagnosis_prompt(
    period: str,
    summary_stats: Dict,
    health_data: Dict,
    redline_data: Dict,
    breakpoint_data: Dict,
    events: List[Dict] = None,
    recommendations: List[Dict] = None
) -> str:
    """
    构建深度诊断 Prompt
    
    Args:
        period: 分析周期
        summary_stats: 数据摘要
        health_data: 健康度数据
        redline_data: 红线检测数据
        breakpoint_data: 断点分析数据
        events: 特殊事件列表
        recommendations: 建议列表
        
    Returns:
        构建好的 Prompt
    """
    # 格式化各部分
    events_section = format_events_section(events)
    summary_str = format_summary_stats(summary_stats)
    health_str = format_health_report(health_data)
    redline_str = format_redline_report(redline_data)
    breakpoint_str = format_breakpoint_report(breakpoint_data)
    
    # 生成诊断表和行动清单的占位符（LLM会填充）
    diagnosis_table = format_diagnosis_table(health_data, redline_data)
    common_risks = format_common_risks(redline_data, breakpoint_data)
    case_analysis = format_case_analysis(redline_data, events)
    action_table = format_action_table(recommendations) if recommendations else "| - | - | 待分析后生成 | - | - |"
    
    # 填充模板
    prompt = DEEP_DIAGNOSIS_TEMPLATE.format(
        period=period,
        events_section=events_section,
        summary_stats=summary_str,
        health_report=health_str,
        redline_report=redline_str,
        breakpoint_report=breakpoint_str,
        diagnosis_table=diagnosis_table,
        common_risks=common_risks,
        case_analysis=case_analysis,
        action_table=action_table
    )
    
    return prompt


def build_quick_analysis_prompt(data_summary: str, question: str) -> str:
    """
    构建快速分析 Prompt
    
    Args:
        data_summary: 数据摘要
        question: 用户问题
        
    Returns:
        构建好的 Prompt
    """
    return f"""请基于以下数据快速回答用户问题。

## 数据摘要
{data_summary}

## 用户问题
{question}

## 回答要求
1. 简洁明了，直击要点
2. 用数据支撑观点
3. 如果需要更多信息，明确指出
"""


def build_store_comparison_prompt(store_data: List[Dict], store_names: List[str]) -> str:
    """
    构建门店对比 Prompt
    
    Args:
        store_data: 门店数据
        store_names: 门店名称列表
        
    Returns:
        构建好的 Prompt
    """
    import json
    
    return f"""请对比分析以下门店的表现。

## 对比门店
{', '.join(store_names)}

## 门店数据
```json
{json.dumps(store_data, ensure_ascii=False, indent=2)}
```

## 请输出：

### 1. 综合对比
（各门店的核心指标对比分析，使用表格展示）

### 2. 优势分析
（每个门店的优势在哪里）

### 3. 差距分析
（表现较差门店的问题在哪里）

### 4. 改进建议
（针对每个门店的具体建议）
"""