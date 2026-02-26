"""
预测分析 Prompt 模板
包含营收预测、趋势分析、节假日效应等场景的 Prompt 模板
"""
from typing import Dict, Any, List, Optional


# ========== 系统提示词 ==========

PREDICTION_SYSTEM_PROMPT = """你是一个专业的外卖经营数据分析助手，擅长预测分析和趋势判断。

你的职责是：
1. 基于历史数据预测未来营收趋势
2. 分析数据变化的规律和周期性
3. 识别节假日、周末等特殊时期的影响
4. 提供基于数据的专业建议

分析原则：
- 基于数据事实，避免主观臆断
- 说明预测的置信度和局限性
- 给出可执行的运营建议
- 关注异常波动和潜在风险"""


# ========== 营收预测模板 ==========

REVENUE_PREDICTION_TEMPLATE = """## 任务：营收预测分析

### 分析周期
{period}

### 历史数据摘要
{historical_summary}

### 统计特征
- 平均日营收: ¥{avg_daily_revenue:,.0f}
- 营收标准差: ¥{std_revenue:,.0f}
- 最高日营收: ¥{max_revenue:,.0f}
- 最低日营收: ¥{min_revenue:,.0f}
- 趋势方向: {trend_direction}
- 趋势强度: {trend_strength}

### 预测参数
- 预测天数: {prediction_days} 天
- 预测方法: {prediction_method}

### 历史趋势数据
{trend_data}

### 基于模型的初步预测
{model_predictions}

### 请输出以下内容：

#### 1. 预测结果分析
（分析预测数据的合理性，结合趋势判断）

#### 2. 置信度评估
（评估预测的可靠性，说明影响因素）

#### 3. 关键影响因素
（列出可能影响预测准确性的因素）

#### 4. 风险提示
（提示可能的下行风险）

#### 5. 运营建议
（基于预测给出的运营建议）"""


# ========== 趋势分析模板 ==========

TREND_ANALYSIS_TEMPLATE = """## 任务：趋势分析

### 分析周期
{period}

### 指标
{metric}

### 趋势数据
{trend_data}

### 趋势统计
- 趋势方向: {direction}
- 趋势强度: {strength}
- 日均变化: {daily_change}
- 拟合度 (R²): {r_squared}

### 周期性分析
{seasonality}

### 增长分析
{growth_analysis}

### 请输出以下内容：

#### 1. 趋势概述
（总结整体趋势走向）

#### 2. 阶段特征
（划分不同阶段，分析各阶段特征）

#### 3. 周期规律
（分析周期性规律，如周末效应等）

#### 4. 异常点分析
（识别并解释异常波动）

#### 5. 趋势预测
（预测未来短期走向）"""


# ========== 节假日效应模板 ==========

HOLIDAY_EFFECT_TEMPLATE = """## 任务：节假日效应分析

### 分析周期
{period}

### 节假日信息
{holiday_info}

### 节假日数据
{holiday_data}

### 对比数据（普通日期）
{normal_data}

### 效应统计
- 节假日平均营收: ¥{holiday_avg:,.0f}
- 普通日平均营收: ¥{normal_avg:,.0f}
- 效应系数: {effect_ratio}
- 提升幅度: {lift_percentage}%

### 请输出以下内容：

#### 1. 节假日效应概述
（总结节假日对营收的整体影响）

#### 2. 节前/节中/节后分析
（分析不同阶段的营收变化）

#### 3. 品类影响
（分析节假日对不同品类的影响差异）

#### 4. 备货建议
（针对下一个节假日的备货建议）

#### 5. 营销策略
（节假日营销策略建议）"""


# ========== 门店预测对比模板 ==========

STORE_PREDICTION_TEMPLATE = """## 任务：门店预测对比

### 分析周期
{period}

### 预测天数
{prediction_days} 天

### 门店预测数据
{store_predictions}

### 整体趋势
- 整体预测营收: ¥{total_predicted:,.0f}
- 整体趋势方向: {overall_trend}

### 请输出以下内容：

#### 1. 门店预测排名
（按预测表现对门店排序）

#### 2. 门店分类
（将门店分为增长型/稳定型/下降型）

#### 3. 重点门店分析
（分析表现突出和需关注的门店）

#### 4. 资源分配建议
（基于预测的资源分配建议）"""


# ========== 格式化函数 ==========

def format_historical_summary(df_summary: Dict) -> str:
    """格式化历史数据摘要"""
    lines = []
    
    if 'date_range' in df_summary:
        dr = df_summary['date_range']
        lines.append(f"- 日期范围: {dr.get('start', '')} 至 {dr.get('end', '')}")
        lines.append(f"- 数据天数: {dr.get('days', 0)} 天")
    
    if 'revenue' in df_summary:
        rev = df_summary['revenue']
        lines.append(f"- 总营收: ¥{rev.get('total', 0):,.0f}")
        lines.append(f"- 日均营收: ¥{rev.get('daily_avg', 0):,.0f}")
    
    if 'orders' in df_summary:
        orders = df_summary['orders']
        lines.append(f"- 总订单: {orders.get('total', 0):,}")
        lines.append(f"- 日均订单: {orders.get('daily_avg', 0):,.0f}")
    
    return '\n'.join(lines)


def format_trend_data(daily_data: List[Dict], metric: str = 'actual_income') -> str:
    """格式化趋势数据"""
    if not daily_data:
        return "暂无数据"
    
    lines = ["| 日期 | 值 | 变化 |", "|------|-----|------|"]
    
    prev_value = None
    for item in daily_data[-14:]:  # 最近14天
        date = item.get('date', '')
        value = item.get(metric, 0)
        
        if prev_value is not None:
            change = value - prev_value
            change_str = f"{'+' if change >= 0 else ''}{change:,.0f}"
        else:
            change_str = "-"
        
        lines.append(f"| {date} | ¥{value:,.0f} | {change_str} |")
        prev_value = value
    
    return '\n'.join(lines)


def format_predictions(predictions: List[Dict]) -> str:
    """格式化预测数据"""
    if not predictions:
        return "暂无预测"
    
    lines = ["| 日期 | 预测值 | 置信区间 |", "|------|--------|----------|"]
    
    for pred in predictions:
        date = pred.get('date', '')
        value = pred.get('predicted_value', 0)
        lower = pred.get('confidence_lower', value * 0.9)
        upper = pred.get('confidence_upper', value * 1.1)
        
        lines.append(f"| {date} | ¥{value:,.0f} | ¥{lower:,.0f} - ¥{upper:,.0f} |")
    
    return '\n'.join(lines)


def format_seasonality(seasonality: Dict) -> str:
    """格式化周期性数据"""
    if not seasonality:
        return "暂无周期性数据"
    
    lines = []
    
    has_pattern = seasonality.get('has_weekly_pattern', False)
    lines.append(f"- 存在周期性: {'是' if has_pattern else '否'}")
    
    if has_pattern:
        lines.append(f"- 高峰日: {seasonality.get('peak_day', '未知')}")
        lines.append(f"- 低谷日: {seasonality.get('low_day', '未知')}")
        lines.append(f"- 周末效应: {seasonality.get('weekend_effect_label', '未知')}")
    
    weekday_avg = seasonality.get('weekday_avg', {})
    if weekday_avg:
        lines.append("\n各日均值:")
        for day, avg in weekday_avg.items():
            lines.append(f"  - {day}: ¥{avg:,.0f}")
    
    return '\n'.join(lines)


def format_growth_analysis(growth: Dict) -> str:
    """格式化增长分析"""
    if not growth:
        return "暂无增长分析"
    
    lines = [
        f"- 总分析天数: {growth.get('total_days', 0)}",
        f"- 增长天数: {growth.get('growth_days', 0)}",
        f"- 下降天数: {growth.get('decline_days', 0)}",
        f"- 增长率: {growth.get('growth_rate', 0):.1f}%",
        f"- 最长连续增长: {growth.get('max_growth_streak', 0)} 天",
        f"- 最长连续下降: {growth.get('max_decline_streak', 0)} 天",
        f"- 整体趋势: {growth.get('overall_trend', '未知')}"
    ]
    
    return '\n'.join(lines)


def format_store_predictions(store_predictions: List[Dict]) -> str:
    """格式化门店预测数据"""
    if not store_predictions:
        return "暂无门店预测"
    
    lines = ["| 门店 | 预测营收 | 趋势 | 置信度 |", "|------|----------|------|--------|"]
    
    for store in store_predictions[:15]:  # 最多显示15个
        name = store.get('store_name', '未知')
        predicted = store.get('predicted_total', 0)
        trend = store.get('trend', '未知')
        confidence = store.get('confidence', 0)
        
        lines.append(f"| {name} | ¥{predicted:,.0f} | {trend} | {confidence:.0%} |")
    
    return '\n'.join(lines)


# ========== 构建函数 ==========

def build_revenue_prediction_prompt(
    historical_summary: Dict,
    trend_data: List[Dict],
    model_predictions: List[Dict],
    period: str,
    prediction_days: int = 7,
    prediction_method: str = "线性趋势外推"
) -> str:
    """
    构建营收预测 Prompt
    
    Args:
        historical_summary: 历史数据摘要
        trend_data: 趋势数据
        model_predictions: 模型预测结果
        period: 分析周期
        prediction_days: 预测天数
        prediction_method: 预测方法
        
    Returns:
        完整的 Prompt 字符串
    """
    # 计算统计特征
    values = [d.get('actual_income', 0) for d in trend_data if d.get('actual_income')]
    
    import numpy as np
    if values:
        avg_daily = np.mean(values)
        std_daily = np.std(values)
        max_val = np.max(values)
        min_val = np.min(values)
    else:
        avg_daily = std_daily = max_val = min_val = 0
    
    # 获取趋势信息
    trend_direction = historical_summary.get('trend', {}).get('direction', '未知')
    trend_strength = historical_summary.get('trend', {}).get('strength', 0)
    
    return REVENUE_PREDICTION_TEMPLATE.format(
        period=period,
        historical_summary=format_historical_summary(historical_summary),
        avg_daily_revenue=avg_daily,
        std_revenue=std_daily,
        max_revenue=max_val,
        min_revenue=min_val,
        trend_direction=trend_direction,
        trend_strength=f"{trend_strength:.2%}",
        prediction_days=prediction_days,
        prediction_method=prediction_method,
        trend_data=format_trend_data(trend_data),
        model_predictions=format_predictions(model_predictions)
    )


def build_trend_analysis_prompt(
    period: str,
    metric: str,
    trend_data: List[Dict],
    trend_stats: Dict,
    seasonality: Dict,
    growth_analysis: Dict
) -> str:
    """
    构建趋势分析 Prompt
    
    Args:
        period: 分析周期
        metric: 分析指标
        trend_data: 趋势数据
        trend_stats: 趋势统计
        seasonality: 周期性数据
        growth_analysis: 增长分析
        
    Returns:
        完整的 Prompt 字符串
    """
    metric_names = {
        'actual_income': '实收',
        'valid_order_count': '有效订单数',
        'margin_rate': '到手率',
        'avg_order_value': '客单价'
    }
    metric_name = metric_names.get(metric, metric)
    
    return TREND_ANALYSIS_TEMPLATE.format(
        period=period,
        metric=metric_name,
        trend_data=format_trend_data(trend_data, metric),
        direction=trend_stats.get('direction', '未知'),
        strength=f"{trend_stats.get('strength', 0):.2%}",
        daily_change=f"¥{trend_stats.get('daily_change', 0):,.2f}",
        r_squared=f"{trend_stats.get('r_squared', 0):.4f}",
        seasonality=format_seasonality(seasonality),
        growth_analysis=format_growth_analysis(growth_analysis)
    )


def build_holiday_effect_prompt(
    period: str,
    holiday_info: str,
    holiday_data: List[Dict],
    normal_data: List[Dict],
    holiday_avg: float,
    normal_avg: float
) -> str:
    """
    构建节假日效应分析 Prompt
    
    Args:
        period: 分析周期
        holiday_info: 节假日信息
        holiday_data: 节假日数据
        normal_data: 普通日数据
        holiday_avg: 节假日平均营收
        normal_avg: 普通日平均营收
        
    Returns:
        完整的 Prompt 字符串
    """
    import numpy as np
    
    holiday_values = [d.get('actual_income', 0) for d in holiday_data]
    normal_values = [d.get('actual_income', 0) for d in normal_data]
    
    effect_ratio = holiday_avg / normal_avg if normal_avg > 0 else 1.0
    lift_percentage = (effect_ratio - 1) * 100
    
    return HOLIDAY_EFFECT_TEMPLATE.format(
        period=period,
        holiday_info=holiday_info,
        holiday_data=format_trend_data(holiday_data),
        normal_data=format_trend_data(normal_data),
        holiday_avg=holiday_avg,
        normal_avg=normal_avg,
        effect_ratio=f"{effect_ratio:.2f}",
        lift_percentage=f"{lift_percentage:.1f}"
    )


def build_store_prediction_prompt(
    period: str,
    prediction_days: int,
    store_predictions: List[Dict],
    total_predicted: float,
    overall_trend: str
) -> str:
    """
    构建门店预测对比 Prompt
    
    Args:
        period: 分析周期
        prediction_days: 预测天数
        store_predictions: 门店预测数据
        total_predicted: 总预测营收
        overall_trend: 整体趋势
        
    Returns:
        完整的 Prompt 字符串
    """
    return STORE_PREDICTION_TEMPLATE.format(
        period=period,
        prediction_days=prediction_days,
        store_predictions=format_store_predictions(store_predictions),
        total_predicted=total_predicted,
        overall_trend=overall_trend
    )