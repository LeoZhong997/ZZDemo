"""
AI 分析模块
提供数据聚合、特征计算、异常检测、时间序列分析功能
"""

from ai.analytics.data_aggregator import (
    DataAggregator,
    aggregate_data,
    CORE_METRICS,
    SUM_METRICS,
    MEAN_METRICS
)

from ai.analytics.feature_calculator import (
    FeatureCalculator,
    calculate_features,
    DEFAULT_SCORE_WEIGHTS
)

from ai.analytics.anomaly_detector import (
    AnomalyDetector,
    detect_anomalies
)

from ai.analytics.time_series import (
    TimeSeriesAnalyzer,
    analyze_time_series
)


__all__ = [
    # 数据聚合
    'DataAggregator',
    'aggregate_data',
    'CORE_METRICS',
    'SUM_METRICS',
    'MEAN_METRICS',
    
    # 特征计算
    'FeatureCalculator',
    'calculate_features',
    'DEFAULT_SCORE_WEIGHTS',
    
    # 异常检测
    'AnomalyDetector',
    'detect_anomalies',
    
    # 时间序列
    'TimeSeriesAnalyzer',
    'analyze_time_series'
]