"""
AI 经营决策模块
提供智能诊断、预测分析、智能问答、决策建议等功能
"""

__version__ = "1.0.0"

# 导出主要接口
from ai.core.llm_adapter import get_llm_adapter, BaseLLMAdapter
from ai.config import get_ai_config, validate_ai_config

__all__ = [
    'get_llm_adapter',
    'BaseLLMAdapter',
    'get_ai_config',
    'validate_ai_config',
]