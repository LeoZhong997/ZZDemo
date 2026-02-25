# AI 经营决策功能 - 技术规格说明书

> **本文档目的**：提供完整的AI经营决策功能技术规格，指导后续开发实现
> 
> **适用场景**：功能开发、代码实现、团队协作、技术文档

---

## 1. 功能概述

### 1.1 功能定位

基于现有外卖数据ETL系统，接入大语言模型（智谱BigModel），实现AI驱动的经营决策辅助功能。

### 1.2 核心功能模块

| 模块 | 功能描述 | 优先级 |
|------|----------|--------|
| 智能诊断报告 | 门店对比、平台对比、异常检测、自动生成诊断报告 | P0 |
| 预测分析 | 营收预测、趋势预测、节假日效应分析 | P1 |
| 智能问答助手 | 自然语言交互、上下文对话、数据查询 | P1 |
| 决策建议引擎 | 推广建议、活动评估、预算分配建议 | P2 |

### 1.3 交互形式

- **Dashboard内嵌报告**：AI诊断报告页面、预测分析图表
- **对话式交互**：Chat界面，支持自然语言问答

### 1.4 分析优先级

门店对比 > 平台对比 > 趋势预测 > 活动评估

---

## 2. 技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dashboard 展示层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  AI诊断报告   │  │  预测分析图表  │  │   AI对话助手界面     │  │
│  │  (内嵌页面)   │  │  (内嵌页面)   │  │   (Chat界面)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI 服务层 (新增)                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LLM 接入层 (统一抽象)                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │   │
│  │  │ 智谱GLM  │ │ OpenAI  │ │通义千问  │ │ 本地Ollama  │   │   │
│  │  │ (首选)  │ │         │ │         │ │             │   │   │
│  │  └────┬────┘ └─────────┘ └─────────┘ └─────────────┘   │   │
│  │       │                                                 │   │
│  │       ▼                                                 │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │           LLM Adapter 统一接口                    │   │   │
│  │  │           (可切换/可扩展)                         │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────── AI 功能引擎 ───────────────┐                 │
│  │                                           │                 │
│  │  ┌─────────────┐  ┌─────────────────────┐│                 │
│  │  │ 智能诊断引擎 │  │   预测分析引擎       ││                 │
│  │  │ - 门店对比   │  │ - 营收预测          ││                 │
│  │  │ - 平台对比   │  │ - 趋势预测          ││                 │
│  │  │ - 异常检测   │  │ - 节假日效应        ││                 │
│  │  └─────────────┘  └─────────────────────┘│                 │
│  │                                           │                 │
│  │  ┌─────────────┐  ┌─────────────────────┐│                 │
│  │  │ 决策建议引擎 │  │   智能问答引擎       ││                 │
│  │  │ - 推广建议   │  │ - 自然语言查询      ││                 │
│  │  │ - 活动评估   │  │ - 上下文对话        ││                 │
│  │  │ - 预算分配   │  │ - 多轮追问          ││                 │
│  │  └─────────────┘  └─────────────────────┘│                 │
│  └───────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据分析层 (新增)                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  数据聚合器   │  │  特征计算器   │  │   Prompt 构建器      │  │
│  │  - 门店汇总   │  │  - 同环比计算 │  │   - 数据注入         │  │
│  │  - 平台汇总   │  │  - 排名计算   │  │   - 模板渲染         │  │
│  │  - 时间序列   │  │  - 转化漏斗   │  │   - 上下文管理       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据存储层 (现有)                             │
│                    MySQL - daily_orders                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户请求 → Dashboard → AI引擎 → 数据分析层 → 数据库
                ↓
           LLM接入层 → 智谱API
                ↓
           AI响应 → Dashboard展示
```

---

## 3. 项目结构

### 3.1 新增目录结构

```
ZZDemo/
├── app.py                          # 主Dashboard (已有)
├── pages/
│   ├── 1_周报数据.py                # (已有)
│   ├── ai_insights.py              # 🆕 AI诊断报告页
│   └── ai_chat.py                  # 🆕 AI对话助手页
│
├── ai/                             # 🆕 AI模块根目录
│   ├── __init__.py
│   ├── config.py                   # 🆕 AI配置文件
│   │
│   ├── core/                       # AI核心模块
│   │   ├── __init__.py
│   │   ├── llm_adapter.py          # LLM统一接入层
│   │   ├── prompt_builder.py       # Prompt构建器
│   │   └── context_manager.py      # 对话上下文管理
│   │
│   ├── engines/                    # AI功能引擎
│   │   ├── __init__.py
│   │   ├── diagnosis_engine.py     # 智能诊断引擎
│   │   ├── prediction_engine.py    # 预测分析引擎
│   │   ├── suggestion_engine.py    # 决策建议引擎
│   │   └── qa_engine.py            # 智能问答引擎
│   │
│   ├── analytics/                  # 数据分析模块
│   │   ├── __init__.py
│   │   ├── data_aggregator.py      # 数据聚合器
│   │   ├── feature_calculator.py   # 特征计算器
│   │   ├── anomaly_detector.py     # 异常检测器
│   │   └── time_series.py          # 时间序列分析
│   │
│   └── prompts/                    # Prompt模板
│       ├── __init__.py
│       ├── diagnosis_prompts.py    # 诊断类Prompt
│       ├── prediction_prompts.py   # 预测类Prompt
│       ├── suggestion_prompts.py   # 建议类Prompt
│       └── qa_prompts.py           # 问答类Prompt
│
└── docs/
    ├── project-specification.md    # (已有)
    └── ai-feature-specification.md # 本文档
```

### 3.2 文件职责说明

| 文件 | 职责 |
|------|------|
| `ai/core/llm_adapter.py` | LLM统一接入层，支持多厂商切换 |
| `ai/core/prompt_builder.py` | 构建和渲染Prompt模板 |
| `ai/core/context_manager.py` | 管理对话上下文和历史记录 |
| `ai/engines/diagnosis_engine.py` | 门店/平台对比诊断、异常检测 |
| `ai/engines/prediction_engine.py` | 营收预测、趋势分析 |
| `ai/engines/suggestion_engine.py` | 运营决策建议生成 |
| `ai/engines/qa_engine.py` | 自然语言问答处理 |
| `ai/analytics/data_aggregator.py` | 数据聚合和预处理 |
| `ai/analytics/feature_calculator.py` | 业务特征计算 |
| `ai/analytics/anomaly_detector.py` | 异常值检测算法 |
| `ai/analytics/time_series.py` | 时间序列分析工具 |
| `ai/config.py` | AI相关配置（API Key、模型参数等）|

---

## 4. 核心模块设计

### 4.1 LLM 接入层 (`ai/core/llm_adapter.py`)

#### 4.1.1 架构设计

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Generator

class BaseLLMAdapter(ABC):
    """LLM适配器基类 - 定义统一接口"""
    
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """
        发送对话请求
        
        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            
        Returns:
            模型响应文本
        """
        pass
    
    @abstractmethod
    def stream_chat(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """
        流式对话 - 逐步返回响应
        
        Args:
            messages: 对话消息列表
            
        Yields:
            响应文本片段
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


class ZhipuAdapter(BaseLLMAdapter):
    """智谱BigModel适配器（OpenAI Compatible接口）"""
    
    def __init__(self, api_key: str, model: str = "glm-5", **kwargs):
        """
        初始化智谱适配器
        
        Args:
            api_key: 智谱API Key
            model: 模型名称，可选 glm-5, glm-4.7, glm-4-plus 等
            **kwargs: 其他配置参数
        """
        pass
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送对话请求"""
        pass
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """流式对话"""
        pass
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接性"""
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI适配器（备用）"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None, **kwargs):
        """初始化OpenAI适配器"""
        pass
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送对话请求"""
        pass
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """流式对话"""
        pass
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接性"""
        pass


class OllamaAdapter(BaseLLMAdapter):
    """本地Ollama适配器（备用）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:14b", **kwargs):
        """初始化Ollama适配器"""
        pass
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送对话请求"""
        pass
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """流式对话"""
        pass
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接性"""
        pass


def get_llm_adapter(provider: str = None, **kwargs) -> BaseLLMAdapter:
    """
    工厂函数：根据配置返回对应的LLM适配器
    
    Args:
        provider: 提供商名称，如果为None则从配置读取
        **kwargs: 额外配置参数
        
    Returns:
        LLM适配器实例
    """
    pass
```

### 4.2 配置管理 (`ai/config.py`)

```python
import os
from typing import Dict, Any

# ========== LLM 提供商配置 ==========
AI_CONFIG: Dict[str, Any] = {
    # 默认LLM提供商
    'llm_provider': 'zhipu',
    
    # 各提供商配置
    'providers': {
        'zhipu': {
            'api_key': os.getenv('ZHIPU_API_KEY', ''),
            'base_url': 'https://open.bigmodel.cn/api/coding/paas/v4',  # OpenAI Compatible接口
            'model': 'glm-5',  # 可选: glm-5, glm-4.7, glm-4-plus
            'timeout': 60,
            'max_tokens': 2000,
            'temperature': 0.7,
            'context_window': 200000  # 上下文窗口大小
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
        'system_prompt': '''你是一个专业的外卖经营分析助手...'''
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
    pass


def update_ai_config(key: str, value: Any) -> None:
    """
    更新AI配置（运行时）
    
    Args:
        key: 配置键
        value: 新值
    """
    pass


def validate_ai_config() -> Dict[str, Any]:
    """
    验证AI配置完整性
    
    Returns:
        {"valid": bool, "errors": list, "warnings": list}
    """
    pass
```

---

## 5. AI 功能引擎

### 5.1 智能诊断引擎 (`ai/engines/diagnosis_engine.py`)

```python
from typing import Dict, Any, List
import pandas as pd

class DiagnosisEngine:
    """
    智能诊断引擎
    
    功能：
    - 门店对比分析
    - 平台对比分析
    - 异常检测
    - 生成诊断报告
    """
    
    def __init__(self, llm_adapter=None):
        """初始化诊断引擎"""
        pass
    
    def generate_full_diagnosis(self, df: pd.DataFrame, 
                                 period: str = "本周",
                                 top_n: int = 10) -> Dict[str, Any]:
        """
        生成完整诊断报告
        
        Args:
            df: 原始数据DataFrame
            period: 报告周期描述
            top_n: 排名展示数量
            
        Returns:
            {
                "store_ranking": {...},
                "platform_comparison": {...},
                "anomalies": [...],
                "summary": "AI生成的总结报告"
            }
        """
        pass
    
    def compare_stores(self, df: pd.DataFrame, 
                       store_names: List[str]) -> Dict[str, Any]:
        """
        指定门店对比分析
        
        Args:
            df: 数据
            store_names: 要对比的门店名称列表
            
        Returns:
            {"data": [...], "analysis": "AI对比分析"}
        """
        pass
    
    def compare_platforms(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        平台对比分析
        
        Args:
            df: 数据
            
        Returns:
            {"data": [...], "analysis": "AI对比分析"}
        """
        pass
```

### 5.2 预测分析引擎 (`ai/engines/prediction_engine.py`)

```python
from typing import Dict, Any, List
import pandas as pd

class PredictionEngine:
    """
    预测分析引擎
    
    功能：
    - 营收预测
    - 趋势分析
    - 节假日效应分析
    """
    
    def __init__(self, llm_adapter=None):
        """初始化预测引擎"""
        pass
    
    def predict_revenue(self, df: pd.DataFrame, 
                        days: int = 7,
                        include_confidence: bool = True) -> Dict[str, Any]:
        """
        营收预测
        
        Args:
            df: 历史数据
            days: 预测天数
            include_confidence: 是否包含置信区间
            
        Returns:
            {
                "predictions": [...],
                "trend": "上升/下降/平稳",
                "confidence": 0.85,
                "analysis": "AI分析说明"
            }
        """
        pass
    
    def analyze_trend(self, df: pd.DataFrame, 
                      metric: str = 'actual_income') -> Dict[str, Any]:
        """
        趋势分析
        
        Args:
            df: 数据
            metric: 分析指标
            
        Returns:
            {"trend": {...}, "analysis": "趋势分析报告"}
        """
        pass
    
    def analyze_holiday_effect(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        节假日效应分析
        
        Args:
            df: 数据
            
        Returns:
            {"holiday_impact": {...}, "analysis": "节假日影响分析"}
        """
        pass
```

### 5.3 智能问答引擎 (`ai/engines/qa_engine.py`)

```python
from typing import Dict, Any, List
import pandas as pd

class QAEngine:
    """
    智能问答引擎
    
    功能：
    - 自然语言查询
    - 上下文对话
    - 多轮追问
    """
    
    def __init__(self, llm_adapter=None, db_engine=None):
        """初始化问答引擎"""
        pass
    
    def ask(self, question: str, 
            context_df: pd.DataFrame = None,
            stream: bool = False) -> str:
        """
        回答用户问题
        
        Args:
            question: 用户问题
            context_df: 当前筛选的数据上下文
            stream: 是否流式输出
            
        Returns:
            AI回答
        """
        pass
    
    def clear_context(self):
        """清除对话上下文"""
        pass
    
    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        pass
```

### 5.4 决策建议引擎 (`ai/engines/suggestion_engine.py`)

```python
from typing import Dict, Any, List
import pandas as pd

class SuggestionEngine:
    """
    决策建议引擎
    
    功能：
    - 推广建议
    - 活动评估
    - 预算分配建议
    """
    
    def __init__(self, llm_adapter=None):
        """初始化建议引擎"""
        pass
    
    def generate_suggestions(self, df: pd.DataFrame,
                             focus_area: str = "all") -> Dict[str, Any]:
        """
        生成经营建议
        
        Args:
            df: 数据
            focus_area: 关注领域 (all/revenue/traffic/conversion/cost)
            
        Returns:
            {"issues": [...], "suggestions": "AI建议", "focus_area": str}
        """
        pass
    
    def evaluate_promotion(self, df: pd.DataFrame,
                           promotion_period: tuple) -> Dict[str, Any]:
        """
        评估活动效果
        
        Args:
            df: 数据
            promotion_period: 活动周期 (start_date, end_date)
            
        Returns:
            {"evaluation": "活动评估报告"}
        """
        pass
    
    def suggest_budget_allocation(self, df: pd.DataFrame,
                                   total_budget: float) -> Dict[str, Any]:
        """
        预算分配建议
        
        Args:
            df: 数据
            total_budget: 总预算
            
        Returns:
            {"allocation": {...}, "rationale": "分配理由"}
        """
        pass
```

---

## 6. 数据分析层

### 6.1 数据聚合器 (`ai/analytics/data_aggregator.py`)

```python
from typing import Dict, Any, List
import pandas as pd

class DataAggregator:
    """
    数据聚合器
    
    功能：
    - 门店维度聚合
    - 平台维度聚合
    - 时间维度聚合
    """
    
    def aggregate_by_store(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        按门店聚合数据
        
        Args:
            df: 原始数据
            
        Returns:
            包含门店指标的DataFrame
        """
        pass
    
    def aggregate_by_platform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        按平台聚合数据
        
        Args:
            df: 原始数据
            
        Returns:
            包含平台指标的DataFrame
        """
        pass
    
    def aggregate_by_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        按日期聚合数据
        
        Args:
            df: 原始数据
            
        Returns:
            包含日期指标的DataFrame
        """
        pass
    
    def calculate_growth_rate(self, current: float, previous: float) -> float:
        """
        计算增长率
        
        Args:
            current: 当前值
            previous: 之前值
            
        Returns:
            增长率百分比
        """
        pass
```

### 6.2 异常检测器 (`ai/analytics/anomaly_detector.py`)

```python
from typing import Dict, Any, List
import pandas as pd

class AnomalyDetector:
    """
    异常检测器
    
    功能：
    - 指标异常检测
    - 趋势异常检测
    """
    
    def __init__(self):
        """初始化异常检测器，从配置读取阈值"""
        pass
    
    def detect(self, df: pd.DataFrame, 
               metrics: List[str] = None) -> List[Dict[str, Any]]:
        """
        检测异常
        
        Args:
            df: 数据
            metrics: 要检测的指标列表
            
        Returns:
            异常列表
        """
        pass
    
    def detect_trend_anomaly(self, df: pd.DataFrame, 
                              metric: str = 'actual_income') -> List[Dict]:
        """
        检测趋势异常（突然下降或上升）
        
        Args:
            df: 数据
            metric: 检测指标
            
        Returns:
            趋势异常列表
        """
        pass
```

### 6.3 时间序列分析 (`ai/analytics/time_series.py`)

```python
from typing import Dict, Any, List
import pandas as pd

class TimeSeriesAnalyzer:
    """
    时间序列分析器
    
    功能：
    - 日度聚合
    - 趋势计算
    - 周期性分析
    """
    
    def aggregate_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        按日聚合数据
        
        Args:
            df: 原始数据
            
        Returns:
            日度聚合数据
        """
        pass
    
    def calculate_trend(self, daily_data: pd.DataFrame, 
                        metric: str = 'actual_income') -> Dict[str, Any]:
        """
        计算趋势
        
        Args:
            daily_data: 日度数据
            metric: 分析指标
            
        Returns:
            {"direction": "上升/下降/平稳", "strength": float, "daily_change": float}
        """
        pass
    
    def detect_seasonality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        检测周期性
        
        Args:
            df: 数据
            
        Returns:
            {"has_weekly_pattern": bool, "peak_day": str, "low_day": str}
        """
        pass
```

### 6.4 特征计算器 (`ai/analytics/feature_calculator.py`)

```python
from typing import Dict, Any, List
import pandas as pd

class FeatureCalculator:
    """
    特征计算器
    
    功能：
    - 同比/环比计算
    - 排名计算
    - 转化漏斗计算
    - 综合评分
    """
    
    def calculate_yoy_growth(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """计算同比增长率"""
        pass
    
    def calculate_wow_growth(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """计算环比增长率"""
        pass
    
    def calculate_ranking(self, df: pd.DataFrame, metric: str, 
                           ascending: bool = False) -> pd.DataFrame:
        """计算排名"""
        pass
    
    def calculate_funnel_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算转化漏斗指标
        
        Returns:
            {"exposure_to_entry": float, "entry_to_order": float, "overall_conversion": float}
        """
        pass
    
    def calculate_store_score(self, store_metrics: Dict) -> float:
        """计算门店综合评分 (0-100)"""
        pass
```

---

## 7. Prompt 构建器 (`ai/core/prompt_builder.py`)

```python
from typing import Dict, Any, List

class PromptBuilder:
    """
    Prompt构建器
    
    功能：
    - 构建各类Prompt模板
    - 数据注入
    - 模板渲染
    """
    
    def __init__(self):
        """初始化，从配置读取系统提示词"""
        pass
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass
    
    def build_diagnosis_prompt(self, 
                                store_ranking: Dict,
                                platform_comparison: Dict,
                                anomalies: List[Dict],
                                period: str) -> str:
        """构建诊断报告Prompt"""
        pass
    
    def build_prediction_prompt(self, 
                                 historical_data: List[Dict],
                                 predictions: List[Dict],
                                 trend: Dict) -> str:
        """构建预测分析Prompt"""
        pass
    
    def build_qa_prompt(self, question: str, relevant_data: Dict) -> str:
        """构建问答Prompt"""
        pass
    
    def build_suggestion_prompt(self,
                                 store_metrics: List[Dict],
                                 platform_metrics: List[Dict],
                                 issues: List[Dict],
                                 focus_area: str) -> str:
        """构建建议Prompt"""
        pass
    
    def build_store_comparison_prompt(self, comparison_data) -> str:
        """构建门店对比Prompt"""
        pass
    
    def build_trend_analysis_prompt(self, daily_data: List[Dict],
                                     metric: str, trend: Dict) -> str:
        """构建趋势分析Prompt"""
        pass
    
    def build_promotion_eval_prompt(self, before_data: Dict,
                                     during_data: Dict,
                                     after_data: Dict) -> str:
        """构建活动评估Prompt"""
        pass
```

---

## 8. 上下文管理器 (`ai/core/context_manager.py`)

```python
from typing import List, Dict

class ContextManager:
    """
    对话上下文管理器
    
    功能：
    - 管理对话历史
    - 限制上下文长度
    - 清理过期上下文
    """
    
    def __init__(self, max_turns: int = 10):
        """
        初始化上下文管理器
        
        Args:
            max_turns: 最大对话轮数
        """
        pass
    
    def add_turn(self, user_message: str, assistant_message: str):
        """添加一轮对话"""
        pass
    
    def get_history(self) -> List[Dict]:
        """获取历史消息"""
        pass
    
    def clear(self):
        """清除历史"""
        pass
    
    def get_last_n_turns(self, n: int) -> List[Dict]:
        """获取最近n轮对话"""
        pass
```

---

## 9. Dashboard 页面设计

### 9.1 AI诊断报告页 (`pages/ai_insights.py`)

**页面功能**：
- 日期范围选择
- LLM连接测试
- 一键生成诊断报告
- 展示门店排名、平台对比、异常告警
- 显示AI诊断总结

**页面布局**：
```
┌─────────────────────────────────────────────────────┐
│  🤖 AI 经营诊断报告                                  │
├─────────────────────────────────────────────────────┤
│  侧边栏:                                             │
│  - 诊断配置                                          │
│  - 日期选择器                                        │
│  - 测试LLM连接按钮                                   │
├─────────────────────────────────────────────────────┤
│  主区域:                                             │
│  - 数据加载状态提示                                  │
│  - [🔍 生成诊断报告] 按钮                            │
│                                                     │
│  报告区域:                                           │
│  ## 📊 门店表现排名                                  │
│  ## 📈 平台对比分析                                  │
│  ## ⚠️ 异常告警                                      │
│  ## 💡 AI 诊断总结                                   │
└─────────────────────────────────────────────────────┘
```

### 9.2 AI对话助手页 (`pages/ai_chat.py`)

**页面功能**：
- 数据上下文选择（日期范围）
- 对话历史显示
- 用户输入框
- 快捷问题按钮
- 清除对话功能

**页面布局**：
```
┌─────────────────────────────────────────────────────┐
│  💬 AI 经营助手                                      │
├─────────────────────────────────────────────────────┤
│  侧边栏:                                             │
│  - 数据上下文                                        │
│  - 日期选择器                                        │
│  - 已加载数据条数提示                                │
│  - [清除对话] 按钮                                   │
├─────────────────────────────────────────────────────┤
│  主区域:                                             │
│  - 对话历史消息列表                                  │
│  - 用户输入框 (chat_input)                           │
│                                                     │
│  底部:                                               │
│  💡 快捷问题:                                        │
│  [为什么这周实收下降?] [哪个门店表现最好?] [给我建议] │
└─────────────────────────────────────────────────────┘
```

---

## 10. 配置文件说明

### 10.1 AI配置文件位置

```
ai/
├── config.py             # 主配置文件（代码形式）
└── settings.json         # 用户配置（运行时保存）

config/
└── .env.example          # 环境变量示例
```

### 10.2 环境变量配置

```bash
# .env.example
ZHIPU_API_KEY=your_zhipu_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 10.3 运行时配置保存

API Key 可通过 Dashboard 设置页面配置，保存至 `config/ai_settings.json`

---

## 11. 开发计划

| 阶段 | 内容 | 预计工时 | 依赖 |
|------|------|----------|------|
| **Phase 1** | LLM接入层 + 配置系统 | 0.5天 | 无 |
| **Phase 2** | 数据分析层 (聚合器/特征计算/异常检测) | 1天 | Phase 1 |
| **Phase 3** | 智能诊断引擎 + Dashboard页面 | 1天 | Phase 2 |
| **Phase 4** | 预测分析引擎 | 1天 | Phase 2 |
| **Phase 5** | 智能问答引擎 + 对话界面 | 1天 | Phase 1, 2 |
| **Phase 6** | 决策建议引擎 + 整合测试 | 0.5天 | Phase 1-5 |

**总计：约5天**

---

## 12. 依赖说明

### 12.1 新增Python依赖

```txt
# requirements.txt 新增
zhipuai>=2.0.0    # 智谱官方SDK（可选，直接用requests也可）
requests>=2.28.0  # HTTP请求
```

### 12.2 安装命令

```bash
pip install zhipuai requests
```

---

## 13. 错误处理与容错

### 13.1 API调用错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| 网络超时 | 重试3次，间隔递增（1s, 2s, 4s） |
| API限流 | 等待后重试，显示"AI忙碌中"提示 |
| API Key无效 | 返回配置错误提示，引导用户检查配置 |
| 模型响应异常 | 捕获异常，返回友好错误信息 |

### 13.2 错误处理接口

```python
class LLMError(Exception):
    """LLM错误基类"""
    pass

class APIKeyError(LLMError):
    """API Key配置错误"""
    pass

class RateLimitError(LLMError):
    """API限流错误"""
    pass

class TimeoutError(LLMError):
    """请求超时错误"""
    pass

def handle_llm_error(error: Exception) -> Dict[str, Any]:
    """
    统一错误处理
    
    Returns:
        {"success": False, "error_type": str, "message": str, "retry_suggested": bool}
    """
    pass
```

---

## 14. API限流与缓存

### 14.1 智谱API限制

| 模型 | 上下文窗口 | RPM (请求/分钟) | TPM (Token/分钟) |
|------|-----------|-----------------|------------------|
| glm-5 | 200,000 | 根据账户配额 | 根据账户配额 |
| glm-4.7 | 200,000 | 根据账户配额 | 根据账户配额 |
| glm-4-plus | 128,000 | 60 | 60,000 |
| glm-4-flash | 128,000 | 120 | 120,000 |

> **注意**: glm-5 和 glm-4.7 使用 OpenAI Compatible 接口，Base URL 为 `https://open.bigmodel.cn/api/coding/paas/v4`

### 14.2 缓存策略

```python
class ResponseCache:
    """
    AI响应缓存器
    
    功能：
    - 缓存相同Prompt的响应
    - TTL过期机制
    - 减少API调用
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """初始化缓存器"""
        pass
    
    def get(self, prompt_hash: str) -> str:
        """获取缓存响应"""
        pass
    
    def set(self, prompt_hash: str, response: str):
        """设置缓存"""
        pass
    
    def clear(self):
        """清除缓存"""
        pass
```

---

## 15. 日志记录规范

### 15.1 日志级别

| 级别 | 使用场景 |
|------|----------|
| DEBUG | 详细调试信息（开发阶段） |
| INFO | 常规操作信息（API调用、报告生成） |
| WARNING | 警告信息（配置缺失使用默认值、缓存未命中） |
| ERROR | 错误信息（API调用失败、数据异常） |

### 15.2 日志接口

```python
import logging

def setup_ai_logger(log_level: str = "INFO") -> logging.Logger:
    """
    配置AI模块日志器
    
    Args:
        log_level: 日志级别
        
    Returns:
        配置好的Logger实例
    """
    pass

def log_llm_request(provider: str, model: str, prompt_length: int):
    """记录LLM请求"""
    pass

def log_llm_response(provider: str, response_length: int, latency_ms: int):
    """记录LLM响应"""
    pass
```

### 15.3 日志文件位置

```
logs/
├── ai_module.log      # AI模块日志
└── ai_errors.log      # AI错误日志（单独记录）
```

---

## 16. 安全考虑

### 16.1 API Key安全

- **存储**：优先使用环境变量，避免硬编码
- **传输**：不在日志中打印API Key
- **显示**：Dashboard配置页中Key显示为 `sk-****xxxx`

### 16.2 数据安全

- 敏感业务数据不发送到云端LLM时，使用本地Ollama
- 对话历史仅保存在用户本地Session

---

## 17. 测试策略

### 17.1 单元测试

| 模块 | 测试重点 |
|------|----------|
| LLM Adapter | Mock API响应、错误处理、重试机制 |
| 数据聚合器 | 聚合逻辑正确性、边界条件 |
| 异常检测器 | 检测算法准确性、阈值配置 |
| Prompt构建器 | 模板渲染、数据注入 |

### 17.2 集成测试

- 端到端诊断报告生成流程
- 问答引擎多轮对话测试
- Dashboard页面交互测试

### 17.3 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行AI模块测试
pytest tests/test_ai/

# 带覆盖率报告
pytest --cov=ai tests/
```

---

## 18. 关键业务指标说明

### 18.1 核心指标定义

| 指标名称 | 字段名 | 计算方式 | 说明 |
|----------|--------|----------|------|
| 实收 | `actual_income` | 有效订单总收入 | 扣除退款后的实际收入 |
| 订单数 | `valid_order_count` | 有效订单数量 | 不包括取消/退款订单 |
| 客单价 | `avg_order_value` | 实收 / 订单数 | 每单平均消费金额 |
| 到手率 | `margin_rate` | 实收 / 平台营业额 × 100% | 反映平台抽成比例 |
| 曝光量 | `exposure_count` | 店铺/商品展示次数 | 用户看到的次数 |
| 进店量 | `entry_count` | 进入店铺的用户数 | 点击进店的次数 |
| 转化率 | `conversion_rate` | 订单数 / 进店量 × 100% | 进店到下单的转化 |
| 竞对排名 | `competitor_rank` | 同商圈排名 | 同品类竞争位置 |

### 18.2 指标分类

```python
# 指标分类配置
METRIC_CATEGORIES = {
    'revenue': ['actual_income', 'platform_revenue', 'settlement_amount'],
    'traffic': ['exposure_count', 'entry_count', 'visitor_count'],
    'conversion': ['valid_order_count', 'conversion_rate', 'order_completion_rate'],
    'cost': ['platform_commission', 'promotion_cost', 'packaging_cost'],
    'efficiency': ['margin_rate', 'avg_order_value', 'cost_per_order']
}
```

---

## 19. API响应格式规范

### 19.1 统一响应格式

```python
# 成功响应
{
    "success": True,
    "data": {...},
    "message": "操作成功",
    "timestamp": "2026-02-25T15:30:00Z"
}

# 错误响应
{
    "success": False,
    "error": {
        "code": "LLM_API_ERROR",
        "message": "API调用失败",
        "details": "Connection timeout after 60s"
    },
    "timestamp": "2026-02-25T15:30:00Z"
}
```

### 19.2 错误码定义

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| `CONFIG_MISSING` | 配置缺失 | 500 |
| `API_KEY_INVALID` | API Key无效 | 401 |
| `RATE_LIMIT_EXCEEDED` | 请求频率超限 | 429 |
| `LLM_API_ERROR` | LLM API调用失败 | 502 |
| `DATA_NOT_FOUND` | 数据不存在 | 404 |
| `INVALID_PARAMETERS` | 参数错误 | 400 |

---

## 20. 性能优化策略

### 20.1 数据量优化

| 策略 | 说明 |
|------|------|
| 数据采样 | 超过10000条记录时，按比例采样发送给LLM |
| 分页聚合 | 大时间范围数据分页处理后合并 |
| 增量更新 | 只发送变化的数据，而非全量数据 |

### 20.2 响应优化

| 策略 | 说明 |
|------|------|
| 流式输出 | 使用`stream_chat`逐步展示响应 |
| 并行请求 | 诊断报告各模块可并行生成 |
| 预加载 | 常用数据提前聚合缓存 |

### 20.3 性能指标

| 操作 | 目标响应时间 |
|------|-------------|
| LLM连接测试 | < 2秒 |
| 简单问答 | < 5秒 |
| 诊断报告生成 | < 15秒 |
| 预测分析 | < 20秒 |

---

## 21. 版本规划

### 21.1 v1.0 (当前目标)

- [x] 智谱GLM接入
- [x] 智能诊断报告
- [x] 基础问答功能
- [x] 门店/平台对比

### 21.2 v1.1 (后续迭代)

- [ ] 多轮对话优化
- [ ] 预测分析增强
- [ ] 节假日效应分析
- [ ] 导出报告(PDF/Excel)

### 21.3 v1.2 (未来规划)

- [ ] 语音交互
- [ ] 自动化报告推送
- [ ] 多租户支持
- [ ] 本地Ollama离线模式

---

## 22. Prompt模板示例

### 22.1 诊断报告Prompt

```
你是一个专业的外卖经营分析助手。请根据以下数据分析经营状况。

## 分析周期
{period}

## 门店表现排名 (Top 10)
{store_ranking}

## 平台对比分析
{platform_comparison}

## 检测到的异常
{anomalies}

## 请输出以下内容：

### 1. 整体经营概况
（总结核心指标表现）

### 2. 门店分析
（分析表现最好和需改进的门店）

### 3. 平台分析
（对比平台表现，给出策略建议）

### 4. 问题诊断
（分析异常原因）

### 5. 改进建议
（3-5条可执行建议，按优先级排序）
```

### 22.2 问答Prompt

```
用户问题: {question}

## 当前数据概况
- 日期范围: {date_range}
- 总实收: ¥{total_income}
- 总订单: {total_orders}
- 平均到手率: {avg_margin_rate}%

请基于以上数据回答用户问题。回答要简洁、准确、有数据支撑。
```

---
