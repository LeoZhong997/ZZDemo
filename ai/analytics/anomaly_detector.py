"""
异常检测器
提供基于 Z-score 和 IQR 方法的异常检测功能
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

from ai.config import get_ai_config

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    异常检测器
    
    功能：
    - 指标异常检测（Z-score 方法）
    - 趋势异常检测（突变检测）
    - 支持 IQR 方法
    """
    
    def __init__(self, threshold: float = None):
        """
        初始化异常检测器
        
        Args:
            threshold: 异常阈值（Z-score），默认从配置读取
        """
        self.config = get_ai_config('analysis', {})
        self.threshold = threshold or self.config.get('anomaly_threshold', 2.0)
    
    def detect(self, df: pd.DataFrame,
               metrics: List[str] = None,
               method: str = 'zscore') -> List[Dict[str, Any]]:
        """
        检测异常值
        
        Args:
            df: 数据
            metrics: 要检测的指标列表，默认检测核心指标
            method: 检测方法 ('zscore' 或 'iqr')
            
        Returns:
            异常列表，每个元素包含:
            {
                'metric': 指标名,
                'index': 数据索引,
                'value': 异常值,
                'zscore': Z分数,
                'direction': 'high' 或 'low',
                'severity': 严重程度
            }
        """
        if df.empty:
            return []
        
        # 默认检测的指标
        if metrics is None:
            metrics = ['actual_income', 'valid_order_count', 'margin_rate', 'conversion_rate']
        
        # 过滤存在的指标
        metrics = [m for m in metrics if m in df.columns]
        
        anomalies = []
        
        for metric in metrics:
            if method == 'zscore':
                metric_anomalies = self._detect_zscore(df, metric)
            elif method == 'iqr':
                metric_anomalies = self._detect_iqr(df, metric)
            else:
                logger.warning(f"未知的检测方法: {method}，使用 zscore")
                metric_anomalies = self._detect_zscore(df, metric)
            
            anomalies.extend(metric_anomalies)
        
        # 按严重程度排序
        anomalies.sort(key=lambda x: abs(x.get('zscore', 0)), reverse=True)
        
        logger.info(f"检测完成：发现 {len(anomalies)} 个异常")
        return anomalies
    
    def detect_by_group(self, df: pd.DataFrame,
                         metrics: List[str] = None,
                         group_col: str = 'brand_store_name',
                         method: str = 'zscore') -> Dict[str, List[Dict]]:
        """
        分组检测异常
        
        Args:
            df: 数据
            metrics: 要检测的指标
            group_col: 分组列名
            method: 检测方法
            
        Returns:
            {组名: [异常列表]}
        """
        if df.empty or group_col not in df.columns:
            return {}
        
        result = {}
        
        for group_value in df[group_col].unique():
            group_df = df[df[group_col] == group_value]
            anomalies = self.detect(group_df, metrics, method)
            
            if anomalies:
                result[str(group_value)] = anomalies
        
        return result
    
    def detect_trend_anomaly(self, df: pd.DataFrame,
                              metric: str = 'actual_income',
                              date_col: str = 'date',
                              window: int = 3,
                              change_threshold: float = 30.0) -> List[Dict[str, Any]]:
        """
        检测趋势异常（突然下降或上升）
        
        Args:
            df: 数据，需包含日期列
            metric: 检测指标
            date_col: 日期列名
            window: 滚动窗口大小
            change_threshold: 变化阈值百分比
            
        Returns:
            趋势异常列表
        """
        if df.empty or metric not in df.columns:
            return []
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # 按日期聚合
        daily = df.groupby(date_col)[metric].sum().reset_index()
        
        if len(daily) < window + 1:
            logger.warning("数据点太少，无法检测趋势异常")
            return []
        
        # 计算滚动均值
        daily['rolling_mean'] = daily[metric].rolling(window=window, min_periods=1).mean()
        daily['rolling_std'] = daily[metric].rolling(window=window, min_periods=1).std()
        
        # 计算变化率
        daily['prev_value'] = daily[metric].shift(1)
        daily['change_rate'] = ((daily[metric] - daily['prev_value']) / daily['prev_value'] * 100).fillna(0)
        
        anomalies = []
        
        for idx, row in daily.iterrows():
            if idx < window:
                continue
            
            # 检测突变
            change_rate = row['change_rate']
            
            if abs(change_rate) >= change_threshold:
                anomaly = {
                    'type': 'trend_change',
                    'metric': metric,
                    'date': str(row[date_col].date()),
                    'value': float(row[metric]),
                    'prev_value': float(row['prev_value']) if pd.notna(row['prev_value']) else None,
                    'change_rate': float(change_rate),
                    'direction': 'drop' if change_rate < 0 else 'spike',
                    'severity': self._get_severity(abs(change_rate), change_threshold)
                }
                anomalies.append(anomaly)
            
            # 检测偏离滚动均值
            if pd.notna(row['rolling_std']) and row['rolling_std'] > 0:
                zscore = (row[metric] - row['rolling_mean']) / row['rolling_std']
                
                if abs(zscore) > self.threshold:
                    anomaly = {
                        'type': 'deviation',
                        'metric': metric,
                        'date': str(row[date_col].date()),
                        'value': float(row[metric]),
                        'expected': float(row['rolling_mean']),
                        'zscore': float(zscore),
                        'direction': 'low' if zscore < 0 else 'high',
                        'severity': self._get_severity(abs(zscore), self.threshold)
                    }
                    anomalies.append(anomaly)
        
        logger.info(f"趋势检测完成：发现 {len(anomalies)} 个趋势异常")
        return anomalies
    
    def detect_consecutive_anomaly(self, df: pd.DataFrame,
                                    metric: str = 'actual_income',
                                    date_col: str = 'date',
                                    consecutive_days: int = 3,
                                    direction: str = 'down') -> List[Dict[str, Any]]:
        """
        检测连续异常（连续下降或连续上升）
        
        Args:
            df: 数据
            metric: 检测指标
            date_col: 日期列名
            consecutive_days: 连续天数阈值
            direction: 'down' 连续下降, 'up' 连续上升
            
        Returns:
            连续异常列表
        """
        if df.empty or metric not in df.columns:
            return []
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # 按日期聚合
        daily = df.groupby(date_col)[metric].sum().reset_index()
        
        if len(daily) < consecutive_days:
            return []
        
        # 计算日变化
        daily['change'] = daily[metric].diff()
        
        anomalies = []
        consecutive_count = 0
        start_idx = None
        
        for idx in range(1, len(daily)):
            change = daily.iloc[idx]['change']
            
            if pd.isna(change):
                continue
            
            # 检查方向
            is_target_direction = (direction == 'down' and change < 0) or \
                                  (direction == 'up' and change > 0)
            
            if is_target_direction:
                if consecutive_count == 0:
                    start_idx = idx - 1
                consecutive_count += 1
            else:
                # 连续中断，检查是否达到阈值
                if consecutive_count >= consecutive_days:
                    anomaly = {
                        'type': 'consecutive',
                        'metric': metric,
                        'direction': direction,
                        'start_date': str(daily.iloc[start_idx][date_col].date()),
                        'end_date': str(daily.iloc[idx - 1][date_col].date()),
                        'consecutive_days': consecutive_count + 1,
                        'total_change': float(daily.iloc[idx - 1][metric] - daily.iloc[start_idx][metric])
                    }
                    anomalies.append(anomaly)
                
                consecutive_count = 0
                start_idx = None
        
        # 检查末尾是否有连续异常
        if consecutive_count >= consecutive_days:
            anomaly = {
                'type': 'consecutive',
                'metric': metric,
                'direction': direction,
                'start_date': str(daily.iloc[start_idx][date_col].date()),
                'end_date': str(daily.iloc[-1][date_col].date()),
                'consecutive_days': consecutive_count + 1,
                'total_change': float(daily.iloc[-1][metric] - daily.iloc[start_idx][metric])
            }
            anomalies.append(anomaly)
        
        return anomalies
    
    def get_anomaly_summary(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """
        获取异常摘要
        
        Args:
            anomalies: 异常列表
            
        Returns:
            摘要信息
        """
        if not anomalies:
            return {
                'total': 0,
                'by_metric': {},
                'by_direction': {},
                'high_severity': 0
            }
        
        summary = {
            'total': len(anomalies),
            'by_metric': {},
            'by_direction': {'high': 0, 'low': 0},
            'high_severity': 0
        }
        
        for anomaly in anomalies:
            # 按指标统计
            metric = anomaly.get('metric', 'unknown')
            summary['by_metric'][metric] = summary['by_metric'].get(metric, 0) + 1
            
            # 按方向统计
            direction = anomaly.get('direction', '')
            if direction in ['high', 'spike', 'up']:
                summary['by_direction']['high'] += 1
            elif direction in ['low', 'drop', 'down']:
                summary['by_direction']['low'] += 1
            
            # 高严重度
            if anomaly.get('severity') == 'high':
                summary['high_severity'] += 1
        
        return summary
    
    def _detect_zscore(self, df: pd.DataFrame, metric: str) -> List[Dict[str, Any]]:
        """使用 Z-score 方法检测异常"""
        anomalies = []
        
        values = df[metric].dropna()
        
        if len(values) < 3:
            return anomalies
        
        mean = values.mean()
        std = values.std()
        
        if std == 0:
            return anomalies
        
        for idx, value in df[metric].items():
            if pd.isna(value):
                continue
            
            zscore = (value - mean) / std
            
            if abs(zscore) > self.threshold:
                anomaly = {
                    'type': 'value',
                    'metric': metric,
                    'index': int(idx),
                    'value': float(value),
                    'mean': float(mean),
                    'zscore': float(zscore),
                    'direction': 'high' if zscore > 0 else 'low',
                    'severity': self._get_severity(abs(zscore), self.threshold)
                }
                
                # 添加标识信息（如果有）
                if 'brand_store_name' in df.columns:
                    anomaly['store'] = df.loc[idx, 'brand_store_name']
                if 'date' in df.columns:
                    anomaly['date'] = str(df.loc[idx, 'date'])
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_iqr(self, df: pd.DataFrame, metric: str) -> List[Dict[str, Any]]:
        """使用 IQR (四分位距) 方法检测异常"""
        anomalies = []
        
        values = df[metric].dropna()
        
        if len(values) < 4:
            return anomalies
        
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        for idx, value in df[metric].items():
            if pd.isna(value):
                continue
            
            if value < lower_bound or value > upper_bound:
                direction = 'high' if value > upper_bound else 'low'
                deviation = abs(value - (upper_bound if direction == 'high' else lower_bound))
                
                anomaly = {
                    'type': 'value',
                    'metric': metric,
                    'index': int(idx),
                    'value': float(value),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'direction': direction,
                    'severity': self._get_severity(deviation, iqr)
                }
                
                if 'brand_store_name' in df.columns:
                    anomaly['store'] = df.loc[idx, 'brand_store_name']
                if 'date' in df.columns:
                    anomaly['date'] = str(df.loc[idx, 'date'])
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def _get_severity(self, value: float, threshold: float) -> str:
        """判断严重程度"""
        ratio = value / threshold
        if ratio >= 2:
            return 'high'
        elif ratio >= 1.5:
            return 'medium'
        else:
            return 'low'


def detect_anomalies(df: pd.DataFrame, 
                     method: str = 'zscore',
                     **kwargs) -> List[Dict[str, Any]]:
    """
    便捷函数：检测异常
    
    Args:
        df: 数据
        method: 检测方法 ('zscore' 或 'iqr')
        **kwargs: 其他参数
        
    Returns:
        异常列表
    """
    detector = AnomalyDetector(threshold=kwargs.get('threshold'))
    return detector.detect(df, method=method, metrics=kwargs.get('metrics'))