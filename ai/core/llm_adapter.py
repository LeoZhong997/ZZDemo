"""
LLM 统一接入层
提供统一的 LLM 接口，支持多厂商切换
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Generator, Optional
import time
import logging

from ai.config import get_ai_config
from ai.core.errors import (
    LLMError, APIKeyError, RateLimitError, TimeoutError,
    ConnectionError, ModelNotFoundError, ResponseParseError
)

# 配置日志
logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """
    LLM 适配器基类
    定义统一接口，所有具体适配器必须实现这些方法
    """
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self._last_request_time = 0
        self._request_count = 0
    
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """
        发送对话请求
        
        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数（temperature, max_tokens 等）
            
        Returns:
            模型响应文本
            
        Raises:
            LLMError: 各种 LLM 错误
        """
        pass
    
    @abstractmethod
    def stream_chat(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """
        流式对话 - 逐步返回响应
        
        Args:
            messages: 对话消息列表
            **kwargs: 额外参数
            
        Yields:
            响应文本片段
            
        Raises:
            LLMError: 各种 LLM 错误
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        测试连接性
        
        Returns:
            {"success": bool, "message": str, "latency_ms": int}
        """
        pass
    
    def _record_request(self):
        """记录请求信息"""
        self._last_request_time = time.time()
        self._request_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取请求统计"""
        return {
            "provider": self.provider_name,
            "total_requests": self._request_count,
            "last_request_time": self._last_request_time
        }


class ZhipuAdapter(BaseLLMAdapter):
    """
    智谱 BigModel 适配器
    使用 OpenAI Compatible 接口
    """
    
    def __init__(self, api_key: str = None, model: str = None, **kwargs):
        """
        初始化智谱适配器
        
        Args:
            api_key: 智谱 API Key，如果不提供则从配置读取
            model: 模型名称，默认从配置读取
            **kwargs: 其他配置参数
        """
        super().__init__("智谱")
        
        # 从配置获取参数
        config = get_ai_config('providers.zhipu', {})
        
        self.api_key = api_key or config.get('api_key', '')
        self.base_url = kwargs.get('base_url', config.get('base_url', 'https://open.bigmodel.cn/api/paas/v4'))
        self.model = model or config.get('model', 'glm-4-flash')
        self.timeout = kwargs.get('timeout', config.get('timeout', 60))
        self.max_tokens = kwargs.get('max_tokens', config.get('max_tokens', 2000))
        self.temperature = kwargs.get('temperature', config.get('temperature', 0.7))
        
        # 延迟导入 openai
        self._client = None
    
    def _get_client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
            except ImportError:
                raise LLMError("请安装 openai 库: pip install openai")
        
        return self._client
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """
        发送对话请求
        
        Args:
            messages: 对话消息列表
            **kwargs: 额外参数
            
        Returns:
            模型响应文本
        """
        if not self.api_key:
            raise APIKeyError("智谱", "API Key 未配置")
        
        # 合并参数
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        model = kwargs.get('model', self.model)
        
        try:
            client = self._get_client()
            self._record_request()
            
            logger.info(f"智谱 API 请求: model={model}, messages_count={len(messages)}")
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            logger.info(f"智谱 API 响应成功: length={len(content)}")
            
            return content
            
        except Exception as e:
            return self._handle_api_error(e)
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """
        流式对话
        
        Args:
            messages: 对话消息列表
            **kwargs: 额外参数
            
        Yields:
            响应文本片段
        """
        if not self.api_key:
            raise APIKeyError("智谱", "API Key 未配置")
        
        # 合并参数
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        model = kwargs.get('model', self.model)
        
        try:
            client = self._get_client()
            self._record_request()
            
            logger.info(f"智谱 API 流式请求: model={model}")
            
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise self._handle_api_error(e)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试连接性
        
        Returns:
            {"success": bool, "message": str, "latency_ms": int}
        """
        if not self.api_key:
            return {
                "success": False,
                "message": "API Key 未配置",
                "latency_ms": 0
            }
        
        try:
            start_time = time.time()
            
            # 发送一个简单的测试请求
            response = self.chat([
                {"role": "user", "content": "请回复'连接成功'"}
            ], max_tokens=10)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "message": f"连接成功，模型: {self.model}",
                "latency_ms": latency_ms,
                "response": response[:50]  # 只显示前50字符
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "latency_ms": 0
            }
    
    def _handle_api_error(self, error: Exception) -> None:
        """处理 API 错误"""
        error_str = str(error).lower()
        
        if "api key" in error_str or "unauthorized" in error_str or "401" in error_str:
            raise APIKeyError("智谱", str(error))
        
        elif "rate limit" in error_str or "429" in error_str:
            raise RateLimitError("智谱")
        
        elif "timeout" in error_str or "timed out" in error_str:
            raise TimeoutError("智谱", self.timeout)
        
        elif "connection" in error_str or "network" in error_str:
            raise ConnectionError("智谱", str(error))
        
        elif "model" in error_str and "not found" in error_str:
            raise ModelNotFoundError(self.model, "智谱")
        
        else:
            raise LLMError(f"智谱 API 调用失败: {error}")


class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI 适配器（备用）
    """
    
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None, **kwargs):
        """
        初始化 OpenAI 适配器
        
        Args:
            api_key: OpenAI API Key
            model: 模型名称
            base_url: API 基础 URL（用于代理）
            **kwargs: 其他配置参数
        """
        super().__init__("OpenAI")
        
        config = get_ai_config('providers.openai', {})
        
        self.api_key = api_key or config.get('api_key', '')
        self.base_url = base_url or config.get('base_url', 'https://api.openai.com/v1')
        self.model = model or config.get('model', 'gpt-4o')
        self.timeout = kwargs.get('timeout', config.get('timeout', 60))
        self.max_tokens = kwargs.get('max_tokens', config.get('max_tokens', 2000))
        self.temperature = kwargs.get('temperature', config.get('temperature', 0.7))
        
        self._client = None
    
    def _get_client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
            except ImportError:
                raise LLMError("请安装 openai 库: pip install openai")
        
        return self._client
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送对话请求"""
        if not self.api_key:
            raise APIKeyError("OpenAI", "API Key 未配置")
        
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        model = kwargs.get('model', self.model)
        
        try:
            client = self._get_client()
            self._record_request()
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return self._handle_api_error(e)
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """流式对话"""
        if not self.api_key:
            raise APIKeyError("OpenAI", "API Key 未配置")
        
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        model = kwargs.get('model', self.model)
        
        try:
            client = self._get_client()
            self._record_request()
            
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise self._handle_api_error(e)
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接性"""
        if not self.api_key:
            return {
                "success": False,
                "message": "API Key 未配置",
                "latency_ms": 0
            }
        
        try:
            start_time = time.time()
            response = self.chat([
                {"role": "user", "content": "Hello"}
            ], max_tokens=10)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "message": f"连接成功，模型: {self.model}",
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "latency_ms": 0
            }
    
    def _handle_api_error(self, error: Exception) -> None:
        """处理 API 错误"""
        error_str = str(error).lower()
        
        if "api key" in error_str or "unauthorized" in error_str or "401" in error_str:
            raise APIKeyError("OpenAI", str(error))
        elif "rate limit" in error_str or "429" in error_str:
            raise RateLimitError("OpenAI")
        elif "timeout" in error_str:
            raise TimeoutError("OpenAI", self.timeout)
        elif "connection" in error_str:
            raise ConnectionError("OpenAI", str(error))
        else:
            raise LLMError(f"OpenAI API 调用失败: {error}")


class OllamaAdapter(BaseLLMAdapter):
    """
    本地 Ollama 适配器（备用）
    """
    
    def __init__(self, base_url: str = None, model: str = None, **kwargs):
        """
        初始化 Ollama 适配器
        
        Args:
            base_url: Ollama 服务地址
            model: 模型名称
            **kwargs: 其他配置参数
        """
        super().__init__("Ollama")
        
        config = get_ai_config('providers.ollama', {})
        
        self.base_url = base_url or config.get('base_url', 'http://localhost:11434')
        self.model = model or config.get('model', 'qwen2.5:14b')
        self.timeout = kwargs.get('timeout', config.get('timeout', 120))
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送对话请求"""
        import requests
        
        model = kwargs.get('model', self.model)
        
        try:
            self._record_request()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                raise ModelNotFoundError(model, "Ollama")
            
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama", self.timeout)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Ollama", "请确保 Ollama 服务正在运行")
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMError(f"Ollama 调用失败: {e}")
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """流式对话"""
        import requests
        
        model = kwargs.get('model', self.model)
        
        try:
            self._record_request()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True
                },
                timeout=self.timeout,
                stream=True
            )
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
                        
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMError(f"Ollama 流式调用失败: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接性"""
        try:
            import requests
            
            start_time = time.time()
            
            # 检查 Ollama 服务状态
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                latency_ms = int((time.time() - start_time) * 1000)
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                
                return {
                    "success": True,
                    "message": f"Ollama 服务可用，已安装模型: {', '.join(model_names[:3])}",
                    "latency_ms": latency_ms
                }
            else:
                return {
                    "success": False,
                    "message": f"Ollama 服务响应异常: {response.status_code}",
                    "latency_ms": 0
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到 Ollama 服务，请确保服务正在运行",
                "latency_ms": 0
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "latency_ms": 0
            }


def get_llm_adapter(provider: str = None, **kwargs) -> BaseLLMAdapter:
    """
    工厂函数：根据配置返回对应的 LLM 适配器
    
    Args:
        provider: 提供商名称 (zhipu/openai/ollama)，如果为 None 则从配置读取
        **kwargs: 额外配置参数，会传递给适配器构造函数
        
    Returns:
        LLM 适配器实例
        
    Raises:
        ValueError: 不支持的提供商
    """
    if provider is None:
        provider = get_ai_config('llm_provider', 'zhipu')
    
    provider = provider.lower()
    
    adapters = {
        'zhipu': ZhipuAdapter,
        'openai': OpenAIAdapter,
        'ollama': OllamaAdapter
    }
    
    if provider not in adapters:
        raise ValueError(f"不支持的 LLM 提供商: {provider}，支持的提供商: {list(adapters.keys())}")
    
    return adapters[provider](**kwargs)


def quick_chat(message: str, system_prompt: str = None, provider: str = None) -> str:
    """
    快速对话的便捷函数
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词（可选）
        provider: 提供商名称（可选）
        
    Returns:
        模型响应
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": message})
    
    adapter = get_llm_adapter(provider)
    return adapter.chat(messages)