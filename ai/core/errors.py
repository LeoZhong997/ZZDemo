"""
AI 模块错误处理
定义 LLM 相关的异常类和统一错误处理
"""
from typing import Dict, Any, Optional


class LLMError(Exception):
    """
    LLM 错误基类
    所有 LLM 相关异常都继承此类
    """
    
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class APIKeyError(LLMError):
    """
    API Key 配置错误
    当 API Key 未配置或无效时抛出
    """
    
    def __init__(self, provider: str = "unknown", details: Optional[str] = None):
        message = f"{provider} API Key 未配置或无效"
        super().__init__(message, details)
        self.provider = provider


class RateLimitError(LLMError):
    """
    API 限流错误
    当请求频率超过限制时抛出
    """
    
    def __init__(self, provider: str = "unknown", retry_after: Optional[int] = None):
        message = f"{provider} API 请求频率超限"
        details = f"请在 {retry_after} 秒后重试" if retry_after else "请稍后重试"
        super().__init__(message, details)
        self.provider = provider
        self.retry_after = retry_after


class TimeoutError(LLMError):
    """
    请求超时错误
    当 API 请求超时时抛出
    """
    
    def __init__(self, provider: str = "unknown", timeout_seconds: Optional[int] = None):
        message = f"{provider} API 请求超时"
        details = f"超时时间: {timeout_seconds} 秒" if timeout_seconds else "请求超时"
        super().__init__(message, details)
        self.provider = provider
        self.timeout_seconds = timeout_seconds


class ConnectionError(LLMError):
    """
    连接错误
    当无法连接到 LLM 服务时抛出
    """
    
    def __init__(self, provider: str = "unknown", details: Optional[str] = None):
        message = f"无法连接到 {provider} 服务"
        super().__init__(message, details)
        self.provider = provider


class ModelNotFoundError(LLMError):
    """
    模型不存在错误
    当指定的模型不存在时抛出
    """
    
    def __init__(self, model: str, provider: str = "unknown"):
        message = f"模型 '{model}' 在 {provider} 中不存在"
        super().__init__(message)
        self.model = model
        self.provider = provider


class ResponseParseError(LLMError):
    """
    响应解析错误
    当无法解析 LLM 响应时抛出
    """
    
    def __init__(self, details: Optional[str] = None, raw_response: Optional[str] = None):
        message = "无法解析 LLM 响应"
        super().__init__(message, details)
        self.raw_response = raw_response


class ContextTooLongError(LLMError):
    """
    上下文过长错误
    当输入上下文超过模型限制时抛出
    """
    
    def __init__(self, current_length: int, max_length: int):
        message = f"上下文长度 ({current_length}) 超过模型限制 ({max_length})"
        super().__init__(message)
        self.current_length = current_length
        self.max_length = max_length


def handle_llm_error(error: Exception) -> Dict[str, Any]:
    """
    统一错误处理
    
    Args:
        error: 异常对象
        
    Returns:
        {"success": False, "error_type": str, "message": str, "retry_suggested": bool, "details": str}
    """
    if isinstance(error, RateLimitError):
        return {
            "success": False,
            "error_type": "RATE_LIMIT",
            "message": error.message,
            "details": error.details,
            "retry_suggested": True,
            "retry_after": error.retry_after
        }
    
    elif isinstance(error, TimeoutError):
        return {
            "success": False,
            "error_type": "TIMEOUT",
            "message": error.message,
            "details": error.details,
            "retry_suggested": True
        }
    
    elif isinstance(error, APIKeyError):
        return {
            "success": False,
            "error_type": "API_KEY_INVALID",
            "message": error.message,
            "details": "请检查 API Key 配置，确保已正确设置",
            "retry_suggested": False
        }
    
    elif isinstance(error, ConnectionError):
        return {
            "success": False,
            "error_type": "CONNECTION_ERROR",
            "message": error.message,
            "details": error.details or "请检查网络连接",
            "retry_suggested": True
        }
    
    elif isinstance(error, ModelNotFoundError):
        return {
            "success": False,
            "error_type": "MODEL_NOT_FOUND",
            "message": error.message,
            "details": "请检查模型名称是否正确",
            "retry_suggested": False
        }
    
    elif isinstance(error, ResponseParseError):
        return {
            "success": False,
            "error_type": "RESPONSE_PARSE_ERROR",
            "message": error.message,
            "details": error.details,
            "retry_suggested": True
        }
    
    elif isinstance(error, ContextTooLongError):
        return {
            "success": False,
            "error_type": "CONTEXT_TOO_LONG",
            "message": error.message,
            "details": "请减少输入内容长度",
            "retry_suggested": False
        }
    
    elif isinstance(error, LLMError):
        return {
            "success": False,
            "error_type": "LLM_ERROR",
            "message": error.message,
            "details": error.details,
            "retry_suggested": True
        }
    
    else:
        # 未知错误
        return {
            "success": False,
            "error_type": "UNKNOWN_ERROR",
            "message": "发生未知错误",
            "details": str(error),
            "retry_suggested": True
        }


def get_user_friendly_message(error: Exception) -> str:
    """
    获取用户友好的错误信息
    
    Args:
        error: 异常对象
        
    Returns:
        用户友好的错误信息
    """
    error_info = handle_llm_error(error)
    
    messages = {
        "RATE_LIMIT": "AI 服务繁忙，请稍后再试 ⏳",
        "TIMEOUT": "AI 响应超时，请重试 ⏰",
        "API_KEY_INVALID": "AI 服务配置错误，请联系管理员 🔑",
        "CONNECTION_ERROR": "网络连接失败，请检查网络 🌐",
        "MODEL_NOT_FOUND": "AI 模型暂时不可用 🔧",
        "RESPONSE_PARSE_ERROR": "AI 响应解析失败，请重试 📝",
        "CONTEXT_TOO_LONG": "输入内容过长，请精简后重试 📄",
        "LLM_ERROR": "AI 服务异常，请稍后重试 🤖",
        "UNKNOWN_ERROR": "发生未知错误，请稍后重试 ❓"
    }
    
    return messages.get(error_info["error_type"], "操作失败，请稍后重试")