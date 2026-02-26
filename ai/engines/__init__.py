"""
AI 功能引擎模块
包含智能诊断、预测分析、智能问答、决策建议等引擎
"""

from ai.engines.diagnosis_engine import DiagnosisEngine, generate_diagnosis, quick_diagnosis
from ai.engines.deep_diagnosis_engine import DeepDiagnosisEngine, generate_deep_diagnosis
from ai.engines.prediction_engine import (
    PredictionEngine,
    predict_revenue,
    analyze_trend,
    predict_by_store
)

__all__ = [
    # 诊断引擎
    'DiagnosisEngine',
    'generate_diagnosis',
    'quick_diagnosis',
    'DeepDiagnosisEngine',
    'generate_deep_diagnosis',
    
    # 预测引擎
    'PredictionEngine',
    'predict_revenue',
    'analyze_trend',
    'predict_by_store',
    
    # 以下引擎将在后续阶段实现
    # 'QAEngine',
    # 'SuggestionEngine',
]
