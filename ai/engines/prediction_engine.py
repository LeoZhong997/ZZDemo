"""
预测分析引擎
提供营收预测、趋势分析、节假日效应分析功能
"""
from typing import Dict, Any, List, Optional, Generator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time

from ai.config import get_ai_config
from ai.core.llm_adapter import get_llm_adapter, BaseLLMAdapter
from ai.analytics.data_aggregator import DataAggregator
from ai.analytics.time_series import TimeSeriesAnalyzer
from ai.prompts.prediction_prompts import (
    PREDICTION_SYSTEM_PROMPT,
    build_revenue_prediction_prompt,
    build_trend_analysis_prompt,
    build_holiday_effect_prompt,
    build_store_prediction_prompt
)

logger = logging.getLogger(__name__)


class PredictionEngine:
    """
    预测分析引擎
    
    功能：
    - 营收预测
    - 趋势分析
    - 节假日效应分析
    - 门店预测对比
    """
    
    def __init__(self, llm_adapter: BaseLLMAdapter = None):
        """
        初始化预测引擎
        
        Args:
            llm_adapter: LLM 适配器实例，如果为 None 则自动创建
        """
        self.config = get_ai_config('analysis', {})
        
        # 初始化 LLM 适配器
        self.llm_adapter = llm_adapter or get_llm_adapter()
        
        # 初始化组件
        self.data_aggregator = DataAggregator()
        self.time_series_analyzer = TimeSeriesAnalyzer()
        
        # 配置参数
        self.prediction_days = self.config.get('prediction_days', 7)
        self.min_data_days = self.config.get('min_data_days', 7)
    
    def predict_revenue(self, df: pd.DataFrame,
                        days: int = 7,
                        include_confidence: bool = True,
                        stream: bool = False) -> Dict[str, Any]:
        """
        营收预测
        
        Args:
            df: 历史数据
            days: 预测天数
            include_confidence: 是否包含置信区间
            stream: 是否流式输出
            
        Returns:
            {
                "predictions": [...],
                "trend": "上升/下降/平稳",
                "confidence": 0.85,
                "analysis": "AI 分析说明",
                "total_predicted": 总预测值
            }
        """
        start_time = time.time()
        
        if df.empty:
            return self._empty_prediction_result("数据为空，无法进行预测")
        
        # 检查数据量
        unique_dates = df['date'].nunique() if 'date' in df.columns else 0
        if unique_dates < self.min_data_days:
            return self._empty_prediction_result(
                f"数据不足，至少需要 {self.min_data_days} 天数据，当前仅 {unique_dates} 天"
            )
        
        # 1. 聚合日度数据
        daily_data = self.time_series_analyzer.aggregate_daily(df)
        
        if daily_data.empty:
            return self._empty_prediction_result("日度数据聚合失败")
        
        # 2. 计算趋势
        trend_stats = self.time_series_analyzer.calculate_trend(daily_data)
        
        # 3. 生成基础预测
        model_result = self.time_series_analyzer.forecast_simple(df, days=days)
        
        if 'error' in model_result:
            return self._empty_prediction_result(model_result['error'])
        
        predictions = model_result.get('predictions', [])
        
        # 4. 添加置信区间
        if include_confidence:
            std = daily_data['actual_income'].std()
            for pred in predictions:
                pred['confidence_lower'] = max(0, pred['predicted_value'] - std * 0.5)
                pred['confidence_upper'] = pred['predicted_value'] + std * 0.5
        
        # 5. 计算置信度
        r_squared = trend_stats.get('r_squared', 0)
        volatility = self.time_series_analyzer.calculate_volatility(df)
        volatility_value = volatility.get('volatility', 50)
        
        # 置信度计算：R² 贡献 60%，波动性贡献 40%（波动越低置信度越高）
        confidence = min(0.95, max(0.3, r_squared * 0.6 + (1 - volatility_value / 100) * 0.4))
        
        # 6. 调用 LLM 进行分析
        period = f"{df['date'].min()} 至 {df['date'].max()}"
        
        # 准备历史摘要
        summary_stats = self.data_aggregator.get_summary_stats(df)
        summary_stats['trend'] = trend_stats
        
        # 转换日度数据为列表格式
        daily_records = daily_data.to_dict('records')
        for record in daily_records:
            if 'date' in record and hasattr(record['date'], 'strftime'):
                record['date'] = record['date'].strftime('%Y-%m-%d')
        
        prompt = build_revenue_prediction_prompt(
            historical_summary=summary_stats,
            trend_data=daily_records,
            model_predictions=predictions,
            period=period,
            prediction_days=days
        )
        
        try:
            messages = [
                {"role": "system", "content": PREDICTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            if stream:
                analysis = self._stream_analysis(messages)
            else:
                analysis = self.llm_adapter.chat(messages)
                
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            analysis = f"⚠️ AI 分析暂时不可用: {str(e)}"
        
        elapsed_time = time.time() - start_time
        logger.info(f"营收预测完成，耗时 {elapsed_time:.2f} 秒")
        
        total_predicted = sum(p['predicted_value'] for p in predictions)
        
        return {
            "success": True,
            "predictions": predictions,
            "trend": trend_stats.get('direction', '未知'),
            "trend_stats": trend_stats,
            "confidence": round(confidence, 2),
            "analysis": analysis,
            "total_predicted": round(total_predicted, 2),
            "daily_avg_predicted": round(total_predicted / days, 2),
            "model_method": model_result.get('method', 'linear_trend'),
            "elapsed_time": elapsed_time
        }
    
    def analyze_trend(self, df: pd.DataFrame,
                      metric: str = 'actual_income',
                      stream: bool = False) -> Dict[str, Any]:
        """
        趋势分析
        
        Args:
            df: 数据
            metric: 分析指标
            stream: 是否流式输出
            
        Returns:
            {"trend": {...}, "analysis": "趋势分析报告"}
        """
        start_time = time.time()
        
        if df.empty:
            return {"success": False, "trend": {}, "analysis": "数据为空"}
        
        # 检查指标列是否存在，如果不存在或为空，尝试计算衍生指标
        if metric not in df.columns:
            # 尝试计算衍生指标
            df = self._ensure_derived_metrics(df, metric)
            if metric not in df.columns:
                return {"success": False, "trend": {}, "analysis": f"指标 '{metric}' 不存在于数据中"}
        
        # 检查指标列是否有有效数据，如果为空尝试重新计算
        valid_count = df[metric].notna().sum()
        if valid_count == 0:
            # 尝试重新计算衍生指标
            df = self._ensure_derived_metrics(df, metric)
            valid_count = df[metric].notna().sum()
            if valid_count == 0:
                return {"success": False, "trend": {}, "analysis": f"指标 '{metric}' 没有有效数据（全部为空）"}
        
        # 聚合日度数据
        daily_data = self.time_series_analyzer.aggregate_daily(df, metric=metric)
        
        if daily_data.empty:
            return {"success": False, "trend": {}, "analysis": f"指标 '{metric}' 数据聚合失败（可能全部为空值）"}
        
        # 计算趋势
        trend_stats = self.time_series_analyzer.calculate_trend(daily_data, metric=metric)
        
        # 检测周期性
        seasonality = self.time_series_analyzer.detect_seasonality(df, metric=metric)
        
        # 增长期分析
        growth_analysis = self.time_series_analyzer.analyze_growth_periods(df, metric=metric)
        
        # 构建分析报告
        period = f"{df['date'].min()} 至 {df['date'].max()}"
        
        # 转换数据格式
        daily_records = daily_data.to_dict('records')
        for record in daily_records:
            if 'date' in record and hasattr(record['date'], 'strftime'):
                record['date'] = record['date'].strftime('%Y-%m-%d')
        
        prompt = build_trend_analysis_prompt(
            period=period,
            metric=metric,
            trend_data=daily_records,
            trend_stats=trend_stats,
            seasonality=seasonality,
            growth_analysis=growth_analysis
        )
        
        try:
            messages = [
                {"role": "system", "content": PREDICTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            if stream:
                analysis = self._stream_analysis(messages)
            else:
                analysis = self.llm_adapter.chat(messages)
                
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            analysis = f"⚠️ AI 分析暂时不可用: {str(e)}"
        
        elapsed_time = time.time() - start_time
        
        return {
            "success": True,
            "trend": trend_stats,
            "seasonality": seasonality,
            "growth_analysis": growth_analysis,
            "analysis": analysis,
            "elapsed_time": elapsed_time
        }
    
    def analyze_holiday_effect(self, df: pd.DataFrame,
                                holiday_dates: List[str] = None,
                                holiday_name: str = "节假日",
                                stream: bool = False) -> Dict[str, Any]:
        """
        节假日效应分析
        
        Args:
            df: 数据
            holiday_dates: 节假日日期列表 (格式: 'YYYY-MM-DD')
            holiday_name: 节假日名称
            stream: 是否流式输出
            
        Returns:
            {"holiday_impact": {...}, "analysis": "节假日影响分析"}
        """
        start_time = time.time()
        
        if df.empty:
            return {"success": False, "holiday_impact": {}, "analysis": "数据为空"}
        
        if not holiday_dates:
            # 如果没有指定节假日，尝试检测周末效应
            return self._analyze_weekend_effect(df, stream)
        
        # 转换日期格式
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        holiday_dates_dt = pd.to_datetime(holiday_dates)
        
        # 分离节假日数据和普通日数据
        holiday_df = df[df['date'].isin(holiday_dates_dt)]
        normal_df = df[~df['date'].isin(holiday_dates_dt)]
        
        if holiday_df.empty:
            return {"success": False, "holiday_impact": {}, "analysis": "没有找到节假日对应的数据"}
        
        # 计算统计数据
        holiday_daily = self.time_series_analyzer.aggregate_daily(holiday_df)
        normal_daily = self.time_series_analyzer.aggregate_daily(normal_df) if not normal_df.empty else pd.DataFrame()
        
        holiday_avg = holiday_daily['actual_income'].mean() if not holiday_daily.empty else 0
        normal_avg = normal_daily['actual_income'].mean() if not normal_daily.empty else 0
        
        # 效应系数
        effect_ratio = holiday_avg / normal_avg if normal_avg > 0 else 1.0
        lift_percentage = (effect_ratio - 1) * 100
        
        # 转换数据
        holiday_records = holiday_daily.to_dict('records') if not holiday_daily.empty else []
        normal_records = normal_daily.to_dict('records') if not normal_daily.empty else []
        
        for record in holiday_records:
            if 'date' in record and hasattr(record['date'], 'strftime'):
                record['date'] = record['date'].strftime('%Y-%m-%d')
        for record in normal_records:
            if 'date' in record and hasattr(record['date'], 'strftime'):
                record['date'] = record['date'].strftime('%Y-%m-%d')
        
        # 构建分析
        period = f"{df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}"
        holiday_info = f"{holiday_name}: {', '.join(holiday_dates)}"
        
        prompt = build_holiday_effect_prompt(
            period=period,
            holiday_info=holiday_info,
            holiday_data=holiday_records,
            normal_data=normal_records,
            holiday_avg=holiday_avg,
            normal_avg=normal_avg
        )
        
        try:
            messages = [
                {"role": "system", "content": PREDICTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            if stream:
                analysis = self._stream_analysis(messages)
            else:
                analysis = self.llm_adapter.chat(messages)
                
        except Exception as e:
            logger.error(f"节假日效应分析失败: {e}")
            analysis = f"⚠️ AI 分析暂时不可用: {str(e)}"
        
        elapsed_time = time.time() - start_time
        
        return {
            "success": True,
            "holiday_impact": {
                "holiday_name": holiday_name,
                "holiday_dates": holiday_dates,
                "holiday_avg": round(holiday_avg, 2),
                "normal_avg": round(normal_avg, 2),
                "effect_ratio": round(effect_ratio, 2),
                "lift_percentage": round(lift_percentage, 2),
                "holiday_days": len(holiday_dates),
                "data_days": len(holiday_records)
            },
            "analysis": analysis,
            "elapsed_time": elapsed_time
        }
    
    def _analyze_weekend_effect(self, df: pd.DataFrame,
                                  stream: bool = False) -> Dict[str, Any]:
        """分析周末效应"""
        seasonality = self.time_series_analyzer.detect_seasonality(df)
        
        weekend_effect = seasonality.get('weekend_effect', 0)
        weekday_avg = seasonality.get('weekday_avg', {})
        
        analysis = f"""
### 周末效应分析

- **周末效应**: {seasonality.get('weekend_effect_label', '未知')}
- **周末与工作日差异**: {abs(weekend_effect):.1f}%
- **高峰日**: {seasonality.get('peak_day', '未知')}
- **低谷日**: {seasonality.get('low_day', '未知')}

#### 各日均值
"""
        for day, avg in weekday_avg.items():
            analysis += f"- {day}: ¥{avg:,.0f}\n"
        
        return {
            "success": True,
            "holiday_impact": {
                "holiday_name": "周末",
                "effect_ratio": 1 + weekend_effect / 100,
                "lift_percentage": weekend_effect,
                "peak_day": seasonality.get('peak_day'),
                "low_day": seasonality.get('low_day')
            },
            "seasonality": seasonality,
            "analysis": analysis,
            "elapsed_time": 0
        }
    
    def predict_by_store(self, df: pd.DataFrame,
                          days: int = 7,
                          top_n: int = 10) -> Dict[str, Any]:
        """
        分门店预测
        
        Args:
            df: 数据
            days: 预测天数
            top_n: 返回前 N 个门店
            
        Returns:
            {"store_predictions": [...], "analysis": "..."}
        """
        start_time = time.time()
        
        if df.empty:
            return {"success": False, "store_predictions": [], "analysis": "数据为空"}
        
        store_predictions = []
        stores = df['brand_store_name'].unique()
        
        for store in stores:
            store_df = df[df['brand_store_name'] == store]
            
            # 检查数据量
            unique_dates = store_df['date'].nunique()
            if unique_dates < 3:  # 至少需要3天数据
                continue
            
            # 聚合并预测
            daily_data = self.time_series_analyzer.aggregate_daily(store_df)
            
            if daily_data.empty:
                continue
            
            trend = self.time_series_analyzer.calculate_trend(daily_data)
            forecast = self.time_series_analyzer.forecast_simple(store_df, days=days)
            
            if 'error' in forecast:
                continue
            
            predictions = forecast.get('predictions', [])
            total_predicted = sum(p['predicted_value'] for p in predictions)
            
            # 计算置信度
            r_squared = trend.get('r_squared', 0)
            confidence = min(0.95, max(0.3, r_squared))
            
            store_predictions.append({
                "store_name": store,
                "predicted_total": round(total_predicted, 2),
                "predicted_daily_avg": round(total_predicted / days, 2),
                "trend": trend.get('direction', '未知'),
                "confidence": round(confidence, 2),
                "predictions": predictions
            })
        
        # 按预测营收排序
        store_predictions.sort(key=lambda x: x['predicted_total'], reverse=True)
        top_predictions = store_predictions[:top_n]
        
        # 计算整体统计
        total_predicted = sum(s['predicted_total'] for s in store_predictions)
        growth_stores = sum(1 for s in store_predictions if s['trend'] == '上升')
        decline_stores = sum(1 for s in store_predictions if s['trend'] == '下降')
        
        overall_trend = "上升" if growth_stores > decline_stores else (
            "下降" if decline_stores > growth_stores else "平稳"
        )
        
        # 构建 LLM 分析
        period = f"{df['date'].min()} 至 {df['date'].max()}"
        
        prompt = build_store_prediction_prompt(
            period=period,
            prediction_days=days,
            store_predictions=top_predictions,
            total_predicted=total_predicted,
            overall_trend=overall_trend
        )
        
        try:
            messages = [
                {"role": "system", "content": PREDICTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            analysis = self.llm_adapter.chat(messages)
        except Exception as e:
            logger.error(f"门店预测分析失败: {e}")
            analysis = f"⚠️ AI 分析暂时不可用: {str(e)}"
        
        elapsed_time = time.time() - start_time
        
        return {
            "success": True,
            "store_predictions": top_predictions,
            "total_stores": len(store_predictions),
            "total_predicted": round(total_predicted, 2),
            "overall_trend": overall_trend,
            "growth_stores": growth_stores,
            "decline_stores": decline_stores,
            "analysis": analysis,
            "elapsed_time": elapsed_time
        }
    
    def predict_by_platform(self, df: pd.DataFrame,
                             days: int = 7) -> Dict[str, Any]:
        """
        分平台预测
        
        Args:
            df: 数据
            days: 预测天数
            
        Returns:
            {"platform_predictions": [...], "analysis": "..."}
        """
        start_time = time.time()
        
        if df.empty:
            return {"success": False, "platform_predictions": [], "analysis": "数据为空"}
        
        platform_predictions = []
        platforms = df['platform'].unique()
        
        for platform in platforms:
            if not platform:
                continue
                
            platform_df = df[df['platform'] == platform]
            
            # 检查数据量
            unique_dates = platform_df['date'].nunique()
            if unique_dates < 3:
                continue
            
            # 聚合并预测
            daily_data = self.time_series_analyzer.aggregate_daily(platform_df)
            
            if daily_data.empty:
                continue
            
            trend = self.time_series_analyzer.calculate_trend(daily_data)
            forecast = self.time_series_analyzer.forecast_simple(platform_df, days=days)
            
            if 'error' in forecast:
                continue
            
            predictions = forecast.get('predictions', [])
            total_predicted = sum(p['predicted_value'] for p in predictions)
            
            # 计算置信度
            r_squared = trend.get('r_squared', 0)
            confidence = min(0.95, max(0.3, r_squared))
            
            platform_predictions.append({
                "platform": platform,
                "predicted_total": round(total_predicted, 2),
                "predicted_daily_avg": round(total_predicted / days, 2),
                "trend": trend.get('direction', '未知'),
                "confidence": round(confidence, 2),
                "predictions": predictions
            })
        
        # 按预测营收排序
        platform_predictions.sort(key=lambda x: x['predicted_total'], reverse=True)
        
        # 计算整体统计
        total_predicted = sum(p['predicted_total'] for p in platform_predictions)
        
        elapsed_time = time.time() - start_time
        
        return {
            "success": True,
            "platform_predictions": platform_predictions,
            "total_predicted": round(total_predicted, 2),
            "elapsed_time": elapsed_time
        }
    
    def get_prediction_summary(self, df: pd.DataFrame,
                                days: int = 7) -> Dict[str, Any]:
        """
        获取预测综合摘要
        
        Args:
            df: 数据
            days: 预测天数
            
        Returns:
            综合预测摘要
        """
        if df.empty:
            return {"success": False, "message": "数据为空"}
        
        # 营收预测
        revenue_result = self.predict_revenue(df, days=days, include_confidence=True)
        
        # 趋势分析
        trend_result = self.analyze_trend(df)
        
        # 门店预测
        store_result = self.predict_by_store(df, days=days, top_n=5)
        
        # 平台预测
        platform_result = self.predict_by_platform(df, days=days)
        
        return {
            "success": True,
            "revenue_prediction": {
                "total_predicted": revenue_result.get('total_predicted', 0),
                "daily_avg": revenue_result.get('daily_avg_predicted', 0),
                "trend": revenue_result.get('trend', '未知'),
                "confidence": revenue_result.get('confidence', 0),
                "predictions": revenue_result.get('predictions', [])
            },
            "trend_analysis": {
                "direction": trend_result.get('trend', {}).get('direction', '未知'),
                "strength": trend_result.get('trend', {}).get('strength', 0),
                "seasonality": trend_result.get('seasonality', {})
            },
            "store_predictions": store_result.get('store_predictions', [])[:5],
            "platform_predictions": platform_result.get('platform_predictions', []),
            "analysis": revenue_result.get('analysis', '')
        }
    
    def _ensure_derived_metrics(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """
        确保衍生指标存在，如果不存在则计算
        
        Args:
            df: 原始数据
            metric: 需要的指标名
            
        Returns:
            添加了衍生指标的数据
        """
        df = df.copy()
        
        # 到手率/利润率相关指标
        margin_metrics = ['net_margin_rate', 'margin_rate', 'profit_rate', 'real_net_margin_rate']
        
        if metric in margin_metrics:
            # 检查列是否已存在且有效数据不为空
            if metric in df.columns:
                valid_count = df[metric].notna().sum()
                if valid_count > 0:
                    return df  # 数据已存在且有效
            
            # 尝试从 actual_income 和 turnover (营业额) 计算
            if 'actual_income' in df.columns and 'turnover' in df.columns:
                df['net_margin_rate'] = df.apply(
                    lambda row: (row['actual_income'] / row['turnover'] * 100)
                    if pd.notna(row.get('turnover')) and row.get('turnover', 0) > 0 
                    else np.nan,
                    axis=1
                )
                df['margin_rate'] = df['net_margin_rate']  # 别名
                df['profit_rate'] = df['net_margin_rate']  # 别名
            # 备选：从 actual_income 和 platform_revenue 计算
            elif 'actual_income' in df.columns and 'platform_revenue' in df.columns:
                df['net_margin_rate'] = df.apply(
                    lambda row: (row['actual_income'] / row['platform_revenue'] * 100)
                    if pd.notna(row.get('platform_revenue')) and row.get('platform_revenue', 0) > 0 
                    else np.nan,
                    axis=1
                )
                df['margin_rate'] = df['net_margin_rate']  # 别名
                df['profit_rate'] = df['net_margin_rate']  # 别名
        
        # 转化率相关指标
        if metric == 'conversion_rate' or metric == 'order_conversion_rate':
            if 'valid_orders' in df.columns and 'entry_count' in df.columns:
                df['conversion_rate'] = df.apply(
                    lambda row: (row['valid_orders'] / row['entry_count'] * 100)
                    if pd.notna(row.get('entry_count')) and row.get('entry_count', 0) > 0
                    else np.nan,
                    axis=1
                )
            elif 'valid_order_count' in df.columns and 'entry_count' in df.columns:
                df['conversion_rate'] = df.apply(
                    lambda row: (row['valid_order_count'] / row['entry_count'] * 100)
                    if pd.notna(row.get('entry_count')) and row.get('entry_count', 0) > 0
                    else np.nan,
                    axis=1
                )
        
        # 客单价
        if metric == 'avg_order_value':
            if 'actual_income' in df.columns and 'valid_orders' in df.columns:
                df['avg_order_value'] = df.apply(
                    lambda row: (row['actual_income'] / row['valid_orders'])
                    if pd.notna(row.get('valid_orders')) and row.get('valid_orders', 0) > 0
                    else np.nan,
                    axis=1
                )
            elif 'actual_income' in df.columns and 'valid_order_count' in df.columns:
                df['avg_order_value'] = df.apply(
                    lambda row: (row['actual_income'] / row['valid_order_count'])
                    if pd.notna(row.get('valid_order_count')) and row.get('valid_order_count', 0) > 0
                    else np.nan,
                    axis=1
                )
        
        return df
    
    def _stream_analysis(self, messages: List[Dict]) -> str:
        """流式生成分析"""
        full_response = []
        for chunk in self.llm_adapter.stream_chat(messages):
            full_response.append(chunk)
        return ''.join(full_response)
    
    def _empty_prediction_result(self, message: str) -> Dict[str, Any]:
        """返回空的预测结果"""
        return {
            "success": False,
            "predictions": [],
            "trend": "未知",
            "confidence": 0,
            "analysis": message,
            "total_predicted": 0,
            "elapsed_time": 0
        }


# ========== 便捷函数 ==========

def predict_revenue(df: pd.DataFrame,
                    days: int = 7,
                    include_confidence: bool = True,
                    llm_adapter: BaseLLMAdapter = None) -> Dict[str, Any]:
    """
    便捷函数：营收预测
    
    Args:
        df: 数据
        days: 预测天数
        include_confidence: 是否包含置信区间
        llm_adapter: LLM 适配器
        
    Returns:
        预测结果
    """
    engine = PredictionEngine(llm_adapter)
    return engine.predict_revenue(df, days, include_confidence)


def analyze_trend(df: pd.DataFrame,
                  metric: str = 'actual_income') -> Dict[str, Any]:
    """
    便捷函数：趋势分析
    
    Args:
        df: 数据
        metric: 分析指标
        
    Returns:
        趋势分析结果
    """
    engine = PredictionEngine()
    return engine.analyze_trend(df, metric)


def predict_by_store(df: pd.DataFrame,
                     days: int = 7,
                     top_n: int = 10) -> Dict[str, Any]:
    """
    便捷函数：门店预测
    
    Args:
        df: 数据
        days: 预测天数
        top_n: 返回前 N 个门店
        
    Returns:
        门店预测结果
    """
    engine = PredictionEngine()
    return engine.predict_by_store(df, days, top_n)