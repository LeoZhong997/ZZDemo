"""
AI Prompt 模板模块
包含诊断、预测、建议、问答等场景的 Prompt 模板
"""

from ai.prompts.diagnosis_prompts import (
    DIAGNOSIS_SYSTEM_PROMPT,
    DIAGNOSIS_REPORT_TEMPLATE,
    STORE_COMPARISON_TEMPLATE,
    PLATFORM_COMPARISON_TEMPLATE,
    ANOMALY_DIAGNOSIS_TEMPLATE,
    TREND_ANALYSIS_TEMPLATE,
    QUICK_DIAGNOSIS_TEMPLATE,
    format_store_ranking,
    format_platform_data,
    format_anomalies,
    format_summary_stats,
    build_diagnosis_prompt,
    build_quick_diagnosis_prompt,
    build_store_comparison_prompt,
    build_anomaly_diagnosis_prompt,
)

from ai.prompts.prediction_prompts import (
    PREDICTION_SYSTEM_PROMPT,
    REVENUE_PREDICTION_TEMPLATE,
    TREND_ANALYSIS_TEMPLATE as PREDICTION_TREND_TEMPLATE,
    HOLIDAY_EFFECT_TEMPLATE,
    STORE_PREDICTION_TEMPLATE,
    format_historical_summary,
    format_trend_data,
    format_predictions,
    format_seasonality,
    format_growth_analysis,
    format_store_predictions,
    build_revenue_prediction_prompt,
    build_trend_analysis_prompt,
    build_holiday_effect_prompt,
    build_store_prediction_prompt,
)

__all__ = [
    # 诊断系统提示词
    'DIAGNOSIS_SYSTEM_PROMPT',
    
    # 诊断模板
    'DIAGNOSIS_REPORT_TEMPLATE',
    'STORE_COMPARISON_TEMPLATE',
    'PLATFORM_COMPARISON_TEMPLATE',
    'ANOMALY_DIAGNOSIS_TEMPLATE',
    'TREND_ANALYSIS_TEMPLATE',
    'QUICK_DIAGNOSIS_TEMPLATE',
    
    # 诊断格式化函数
    'format_store_ranking',
    'format_platform_data',
    'format_anomalies',
    'format_summary_stats',
    
    # 诊断构建函数
    'build_diagnosis_prompt',
    'build_quick_diagnosis_prompt',
    'build_store_comparison_prompt',
    'build_anomaly_diagnosis_prompt',
    
    # 预测系统提示词
    'PREDICTION_SYSTEM_PROMPT',
    
    # 预测模板
    'REVENUE_PREDICTION_TEMPLATE',
    'PREDICTION_TREND_TEMPLATE',
    'HOLIDAY_EFFECT_TEMPLATE',
    'STORE_PREDICTION_TEMPLATE',
    
    # 预测格式化函数
    'format_historical_summary',
    'format_trend_data',
    'format_predictions',
    'format_seasonality',
    'format_growth_analysis',
    'format_store_predictions',
    
    # 预测构建函数
    'build_revenue_prediction_prompt',
    'build_trend_analysis_prompt',
    'build_holiday_effect_prompt',
    'build_store_prediction_prompt',
]
