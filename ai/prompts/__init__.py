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

__all__ = [
    # 系统提示词
    'DIAGNOSIS_SYSTEM_PROMPT',
    
    # 模板
    'DIAGNOSIS_REPORT_TEMPLATE',
    'STORE_COMPARISON_TEMPLATE',
    'PLATFORM_COMPARISON_TEMPLATE',
    'ANOMALY_DIAGNOSIS_TEMPLATE',
    'TREND_ANALYSIS_TEMPLATE',
    'QUICK_DIAGNOSIS_TEMPLATE',
    
    # 格式化函数
    'format_store_ranking',
    'format_platform_data',
    'format_anomalies',
    'format_summary_stats',
    
    # 构建函数
    'build_diagnosis_prompt',
    'build_quick_diagnosis_prompt',
    'build_store_comparison_prompt',
    'build_anomaly_diagnosis_prompt',
]