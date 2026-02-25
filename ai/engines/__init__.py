"""
AI 功能引擎模块
包含智能诊断、预测分析、智能问答、决策建议等引擎
"""

from ai.engines.diagnosis_engine import DiagnosisEngine, generate_diagnosis, quick_diagnosis

__all__ = [
    'DiagnosisEngine',
    'generate_diagnosis',
    'quick_diagnosis',
    # 以下引擎将在后续阶段实现
    # 'PredictionEngine',
    # 'QAEngine',
    # 'SuggestionEngine',
]
