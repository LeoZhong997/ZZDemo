"""
数据聚合器
提供门店、平台、时间维度的数据聚合功能
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

from ai.config import get_ai_config

logger = logging.getLogger(__name__)


# 核心指标定义
CORE_METRICS = {
    'revenue': ['actual_income', 'platform_revenue', 'settlement_amount'],
    'traffic': ['exposure_count', 'entry_count', 'visitor_count'],
    'conversion': ['valid_order_count', 'conversion_rate', 'order_completion_rate'],
    'cost': ['platform_commission', 'promotion_cost', 'packaging_cost'],
    'efficiency': ['margin_rate', 'avg_order_value', 'cost_per_order']
}

# 聚合规则：哪些指标用 sum，哪些用 mean
SUM_METRICS = [
    'actual_income', 'platform_revenue', 'settlement_amount',
    'exposure_count', 'entry_count', 'visitor_count',
    'valid_order_count', 'invalid_order_count',
    'platform_commission', 'promotion_cost', 'packaging_cost'
]

MEAN_METRICS = [
    'margin_rate', 'conversion_rate', 'order_completion_rate',
    'avg_order_value', 'cost_per_order', 'competitor_rank'
]


class DataAggregator:
    """
    数据聚合器
    
    功能：
    - 门店维度聚合
    - 平台维度聚合
    - 时间维度聚合
    - 增长率计算
    """
    
    def __init__(self):
        """初始化数据聚合器"""
        self.config = get_ai_config('analysis', {})
        self.top_n = self.config.get('top_n_stores', 10)
    
    def aggregate_by_store(self, df: pd.DataFrame, 
                           metrics: List[str] = None) -> pd.DataFrame:
        """
        按门店聚合数据
        
        Args:
            df: 原始数据，需包含 brand_store_name 列
            metrics: 要聚合的指标列表，默认聚合所有核心指标
            
        Returns:
            包含门店指标的 DataFrame，按实收降序排列
        """
        if df.empty:
            logger.warning("输入数据为空")
            return pd.DataFrame()
        
        if 'brand_store_name' not in df.columns:
            logger.error("数据缺少 brand_store_name 列")
            return pd.DataFrame()
        
        # 确定要聚合的指标
        if metrics is None:
            # 自动检测存在的指标
            all_metrics = []
            for category_metrics in CORE_METRICS.values():
                all_metrics.extend(category_metrics)
            metrics = [m for m in all_metrics if m in df.columns]
        
        # 构建聚合规则
        agg_rules = {}
        for metric in metrics:
            if metric in df.columns:
                if metric in SUM_METRICS:
                    agg_rules[metric] = 'sum'
                elif metric in MEAN_METRICS:
                    agg_rules[metric] = 'mean'
                else:
                    agg_rules[metric] = 'sum'  # 默认求和
        
        if not agg_rules:
            logger.warning("没有可聚合的指标")
            return pd.DataFrame()
        
        # 执行聚合
        result = df.groupby('brand_store_name').agg(agg_rules).reset_index()
        
        # 计算衍生指标
        result = self._calculate_derived_metrics(result)
        
        # 按实收降序排列
        if 'actual_income' in result.columns:
            result = result.sort_values('actual_income', ascending=False)
        
        logger.info(f"门店聚合完成：{len(result)} 个门店")
        return result
    
    def aggregate_by_platform(self, df: pd.DataFrame,
                               metrics: List[str] = None) -> pd.DataFrame:
        """
        按平台聚合数据
        
        Args:
            df: 原始数据，需包含 platform 列
            metrics: 要聚合的指标列表
            
        Returns:
            包含平台指标的 DataFrame
        """
        if df.empty:
            logger.warning("输入数据为空")
            return pd.DataFrame()
        
        if 'platform' not in df.columns:
            logger.error("数据缺少 platform 列")
            return pd.DataFrame()
        
        # 确定要聚合的指标
        if metrics is None:
            all_metrics = []
            for category_metrics in CORE_METRICS.values():
                all_metrics.extend(category_metrics)
            metrics = [m for m in all_metrics if m in df.columns]
        
        # 构建聚合规则
        agg_rules = {}
        for metric in metrics:
            if metric in df.columns:
                if metric in SUM_METRICS:
                    agg_rules[metric] = 'sum'
                elif metric in MEAN_METRICS:
                    agg_rules[metric] = 'mean'
                else:
                    agg_rules[metric] = 'sum'
        
        if not agg_rules:
            return pd.DataFrame()
        
        # 执行聚合
        result = df.groupby('platform').agg(agg_rules).reset_index()
        
        # 计算衍生指标
        result = self._calculate_derived_metrics(result)
        
        # 计算平台占比
        if 'actual_income' in result.columns:
            total = result['actual_income'].sum()
            if total > 0:
                result['revenue_share'] = result['actual_income'] / total * 100
        
        logger.info(f"平台聚合完成：{len(result)} 个平台")
        return result
    
    def aggregate_by_date(self, df: pd.DataFrame,
                          metrics: List[str] = None,
                          freq: str = 'D') -> pd.DataFrame:
        """
        按日期聚合数据
        
        Args:
            df: 原始数据，需包含 date 列
            metrics: 要聚合的指标列表
            freq: 聚合频率，'D'=日, 'W'=周, 'M'=月
            
        Returns:
            包含日期指标的 DataFrame
        """
        if df.empty:
            logger.warning("输入数据为空")
            return pd.DataFrame()
        
        if 'date' not in df.columns:
            logger.error("数据缺少 date 列")
            return pd.DataFrame()
        
        # 确保日期格式正确
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # 确定要聚合的指标
        if metrics is None:
            all_metrics = []
            for category_metrics in CORE_METRICS.values():
                all_metrics.extend(category_metrics)
            metrics = [m for m in all_metrics if m in df.columns]
        
        # 构建聚合规则
        agg_rules = {}
        for metric in metrics:
            if metric in df.columns:
                if metric in SUM_METRICS:
                    agg_rules[metric] = 'sum'
                elif metric in MEAN_METRICS:
                    agg_rules[metric] = 'mean'
                else:
                    agg_rules[metric] = 'sum'
        
        if not agg_rules:
            return pd.DataFrame()
        
        # 执行聚合
        result = df.groupby(pd.Grouper(key='date', freq=freq)).agg(agg_rules).reset_index()
        
        # 计算衍生指标
        result = self._calculate_derived_metrics(result)
        
        logger.info(f"日期聚合完成：{len(result)} 个时间点，频率={freq}")
        return result
    
    def aggregate_by_store_and_platform(self, df: pd.DataFrame,
                                         metrics: List[str] = None) -> pd.DataFrame:
        """
        按门店和平台聚合数据
        
        Args:
            df: 原始数据
            metrics: 要聚合的指标列表
            
        Returns:
            包含门店-平台组合指标的 DataFrame
        """
        if df.empty:
            return pd.DataFrame()
        
        if 'brand_store_name' not in df.columns or 'platform' not in df.columns:
            logger.error("数据缺少 brand_store_name 或 platform 列")
            return pd.DataFrame()
        
        # 确定要聚合的指标
        if metrics is None:
            all_metrics = []
            for category_metrics in CORE_METRICS.values():
                all_metrics.extend(category_metrics)
            metrics = [m for m in all_metrics if m in df.columns]
        
        # 构建聚合规则
        agg_rules = {}
        for metric in metrics:
            if metric in df.columns:
                if metric in SUM_METRICS:
                    agg_rules[metric] = 'sum'
                elif metric in MEAN_METRICS:
                    agg_rules[metric] = 'mean'
                else:
                    agg_rules[metric] = 'sum'
        
        if not agg_rules:
            return pd.DataFrame()
        
        # 执行聚合
        result = df.groupby(['brand_store_name', 'platform']).agg(agg_rules).reset_index()
        
        # 计算衍生指标
        result = self._calculate_derived_metrics(result)
        
        logger.info(f"门店-平台聚合完成：{len(result)} 条记录")
        return result
    
    def calculate_growth_rate(self, current: float, previous: float) -> float:
        """
        计算增长率
        
        Args:
            current: 当前值
            previous: 之前值
            
        Returns:
            增长率百分比，如果基数为0返回 0 或 inf
        """
        if previous == 0:
            if current > 0:
                return float('inf')  # 从0增长
            elif current < 0:
                return float('-inf')
            else:
                return 0.0
        
        return ((current - previous) / abs(previous)) * 100
    
    def calculate_period_comparison(self, df: pd.DataFrame,
                                     metric: str = 'actual_income',
                                     group_by: str = 'brand_store_name') -> pd.DataFrame:
        """
        计算时间段对比（前半段 vs 后半段）
        
        Args:
            df: 数据，需包含 date 列
            metric: 对比的指标
            group_by: 分组字段
            
        Returns:
            包含对比结果的 DataFrame
        """
        if df.empty or metric not in df.columns:
            return pd.DataFrame()
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # 分割为前后两段
        mid_date = df['date'].min() + (df['date'].max() - df['date'].min()) / 2
        
        first_half = df[df['date'] <= mid_date]
        second_half = df[df['date'] > mid_date]
        
        # 聚合
        first_agg = first_half.groupby(group_by)[metric].sum()
        second_agg = second_half.groupby(group_by)[metric].sum()
        
        # 合并
        result = pd.DataFrame({
            'first_half': first_agg,
            'second_half': second_agg
        }).fillna(0)
        
        # 计算变化
        result['change'] = result['second_half'] - result['first_half']
        result['growth_rate'] = result.apply(
            lambda row: self.calculate_growth_rate(row['second_half'], row['first_half']),
            axis=1
        )
        
        return result.reset_index()
    
    def get_top_stores(self, df: pd.DataFrame, 
                       metric: str = 'actual_income',
                       n: int = None) -> pd.DataFrame:
        """
        获取 Top N 门店
        
        Args:
            df: 数据
            metric: 排名指标
            n: 数量，默认从配置读取
            
        Returns:
            Top N 门店 DataFrame
        """
        if n is None:
            n = self.top_n
        
        store_data = self.aggregate_by_store(df, metrics=[metric])
        
        if store_data.empty:
            return store_data
        
        return store_data.head(n)
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取数据摘要统计
        
        Args:
            df: 原始数据
            
        Returns:
            摘要统计字典
        """
        if df.empty:
            return {"error": "数据为空"}
        
        stats = {
            "total_records": len(df),
            "date_range": {
                "start": str(df['date'].min()) if 'date' in df.columns else None,
                "end": str(df['date'].max()) if 'date' in df.columns else None,
                "days": (df['date'].max() - df['date'].min()).days + 1 if 'date' in df.columns else 0
            },
            "stores": {
                "count": df['brand_store_name'].nunique() if 'brand_store_name' in df.columns else 0,
            },
            "platforms": {
                "count": df['platform'].nunique() if 'platform' in df.columns else 0,
                "list": df['platform'].unique().tolist() if 'platform' in df.columns else []
            }
        }
        
        # 核心指标汇总
        if 'actual_income' in df.columns:
            stats['revenue'] = {
                "total": float(df['actual_income'].sum()),
                "mean": float(df['actual_income'].mean()),
                "max": float(df['actual_income'].max()),
                "min": float(df['actual_income'].min())
            }
        
        if 'valid_order_count' in df.columns:
            stats['orders'] = {
                "total": int(df['valid_order_count'].sum()),
                "mean": float(df['valid_order_count'].mean())
            }
        
        return stats
    
    def _calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算衍生指标
        
        Args:
            df: 聚合后的数据
            
        Returns:
            添加了衍生指标的数据
        """
        df = df.copy()
        
        # 客单价 = 实收 / 订单数
        if 'actual_income' in df.columns and 'valid_order_count' in df.columns:
            df['avg_order_value'] = df.apply(
                lambda row: row['actual_income'] / row['valid_order_count'] 
                if row['valid_order_count'] > 0 else 0,
                axis=1
            )
        
        # 转化率 = 订单数 / 进店量
        if 'valid_order_count' in df.columns and 'entry_count' in df.columns:
            df['conversion_rate'] = df.apply(
                lambda row: row['valid_order_count'] / row['entry_count'] * 100 
                if row['entry_count'] > 0 else 0,
                axis=1
            )
        
        # 到手率 = 实收 / 平台营业额
        if 'actual_income' in df.columns and 'platform_revenue' in df.columns:
            df['margin_rate'] = df.apply(
                lambda row: row['actual_income'] / row['platform_revenue'] * 100 
                if row['platform_revenue'] > 0 else 0,
                axis=1
            )
        
        return df


def aggregate_data(df: pd.DataFrame, 
                   by: str = 'store',
                   **kwargs) -> pd.DataFrame:
    """
    便捷函数：聚合数据
    
    Args:
        df: 原始数据
        by: 聚合维度 (store/platform/date/store_platform)
        **kwargs: 其他参数传递给对应的聚合方法
        
    Returns:
        聚合后的 DataFrame
    """
    aggregator = DataAggregator()
    
    if by == 'store':
        return aggregator.aggregate_by_store(df, **kwargs)
    elif by == 'platform':
        return aggregator.aggregate_by_platform(df, **kwargs)
    elif by == 'date':
        return aggregator.aggregate_by_date(df, **kwargs)
    elif by == 'store_platform':
        return aggregator.aggregate_by_store_and_platform(df, **kwargs)
    else:
        raise ValueError(f"不支持的聚合维度: {by}")