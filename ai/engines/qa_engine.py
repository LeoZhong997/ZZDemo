"""
智能问答引擎
提供自然语言查询、上下文对话、多轮追问功能
"""
from typing import Dict, Any, List, Optional, Generator
import pandas as pd
import logging
import time

from ai.config import get_ai_config
from ai.core.llm_adapter import get_llm_adapter, BaseLLMAdapter
from ai.core.context_manager import ContextManager, get_context
from ai.analytics.data_aggregator import DataAggregator
from ai.analytics.anomaly_detector import AnomalyDetector
from ai.prompts.qa_prompts import (
    QA_SYSTEM_PROMPT,
    build_qa_prompt,
    build_qa_prompt_with_dataframe,
    build_quick_question_prompt,
    get_suggested_questions
)

logger = logging.getLogger(__name__)


class QAEngine:
    """
    智能问答引擎
    
    功能：
    - 自然语言查询
    - 上下文对话
    - 多轮追问
    """
    
    def __init__(self, llm_adapter: BaseLLMAdapter = None, 
                 session_id: str = "default"):
        """
        初始化问答引擎
        
        Args:
            llm_adapter: LLM 适配器实例
            session_id: 会话 ID，用于隔离不同会话的上下文
        """
        self.config = get_ai_config('qa', {})
        
        # 初始化 LLM 适配器
        self.llm_adapter = llm_adapter or get_llm_adapter()
        
        # 初始化数据聚合器
        self.data_aggregator = DataAggregator()
        self.anomaly_detector = AnomalyDetector()
        
        # 获取或创建上下文管理器
        self.session_id = session_id
        self.context_manager = get_context(session_id)
        
        # 当前数据上下文
        self._current_df: Optional[pd.DataFrame] = None
        self._data_context: Dict[str, Any] = {}
    
    def set_data_context(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        设置数据上下文
        
        Args:
            df: 数据 DataFrame
            
        Returns:
            数据上下文摘要
        """
        self._current_df = df
        
        if df.empty:
            self._data_context = {}
            return {"success": False, "message": "数据为空"}
        
        # 获取摘要统计
        summary_stats = self.data_aggregator.get_summary_stats(df)
        
        # 获取门店排名
        store_ranking = self.data_aggregator.aggregate_by_store(df)
        top_stores = []
        if not store_ranking.empty:
            for _, row in store_ranking.head(5).iterrows():
                top_stores.append({
                    "name": row.get('brand_store_name', ''),
                    "revenue": row.get('actual_income', 0)
                })
        
        # 获取平台列表
        platform_df = self.data_aggregator.aggregate_by_platform(df)
        platforms = platform_df['platform'].tolist() if not platform_df.empty else []
        
        # 检测异常
        anomalies = self.anomaly_detector.detect(df)
        
        # 构建数据上下文
        self._data_context = {
            "date_range": summary_stats.get('date_range', {}),
            "revenue": summary_stats.get('revenue', {}),
            "orders": summary_stats.get('orders', {}),
            "store_count": summary_stats.get('stores', {}).get('count', 0),
            "platforms": platforms,
            "top_stores": top_stores,
            "anomalies": anomalies[:3] if anomalies else [],
            "avg_order_value": summary_stats.get('efficiency', {}).get('avg_order_value', 0),
            "margin_rate": summary_stats.get('efficiency', {}).get('margin_rate', 0),
            "has_trend_data": len(df) >= 7
        }
        
        logger.info(f"数据上下文已设置: {len(df)} 条记录, {len(top_stores)} 个门店")
        
        return {
            "success": True,
            "data_context": self._data_context,
            "record_count": len(df)
        }
    
    def ask(self, question: str, 
            stream: bool = False,
            include_history: bool = True) -> str:
        """
        回答用户问题
        
        Args:
            question: 用户问题
            stream: 是否流式输出
            include_history: 是否包含历史对话
            
        Returns:
            AI 回答
        """
        if not question or not question.strip():
            return "请输入您的问题。"
        
        start_time = time.time()
        
        try:
            # 构建 Prompt
            history = self.context_manager.get_history() if include_history else []
            prompt = build_qa_prompt(question, self._data_context, history)
            
            # 构建消息
            messages = self.context_manager.build_messages(
                system_prompt=QA_SYSTEM_PROMPT,
                current_question=prompt,
                include_history=False  # 已经在 prompt 中包含了
            )
            
            # 调用 LLM
            if stream:
                response = self._stream_ask(messages)
            else:
                response = self.llm_adapter.chat(messages)
            
            # 记录对话
            self.context_manager.add_turn(question, response)
            
            elapsed_time = time.time() - start_time
            logger.info(f"问答完成，耗时 {elapsed_time:.2f} 秒")
            
            return response
            
        except Exception as e:
            logger.error(f"问答失败: {e}")
            error_response = f"⚠️ 抱歉，处理您的问题时出现错误: {str(e)}"
            return error_response
    
    def stream_ask(self, question: str, 
                   include_history: bool = True) -> Generator[str, None, None]:
        """
        流式回答用户问题
        
        Args:
            question: 用户问题
            include_history: 是否包含历史对话
            
        Yields:
            响应文本片段
        """
        if not question or not question.strip():
            yield "请输入您的问题。"
            return
        
        try:
            # 构建 Prompt
            history = self.context_manager.get_history() if include_history else []
            prompt = build_qa_prompt(question, self._data_context, history)
            
            # 构建消息
            messages = self.context_manager.build_messages(
                system_prompt=QA_SYSTEM_PROMPT,
                current_question=prompt,
                include_history=False
            )
            
            # 流式调用 LLM
            full_response = []
            for chunk in self.llm_adapter.stream_chat(messages):
                full_response.append(chunk)
                yield chunk
            
            # 记录对话
            complete_response = ''.join(full_response)
            self.context_manager.add_turn(question, complete_response)
            
        except Exception as e:
            logger.error(f"流式问答失败: {e}")
            yield f"⚠️ 抱歉，处理您的问题时出现错误: {str(e)}"
    
    def _stream_ask(self, messages: List[Dict]) -> str:
        """
        内部流式回答
        
        Args:
            messages: 消息列表
            
        Returns:
            完整响应
        """
        full_response = []
        for chunk in self.llm_adapter.stream_chat(messages):
            full_response.append(chunk)
        return ''.join(full_response)
    
    def quick_question(self, question_type: str) -> str:
        """
        快捷问题
        
        Args:
            question_type: 问题类型 (summary/best_store/suggestions 等)
            
        Returns:
            AI 回答
        """
        # 构建快捷问题 Prompt
        prompt = build_quick_question_prompt(question_type, self._data_context)
        
        # 提取实际问题文本
        question_map = {
            "summary": "请总结本周的经营状况",
            "best_store": "哪个门店表现最好？",
            "worst_store": "哪个门店表现最差？",
            "suggestions": "给我改进建议",
            "platform_compare": "对比各平台表现",
            "anomalies": "分析异常问题",
            "trend": "分析经营趋势"
        }
        question = question_map.get(question_type, question_type)
        
        return self.ask(prompt)
    
    def get_suggested_questions(self) -> List[Dict[str, str]]:
        """
        获取建议的问题列表
        
        Returns:
            建议问题列表
        """
        return get_suggested_questions(self._data_context)
    
    def clear_context(self) -> None:
        """清除对话上下文"""
        self.context_manager.clear()
        logger.info("对话上下文已清除")
    
    def get_conversation_history(self) -> List[Dict]:
        """
        获取对话历史
        
        Returns:
            对话历史列表
        """
        return self.context_manager.get_raw_history()
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        获取上下文摘要
        
        Returns:
            上下文统计信息
        """
        return {
            "session_id": self.session_id,
            "context": self.context_manager.get_context_summary(),
            "data_loaded": self._current_df is not None and not self._current_df.empty,
            "data_context": self._data_context
        }
    
    def ask_about_store(self, store_name: str, question: str = None) -> str:
        """
        询问特定门店的情况
        
        Args:
            store_name: 门店名称
            question: 具体问题（可选）
            
        Returns:
            AI 回答
        """
        if self._current_df is None or self._current_df.empty:
            return "请先加载数据。"
        
        # 筛选门店数据
        store_df = self._current_df[
            self._current_df['brand_store_name'].str.contains(store_name, na=False)
        ]
        
        if store_df.empty:
            return f"未找到门店: {store_name}"
        
        # 获取门店详细数据
        store_metrics = self.data_aggregator.aggregate_by_store(store_df)
        store_data = store_metrics.iloc[0].to_dict() if not store_metrics.empty else {}
        
        # 构建问题
        if question:
            full_question = f"关于门店【{store_name}】：{question}"
        else:
            full_question = f"请详细介绍门店【{store_name}】的经营情况，包括收入、订单、转化率等关键指标。"
        
        # 添加门店数据到上下文
        enhanced_context = self._data_context.copy()
        enhanced_context['current_store'] = {
            "name": store_name,
            "metrics": store_data
        }
        
        # 临时替换上下文
        original_context = self._data_context
        self._data_context = enhanced_context
        
        response = self.ask(full_question)
        
        # 恢复上下文
        self._data_context = original_context
        
        return response
    
    def compare_entities(self, entity_type: str, 
                         entity_names: List[str],
                         aspect: str = "整体表现") -> str:
        """
        对比分析
        
        Args:
            entity_type: 实体类型 (store/platform)
            entity_names: 实体名称列表
            aspect: 对比方面
            
        Returns:
            AI 回答
        """
        if self._current_df is None or self._current_df.empty:
            return "请先加载数据。"
        
        if len(entity_names) < 2:
            return "请至少提供两个实体进行对比。"
        
        # 筛选数据
        if entity_type == "store":
            filtered_df = self._current_df[
                self._current_df['brand_store_name'].isin(entity_names)
            ]
            aggregated = self.data_aggregator.aggregate_by_store(filtered_df)
        elif entity_type == "platform":
            filtered_df = self._current_df[
                self._current_df['platform'].isin(entity_names)
            ]
            aggregated = self.data_aggregator.aggregate_by_platform(filtered_df)
        else:
            return f"不支持的实体类型: {entity_type}"
        
        # 构建对比问题
        entities_str = "、".join(entity_names)
        question = f"请对比{entity_type}【{entities_str}】的{aspect}，分析差异原因。"
        
        # 添加对比数据到上下文
        enhanced_context = self._data_context.copy()
        enhanced_context['comparison_data'] = aggregated.to_dict('records')
        
        # 临时替换上下文
        original_context = self._data_context
        self._data_context = enhanced_context
        
        response = self.ask(question)
        
        # 恢复上下文
        self._data_context = original_context
        
        return response


def ask_question(df: pd.DataFrame,
                 question: str,
                 session_id: str = "default",
                 llm_adapter: BaseLLMAdapter = None) -> str:
    """
    便捷函数：问答
    
    Args:
        df: 数据
        question: 问题
        session_id: 会话 ID
        llm_adapter: LLM 适配器
        
    Returns:
        AI 回答
    """
    engine = QAEngine(llm_adapter=llm_adapter, session_id=session_id)
    engine.set_data_context(df)
    return engine.ask(question)


def quick_analysis(df: pd.DataFrame,
                   analysis_type: str = "summary",
                   session_id: str = "default") -> str:
    """
    便捷函数：快速分析
    
    Args:
        df: 数据
        analysis_type: 分析类型
        session_id: 会话 ID
        
    Returns:
        AI 分析结果
    """
    engine = QAEngine(session_id=session_id)
    engine.set_data_context(df)
    return engine.quick_question(analysis_type)