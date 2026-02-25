"""
智能诊断引擎
提供门店对比、平台对比、异常检测、诊断报告生成功能
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import logging
import time

from ai.config import get_ai_config
from ai.core.llm_adapter import get_llm_adapter, BaseLLMAdapter
from ai.core.prompt_builder import PromptBuilder
from ai.analytics.data_aggregator import DataAggregator
from ai.analytics.anomaly_detector import AnomalyDetector
from ai.analytics.time_series import TimeSeriesAnalyzer
from ai.prompts.diagnosis_prompts import (
    DIAGNOSIS_SYSTEM_PROMPT,
    build_diagnosis_prompt,
    build_quick_diagnosis_prompt
)

logger = logging.getLogger(__name__)


class DiagnosisEngine:
    """
    智能诊断引擎
    
    功能：
    - 门店对比分析
    - 平台对比分析
    - 异常检测
    - 生成诊断报告
    """
    
    def __init__(self, llm_adapter: BaseLLMAdapter = None):
        """
        初始化诊断引擎
        
        Args:
            llm_adapter: LLM 适配器实例，如果为 None 则自动创建
        """
        self.config = get_ai_config('analysis', {})
        
        # 初始化 LLM 适配器
        self.llm_adapter = llm_adapter or get_llm_adapter()
        
        # 初始化各组件
        self.data_aggregator = DataAggregator()
        self.anomaly_detector = AnomalyDetector()
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.prompt_builder = PromptBuilder()
        
        # 配置参数
        self.top_n = self.config.get('top_n_stores', 10)
        self.min_data_days = self.config.get('min_data_days', 7)
    
    def generate_full_diagnosis(self, df: pd.DataFrame,
                                 period: str = "本周",
                                 top_n: int = None,
                                 stream: bool = False) -> Dict[str, Any]:
        """
        生成完整诊断报告
        
        Args:
            df: 原始数据 DataFrame
            period: 报告周期描述
            top_n: 排名展示数量
            stream: 是否流式输出
            
        Returns:
            {
                "store_ranking": {...},
                "platform_comparison": {...},
                "anomalies": [...],
                "summary_stats": {...},
                "ai_summary": "AI 生成的总结报告"
            }
        """
        start_time = time.time()
        
        if top_n is None:
            top_n = self.top_n
        
        # 验证数据
        if df.empty:
            return self._empty_result("数据为空，无法生成诊断报告")
        
        # 1. 数据聚合
        logger.info("开始数据聚合...")
        store_ranking_df = self.data_aggregator.aggregate_by_store(df)
        platform_comparison_df = self.data_aggregator.aggregate_by_platform(df)
        summary_stats = self.data_aggregator.get_summary_stats(df)
        
        # 2. 异常检测
        logger.info("开始异常检测...")
        anomalies = self.anomaly_detector.detect(df)
        
        # 3. 转换为可序列化格式
        store_ranking = store_ranking_df.to_dict('records') if not store_ranking_df.empty else []
        platform_comparison = platform_comparison_df.to_dict('records') if not platform_comparison_df.empty else []
        
        # 4. 构建 Prompt
        prompt = build_diagnosis_prompt(
            store_ranking=store_ranking,
            platform_comparison=platform_comparison,
            anomalies=anomalies,
            period=period,
            summary_stats=summary_stats,
            top_n=top_n
        )
        
        # 5. 调用 LLM 生成诊断报告
        logger.info("调用 LLM 生成诊断报告...")
        
        try:
            messages = [
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            if stream:
                # 流式输出
                ai_summary = self._stream_diagnosis(messages)
            else:
                # 同步输出
                ai_summary = self.llm_adapter.chat(messages)
                
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            ai_summary = f"⚠️ AI 分析暂时不可用: {str(e)}"
        
        elapsed_time = time.time() - start_time
        logger.info(f"诊断报告生成完成，耗时 {elapsed_time:.2f} 秒")
        
        return {
            "success": True,
            "store_ranking": store_ranking,
            "platform_comparison": platform_comparison,
            "anomalies": anomalies,
            "summary_stats": summary_stats,
            "ai_summary": ai_summary,
            "period": period,
            "elapsed_time": elapsed_time
        }
    
    def _stream_diagnosis(self, messages: List[Dict]) -> str:
        """
        流式生成诊断报告
        
        Args:
            messages: 消息列表
            
        Returns:
            完整的响应文本
        """
        full_response = []
        for chunk in self.llm_adapter.stream_chat(messages):
            full_response.append(chunk)
        return ''.join(full_response)
    
    def compare_stores(self, df: pd.DataFrame,
                       store_names: List[str]) -> Dict[str, Any]:
        """
        指定门店对比分析
        
        Args:
            df: 数据
            store_names: 要对比的门店名称列表
            
        Returns:
            {"data": [...], "analysis": "AI 对比分析"}
        """
        if df.empty or not store_names:
            return {"data": [], "analysis": "数据或门店列表为空"}
        
        # 筛选指定门店
        filtered_df = df[df['brand_store_name'].isin(store_names)]
        
        if filtered_df.empty:
            return {"data": [], "analysis": "未找到指定门店的数据"}
        
        # 聚合数据
        comparison_df = self.data_aggregator.aggregate_by_store(filtered_df)
        comparison_data = comparison_df.to_dict('records')
        
        # 构建 Prompt
        from ai.prompts.diagnosis_prompts import build_store_comparison_prompt
        prompt = build_store_comparison_prompt(comparison_data, store_names)
        
        # 调用 LLM
        try:
            messages = [
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            analysis = self.llm_adapter.chat(messages)
        except Exception as e:
            logger.error(f"门店对比分析失败: {e}")
            analysis = f"⚠️ AI 分析暂时不可用: {str(e)}"
        
        return {
            "success": True,
            "data": comparison_data,
            "analysis": analysis,
            "store_names": store_names
        }
    
    def compare_platforms(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        平台对比分析
        
        Args:
            df: 数据
            
        Returns:
            {"data": [...], "analysis": "AI 对比分析"}
        """
        if df.empty:
            return {"data": [], "analysis": "数据为空"}
        
        # 聚合数据
        platform_df = self.data_aggregator.aggregate_by_platform(df)
        platform_data = platform_df.to_dict('records')
        
        # 构建分析文本
        analysis_text = self._generate_platform_analysis(platform_data)
        
        return {
            "success": True,
            "data": platform_data,
            "analysis": analysis_text
        }
    
    def _generate_platform_analysis(self, platform_data: List[Dict]) -> str:
        """生成平台分析文本"""
        if not platform_data:
            return "无平台数据"
        
        # 简单的规则分析
        if len(platform_data) == 1:
            return f"当前只有 {platform_data[0]['platform']} 一个平台的数据，建议增加其他平台进行对比分析。"
        
        # 找出最佳平台
        best = max(platform_data, key=lambda x: x.get('actual_income', 0))
        worst = min(platform_data, key=lambda x: x.get('actual_income', 0))
        
        lines = [
            f"**{best['platform']}** 表现最佳，实收 ¥{best.get('actual_income', 0):,.0f}",
            f"**{worst['platform']}** 表现较弱，实收 ¥{worst.get('actual_income', 0):,.0f}",
            f"差距: ¥{(best.get('actual_income', 0) - worst.get('actual_income', 0)):,.0f}"
        ]
        
        return '\n'.join(lines)
    
    def quick_diagnosis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        快速诊断 - 生成简要分析
        
        Args:
            df: 数据
            
        Returns:
            {"summary": "简要分析"}
        """
        if df.empty:
            return {"success": False, "summary": "数据为空"}
        
        # 获取摘要统计
        summary_stats = self.data_aggregator.get_summary_stats(df)
        
        # 构建简要数据摘要
        data_summary = self._build_quick_summary(summary_stats)
        
        # 构建 Prompt
        prompt = build_quick_diagnosis_prompt(data_summary)
        
        # 调用 LLM
        try:
            messages = [
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            summary = self.llm_adapter.chat(messages, max_tokens=500)
        except Exception as e:
            logger.error(f"快速诊断失败: {e}")
            summary = f"⚠️ AI 分析暂时不可用: {str(e)}"
        
        return {
            "success": True,
            "summary": summary,
            "stats": summary_stats
        }
    
    def _build_quick_summary(self, stats: Dict) -> str:
        """构建快速摘要文本"""
        lines = []
        
        if 'date_range' in stats:
            dr = stats['date_range']
            lines.append(f"日期: {dr.get('start', '')} 至 {dr.get('end', '')}")
        
        if 'revenue' in stats:
            rev = stats['revenue']
            lines.append(f"总实收: ¥{rev.get('total', 0):,.0f}")
        
        if 'orders' in stats:
            orders = stats['orders']
            lines.append(f"总订单: {orders.get('total', 0):,}")
        
        if 'stores' in stats:
            lines.append(f"门店数: {stats['stores'].get('count', 0)}")
        
        if 'platforms' in stats:
            lines.append(f"平台: {', '.join(stats['platforms'].get('list', []))}")
        
        return '\n'.join(lines)
    
    def detect_anomalies(self, df: pd.DataFrame,
                         metrics: List[str] = None) -> Dict[str, Any]:
        """
        检测异常
        
        Args:
            df: 数据
            metrics: 要检测的指标列表
            
        Returns:
            {"anomalies": [...], "count": int}
        """
        if df.empty:
            return {"anomalies": [], "count": 0}
        
        anomalies = self.anomaly_detector.detect(df, metrics)
        
        return {
            "success": True,
            "anomalies": anomalies,
            "count": len(anomalies)
        }
    
    def get_store_performance(self, df: pd.DataFrame,
                               store_name: str) -> Dict[str, Any]:
        """
        获取单个门店的详细表现
        
        Args:
            df: 数据
            store_name: 门店名称
            
        Returns:
            门店详细表现数据
        """
        if df.empty:
            return {"success": False, "message": "数据为空"}
        
        # 筛选门店数据
        store_df = df[df['brand_store_name'] == store_name]
        
        if store_df.empty:
            return {"success": False, "message": f"未找到门店: {store_name}"}
        
        # 聚合数据
        aggregated = self.data_aggregator.aggregate_by_store(store_df)
        
        if aggregated.empty:
            return {"success": False, "message": "聚合数据失败"}
        
        store_data = aggregated.iloc[0].to_dict()
        
        # 获取时间序列数据
        daily_data = self.data_aggregator.aggregate_by_date(store_df)
        daily_records = daily_data.to_dict('records') if not daily_data.empty else []
        
        # 获取平台分布
        platform_df = self.data_aggregator.aggregate_by_platform(store_df)
        platform_data = platform_df.to_dict('records') if not platform_df.empty else []
        
        # 检测异常
        anomalies = self.anomaly_detector.detect(store_df)
        store_anomalies = [a for a in anomalies if a.get('store') == store_name]
        
        return {
            "success": True,
            "store_name": store_name,
            "metrics": store_data,
            "daily_data": daily_records,
            "platform_distribution": platform_data,
            "anomalies": store_anomalies
        }
    
    def _empty_result(self, message: str = "无数据") -> Dict[str, Any]:
        """返回空结果"""
        return {
            "success": False,
            "store_ranking": [],
            "platform_comparison": [],
            "anomalies": [],
            "summary_stats": {},
            "ai_summary": message,
            "period": "",
            "elapsed_time": 0
        }


def generate_diagnosis(df: pd.DataFrame,
                       period: str = "本周",
                       top_n: int = 10,
                       llm_adapter: BaseLLMAdapter = None) -> Dict[str, Any]:
    """
    便捷函数：生成诊断报告
    
    Args:
        df: 数据
        period: 周期描述
        top_n: 排名数量
        llm_adapter: LLM 适配器
        
    Returns:
        诊断报告
    """
    engine = DiagnosisEngine(llm_adapter)
    return engine.generate_full_diagnosis(df, period, top_n)


def quick_diagnosis(df: pd.DataFrame) -> str:
    """
    便捷函数：快速诊断
    
    Args:
        df: 数据
        
    Returns:
        诊断摘要
    """
    engine = DiagnosisEngine()
    result = engine.quick_diagnosis(df)
    return result.get("summary", "分析失败")