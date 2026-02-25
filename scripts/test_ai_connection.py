"""
测试 AI 模块连接
验证智谱 BigModel API 是否可用
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载 .env 文件
from pathlib import Path
from ai.config import validate_ai_config, get_masked_api_key, get_ai_config, set_provider_api_key
from ai.core.llm_adapter import get_llm_adapter, quick_chat


def load_env_file():
    """手动加载 .env 文件"""
    env_file = Path(__file__).parent.parent / 'config' / '.env'
    
    if not env_file.exists():
        print(f"⚠️ .env 文件不存在: {env_file}")
        print("请复制 config/.env.example 为 config/.env 并填写 API Key")
        return False
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            # 解析 KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    
    return True


def test_connection():
    """测试智谱 API 连接"""
    
    print("=" * 50)
    print("🤖 AI 模块连接测试")
    print("=" * 50)
    
    # 1. 加载 .env 文件
    print("\n📂 加载配置文件...")
    if not load_env_file():
        return False
    
    # 2. 检查 API Key
    api_key = os.environ.get('ZHIPU_API_KEY', '')
    if not api_key or api_key == 'your_zhipu_api_key_here':
        print("❌ ZHIPU_API_KEY 未配置")
        print("请在 config/.env 文件中设置 ZHIPU_API_KEY")
        return False
    
    # 设置 API Key 到配置
    set_provider_api_key('zhipu', api_key, persist=False)
    print(f"✅ API Key 已加载: {get_masked_api_key('zhipu')}")
    
    # 3. 验证配置
    print("\n📋 配置验证...")
    validation = validate_ai_config()
    print(f"   - 配置有效: {validation['valid']}")
    if validation['errors']:
        print(f"   - 错误: {validation['errors']}")
    if validation['warnings']:
        print(f"   - 警告: {validation['warnings']}")
    
    # 4. 获取适配器
    print("\n🔌 获取 LLM 适配器...")
    adapter = get_llm_adapter('zhipu')
    print(f"   - 提供商: {adapter.provider_name}")
    print(f"   - 模型: {adapter.model}")
    print(f"   - Base URL: {adapter.base_url}")
    
    # 5. 测试连接
    print("\n🌐 测试 API 连接...")
    result = adapter.test_connection()
    
    print(f"   - 连接成功: {result['success']}")
    print(f"   - 消息: {result['message']}")
    print(f"   - 延迟: {result['latency_ms']} ms")
    
    if result['success']:
        print(f"   - 响应预览: {result.get('response', 'N/A')}")
    
    # 6. 测试简单对话
    if result['success']:
        print("\n💬 测试对话功能...")
        try:
            response = quick_chat(
                "请用一句话介绍你自己",
                system_prompt="你是一个友好的AI助手，请简洁回答",
                provider='zhipu'
            )
            print(f"   - AI 响应: {response}")
            print("\n✅ AI 模块测试全部通过！")
        except Exception as e:
            print(f"   - 对话失败: {e}")
    
    print("\n" + "=" * 50)
    return result['success']


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)