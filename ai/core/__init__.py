"""
AI 核心模块
包含 LLM 接入层、Prompt 构建器、上下文管理器
"""

from ai.core.llm_adapter import BaseLLMAdapter, get_llm_adapter
from ai.core.errors import LLMError, APIKeyError, RateLimitError, TimeoutError
from ai.core.prompt_builder import PromptBuilder, build_diagnosis_prompt, build_qa_prompt
from ai.core.context_manager import ContextManager, SessionContextManager, get_context, get_session_manager

__all__ = [
    # LLM Adapter
    'BaseLLMAdapter',
    'get_llm_adapter',
    
    # Errors
    'LLMError',
    'APIKeyError',
    'RateLimitError',
    'TimeoutError',
    
    # Prompt Builder
    'PromptBuilder',
    'build_diagnosis_prompt',
    'build_qa_prompt',
    
    # Context Manager
    'ContextManager',
    'SessionContextManager',
    'get_context',
    'get_session_manager',
]
