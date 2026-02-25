"""
AI 模块配置文件
包含 LLM 提供商配置、功能开关、分析参数等
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# ========== 加载 .env 文件 ==========
# 尝试从 python-dotenv 加载环境变量
try:
    from dotenv import load_dotenv
    # 加载 config/.env 文件
    config_dir = Path(__file__).parent.parent / 'config'
    env_file = config_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # 如果没有安装 python-dotenv，跳过

# ========== 项目路径配置 ==========
CONFIG_DIR = Path(__file__).parent.parent / 'config'
AI_SETTINGS_FILE = CONFIG_DIR / 'ai_settings.json'

# ========== LLM 提供商配置 ==========
AI_CONFIG: Dict[str, Any] = {
    # 默认LLM提供商
    'llm_provider': 'zhipu',
    
    # 各提供商配置
    'providers': {
        'zhipu': {
            'api_key': os.getenv('ZHIPU_API_KEY', ''),
            'base_url': 'https://open.bigmodel.cn/api/paas/v4',  # OpenAI Compatible接口
            'model': 'glm-4-flash',  # 可选: glm-4-flash, glm-4, glm-4-plus
            'timeout': 60,
            'max_tokens': 2000,
            'temperature': 0.7,
            'context_window': 128000  # 上下文窗口大小
        },
        'openai': {
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'model': 'gpt-4o',
            'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            'timeout': 60,
            'max_tokens': 2000,
            'temperature': 0.7
        },
        'ollama': {
            'base_url': 'http://localhost:11434',
            'model': 'qwen2.5:14b',
            'timeout': 120
        }
    },
    
    # 功能开关
    'features': {
        'diagnosis': True,
        'prediction': True,
        'qa_chat': True,
        'suggestion': True
    },
    
    # 分析参数
    'analysis': {
        'min_data_days': 7,
        'prediction_days': 7,
        'anomaly_threshold': 2.0,
        'top_n_stores': 10
    },
    
    # Prompt配置
    'prompt': {
        'max_context_length': 8000,
        'system_prompt': '''你是一个专业的外卖经营分析助手，具有以下能力：

1. **数据分析**：能够分析外卖经营数据，包括营收、订单量、转化率、到手率等核心指标
2. **趋势洞察**：识别数据趋势，发现异常情况，提供预警
3. **对比分析**：门店对比、平台对比、时间段对比
4. **决策建议**：基于数据给出可执行的经营建议

## 分析原则
- 数据驱动：所有分析都要有数据支撑
- 简洁明了：避免冗长，突出重点
- 可操作性：建议要具体、可执行
- 业务导向：关注对经营有影响的指标

## 回答格式
- 使用中文回答
- 适当使用 Markdown 格式
- 重要数据用 **粗体** 标注
- 列表建议使用编号形式'''
    },
    
    # 缓存配置
    'cache': {
        'enabled': True,
        'ttl_seconds': 3600  # 1小时
    }
}


def get_ai_config(key: str = None, default: Any = None) -> Any:
    """
    获取AI配置
    
    Args:
        key: 配置键，支持点分隔符如 'providers.zhipu.model'
        default: 默认值
        
    Returns:
        配置值
    """
    # 先尝试从用户配置文件加载
    user_config = _load_user_settings()
    merged_config = _deep_merge(AI_CONFIG, user_config)
    
    if key is None:
        return merged_config
    
    # 支持点分隔符访问嵌套配置
    keys = key.split('.')
    value = merged_config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def update_ai_config(key: str, value: Any, persist: bool = False) -> None:
    """
    更新AI配置（运行时）
    
    Args:
        key: 配置键
        value: 新值
        persist: 是否持久化到配置文件
    """
    keys = key.split('.')
    config = AI_CONFIG
    
    # 导航到目标位置
    for k in keys[:-1]:
        if k not in config:
            config[k] = {}
        config = config[k]
    
    # 设置值
    config[keys[-1]] = value
    
    # 如果需要持久化
    if persist:
        _save_user_settings({key: value})


def validate_ai_config() -> Dict[str, Any]:
    """
    验证AI配置完整性
    
    Returns:
        {"valid": bool, "errors": list, "warnings": list}
    """
    errors = []
    warnings = []
    
    # 检查默认提供商配置
    provider = get_ai_config('llm_provider')
    provider_config = get_ai_config(f'providers.{provider}')
    
    if not provider_config:
        errors.append(f"提供商 '{provider}' 配置不存在")
    else:
        # 检查 API Key（根据提供商类型）
        if provider == 'zhipu':
            api_key = get_ai_config('providers.zhipu.api_key')
            if not api_key:
                errors.append("智谱 API Key 未配置，请设置 ZHIPU_API_KEY 环境变量或在配置中设置")
        elif provider == 'openai':
            api_key = get_ai_config('providers.openai.api_key')
            if not api_key:
                warnings.append("OpenAI API Key 未配置")
    
    # 检查功能开关
    features = get_ai_config('features')
    if not any(features.values()):
        warnings.append("所有 AI 功能均已关闭")
    
    # 检查分析参数
    min_days = get_ai_config('analysis.min_data_days')
    if min_days < 3:
        warnings.append(f"最小数据天数 {min_days} 天可能太少，建议至少 7 天")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def set_provider_api_key(provider: str, api_key: str, persist: bool = True) -> bool:
    """
    设置提供商的 API Key
    
    Args:
        provider: 提供商名称 (zhipu/openai)
        api_key: API Key
        persist: 是否持久化
        
    Returns:
        是否设置成功
    """
    if provider not in ['zhipu', 'openai']:
        return False
    
    update_ai_config(f'providers.{provider}.api_key', api_key)
    
    if persist:
        _save_user_settings({
            'providers': {
                provider: {
                    'api_key': api_key
                }
            }
        })
    
    return True


def get_masked_api_key(provider: str) -> str:
    """
    获取脱敏的 API Key（用于显示）
    
    Args:
        provider: 提供商名称
        
    Returns:
        脱敏后的 API Key，如 "sk-****xxxx"
    """
    api_key = get_ai_config(f'providers.{provider}.api_key', '')
    
    if not api_key:
        return "未配置"
    
    if len(api_key) <= 8:
        return "****"
    
    # 显示前4位和后4位
    return f"{api_key[:4]}****{api_key[-4:]}"


def _load_user_settings() -> Dict[str, Any]:
    """加载用户配置文件"""
    if not AI_SETTINGS_FILE.exists():
        return {}
    
    try:
        with open(AI_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_user_settings(settings: Dict[str, Any]) -> bool:
    """保存用户配置到文件"""
    try:
        # 确保目录存在
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # 读取现有配置
        existing = _load_user_settings()
        
        # 合并新配置
        merged = _deep_merge(existing, settings)
        
        # 保存
        with open(AI_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并两个字典"""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


# 模块加载时检查配置
def _init_config():
    """初始化配置"""
    # 尝试从环境变量加载 API Key
    zhipu_key = os.getenv('ZHIPU_API_KEY', '')
    if zhipu_key:
        AI_CONFIG['providers']['zhipu']['api_key'] = zhipu_key
    
    openai_key = os.getenv('OPENAI_API_KEY', '')
    if openai_key:
        AI_CONFIG['providers']['openai']['api_key'] = openai_key


# 执行初始化
_init_config()