"""
LLM 适配器单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.config import get_ai_config, validate_ai_config, update_ai_config, AI_CONFIG
from ai.core.errors import (
    LLMError, APIKeyError, RateLimitError, TimeoutError,
    ConnectionError, ModelNotFoundError, handle_llm_error, get_user_friendly_message
)
from ai.core.llm_adapter import BaseLLMAdapter, ZhipuAdapter, OpenAIAdapter, OllamaAdapter, get_llm_adapter


class TestAIConfig:
    """AI 配置测试"""
    
    def test_get_ai_config_default(self):
        """测试获取默认配置"""
        config = get_ai_config()
        assert config is not None
        assert 'llm_provider' in config
        assert 'providers' in config
    
    def test_get_ai_config_with_key(self):
        """测试通过键获取配置"""
        provider = get_ai_config('llm_provider')
        assert provider == 'zhipu'
    
    def test_get_ai_config_nested_key(self):
        """测试嵌套键获取配置"""
        model = get_ai_config('providers.zhipu.model')
        assert model is not None
        assert isinstance(model, str)
    
    def test_get_ai_config_default_value(self):
        """测试默认值"""
        value = get_ai_config('nonexistent.key', 'default')
        assert value == 'default'
    
    def test_validate_ai_config(self):
        """测试配置验证"""
        result = validate_ai_config()
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result


class TestErrors:
    """错误处理测试"""
    
    def test_llm_error(self):
        """测试基础 LLM 错误"""
        error = LLMError("测试错误", "详细信息")
        assert error.message == "测试错误"
        assert error.details == "详细信息"
        
        error_dict = error.to_dict()
        assert error_dict['error_type'] == 'LLMError'
        assert error_dict['message'] == "测试错误"
    
    def test_api_key_error(self):
        """测试 API Key 错误"""
        error = APIKeyError("智谱", "Key无效")
        assert "智谱" in error.message
        assert error.provider == "智谱"
    
    def test_rate_limit_error(self):
        """测试限流错误"""
        error = RateLimitError("智谱", retry_after=60)
        assert "智谱" in error.message
        assert error.retry_after == 60
    
    def test_timeout_error(self):
        """测试超时错误"""
        error = TimeoutError("智谱", timeout_seconds=30)
        assert "智谱" in error.message
        assert error.timeout_seconds == 30
    
    def test_handle_llm_error_rate_limit(self):
        """测试限流错误处理"""
        error = RateLimitError("智谱", retry_after=60)
        result = handle_llm_error(error)
        
        assert result['success'] == False
        assert result['error_type'] == 'RATE_LIMIT'
        assert result['retry_suggested'] == True
        assert result['retry_after'] == 60
    
    def test_handle_llm_error_api_key(self):
        """测试 API Key 错误处理"""
        error = APIKeyError("智谱")
        result = handle_llm_error(error)
        
        assert result['success'] == False
        assert result['error_type'] == 'API_KEY_INVALID'
        assert result['retry_suggested'] == False
    
    def test_handle_unknown_error(self):
        """测试未知错误处理"""
        error = Exception("未知错误")
        result = handle_llm_error(error)
        
        assert result['success'] == False
        assert result['error_type'] == 'UNKNOWN_ERROR'
    
    def test_get_user_friendly_message(self):
        """测试用户友好消息"""
        error = RateLimitError("智谱")
        message = get_user_friendly_message(error)
        
        assert "繁忙" in message or "稍后" in message


class TestLLMAdapter:
    """LLM 适配器测试"""
    
    def test_get_llm_adapter_zhipu(self):
        """测试获取智谱适配器"""
        adapter = get_llm_adapter('zhipu')
        assert isinstance(adapter, ZhipuAdapter)
        assert adapter.provider_name == "智谱"
    
    def test_get_llm_adapter_openai(self):
        """测试获取 OpenAI 适配器"""
        adapter = get_llm_adapter('openai')
        assert isinstance(adapter, OpenAIAdapter)
        assert adapter.provider_name == "OpenAI"
    
    def test_get_llm_adapter_ollama(self):
        """测试获取 Ollama 适配器"""
        adapter = get_llm_adapter('ollama')
        assert isinstance(adapter, OllamaAdapter)
        assert adapter.provider_name == "Ollama"
    
    def test_get_llm_adapter_invalid(self):
        """测试无效提供商"""
        with pytest.raises(ValueError):
            get_llm_adapter('invalid_provider')
    
    def test_zhipu_adapter_init(self):
        """测试智谱适配器初始化"""
        adapter = ZhipuAdapter(api_key="test_key", model="glm-4-flash")
        assert adapter.api_key == "test_key"
        assert adapter.model == "glm-4-flash"
    
    def test_zhipu_adapter_no_api_key(self):
        """测试智谱适配器无 API Key"""
        adapter = ZhipuAdapter(api_key="")
        with pytest.raises(APIKeyError):
            adapter.chat([{"role": "user", "content": "test"}])
    
    def test_zhipu_test_connection_no_key(self):
        """测试连接检测无 API Key"""
        adapter = ZhipuAdapter(api_key="")
        result = adapter.test_connection()
        
        assert result['success'] == False
        assert "API Key" in result['message']
    
    def test_adapter_stats(self):
        """测试适配器统计"""
        adapter = ZhipuAdapter(api_key="test_key")
        stats = adapter.get_stats()
        
        assert 'provider' in stats
        assert 'total_requests' in stats
        assert stats['provider'] == "智谱"


class TestZhipuAdapterWithMock:
    """智谱适配器 Mock 测试"""
    
    @patch('ai.core.llm_adapter.ZhipuAdapter._get_client')
    def test_chat_success(self, mock_get_client):
        """测试成功的对话请求"""
        # 创建 Mock 客户端
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "这是测试响应"
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_get_client.return_value = mock_client
        
        adapter = ZhipuAdapter(api_key="test_key")
        response = adapter.chat([{"role": "user", "content": "你好"}])
        
        assert response == "这是测试响应"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('ai.core.llm_adapter.ZhipuAdapter._get_client')
    def test_stream_chat(self, mock_get_client):
        """测试流式对话"""
        # 创建 Mock 客户端
        mock_client = MagicMock()
        
        # 创建 Mock 流式响应
        mock_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="这"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="是"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="测试"))]),
        ]
        mock_client.chat.completions.create.return_value = iter(mock_chunks)
        
        mock_get_client.return_value = mock_client
        
        adapter = ZhipuAdapter(api_key="test_key")
        chunks = list(adapter.stream_chat([{"role": "user", "content": "你好"}]))
        
        assert chunks == ["这", "是", "测试"]


class TestOllamaAdapter:
    """Ollama 适配器测试"""
    
    def test_ollama_adapter_init(self):
        """测试 Ollama 适配器初始化"""
        adapter = OllamaAdapter(base_url="http://localhost:11434", model="qwen2.5:14b")
        assert adapter.base_url == "http://localhost:11434"
        assert adapter.model == "qwen2.5:14b"
    
    @patch('requests.get')
    def test_ollama_test_connection_success(self, mock_get):
        """测试 Ollama 连接成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "qwen2.5:14b"}, {"name": "llama2"}]
        }
        mock_get.return_value = mock_response
        
        adapter = OllamaAdapter()
        result = adapter.test_connection()
        
        assert result['success'] == True
        assert "qwen2.5:14b" in result['message']
    
    @patch('requests.get')
    def test_ollama_test_connection_failure(self, mock_get):
        """测试 Ollama 连接失败"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        adapter = OllamaAdapter()
        result = adapter.test_connection()
        
        assert result['success'] == False
        assert "无法连接" in result['message']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])