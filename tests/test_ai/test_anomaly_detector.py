"""
异常检测器单元测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.analytics.anomaly_detector import AnomalyDetector, detect_anomalies


class TestAnomalyDetector:
    """异常检测器测试"""
    
    @pytest.fixture
    def normal_df(self):
        """创建正常数据"""
        np.random.seed(42)
        
        data = []
        for i in range(100):
            data.append({
                'brand_store_name': f'门店{(i // 20) + 1}',
                'actual_income': np.random.normal(10000, 1000),  # 正态分布
                'valid_order_count': np.random.normal(100, 10),
                'margin_rate': np.random.normal(70, 5),
                'conversion_rate': np.random.normal(15, 2)
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def df_with_anomaly(self):
        """创建包含异常的数据"""
        np.random.seed(42)
        
        data = []
        for i in range(100):
            data.append({
                'brand_store_name': f'门店{(i // 20) + 1}',
                'actual_income': np.random.normal(10000, 1000),
                'valid_order_count': np.random.normal(100, 10),
                'margin_rate': np.random.normal(70, 5),
                'conversion_rate': np.random.normal(15, 2)
            })
        
        # 添加异常值
        data.append({
            'brand_store_name': '门店1',
            'actual_income': 50000,  # 明显异常高
            'valid_order_count': 10,  # 明显异常低
            'margin_rate': 95,
            'conversion_rate': 50
        })
        
        data.append({
            'brand_store_name': '门店2',
            'actual_income': 100,  # 明显异常低
            'valid_order_count': 500,  # 明显异常高
            'margin_rate': 30,
            'conversion_rate': 2
        })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def time_series_df(self):
        """创建时间序列数据"""
        np.random.seed(42)
        dates = pd.date_range('2026-01-01', periods=14, freq='D')
        
        data = []
        for i, date in enumerate(dates):
            # 第10天有一个突然下降
            value = 10000 if i != 9 else 3000
            
            data.append({
                'date': date,
                'brand_store_name': '门店A',
                'actual_income': value,
                'valid_order_count': 100
            })
        
        return pd.DataFrame(data)
    
    def test_detect_no_anomaly(self, normal_df):
        """测试无异常数据"""
        detector = AnomalyDetector(threshold=3.0)  # 使用较高阈值
        anomalies = detector.detect(normal_df, metrics=['actual_income'])
        
        # 在3倍标准差下，正常数据应该很少或没有异常
        assert len(anomalies) <= 5
    
    def test_detect_with_anomaly(self, df_with_anomaly):
        """测试包含异常的数据"""
        detector = AnomalyDetector(threshold=2.0)
        anomalies = detector.detect(df_with_anomaly, metrics=['actual_income'])
        
        # 应该检测到异常
        assert len(anomalies) > 0
    
    def test_detect_zscore_method(self, df_with_anomaly):
        """测试 Z-score 方法"""
        detector = AnomalyDetector(threshold=2.0)
        anomalies = detector.detect(df_with_anomaly, method='zscore')
        
        assert isinstance(anomalies, list)
        if anomalies:
            assert 'metric' in anomalies[0]
            assert 'zscore' in anomalies[0]
            assert 'direction' in anomalies[0]
    
    def test_detect_iqr_method(self, df_with_anomaly):
        """测试 IQR 方法"""
        detector = AnomalyDetector(threshold=2.0)
        anomalies = detector.detect(df_with_anomaly, method='iqr')
        
        assert isinstance(anomalies, list)
        if anomalies:
            assert 'metric' in anomalies[0]
            assert 'direction' in anomalies[0]
    
    def test_detect_by_group(self, df_with_anomaly):
        """测试分组检测"""
        detector = AnomalyDetector(threshold=2.0)
        result = detector.detect_by_group(df_with_anomaly, group_col='brand_store_name')
        
        assert isinstance(result, dict)
    
    def test_detect_trend_anomaly(self, time_series_df):
        """测试趋势异常检测"""
        detector = AnomalyDetector()
        anomalies = detector.detect_trend_anomaly(
            time_series_df, 
            metric='actual_income',
            change_threshold=50.0  # 50%变化
        )
        
        # 应该检测到第10天的下降
        assert len(anomalies) > 0
    
    def test_detect_consecutive_anomaly_down(self, time_series_df):
        """测试连续下降检测"""
        # 创建连续下降数据
        np.random.seed(42)
        dates = pd.date_range('2026-01-01', periods=10, freq='D')
        
        data = []
        for i, date in enumerate(dates):
            # 连续5天下降
            value = 10000 - i * 500
            
            data.append({
                'date': date,
                'brand_store_name': '门店A',
                'actual_income': value
            })
        
        df = pd.DataFrame(data)
        
        detector = AnomalyDetector()
        anomalies = detector.detect_consecutive_anomaly(
            df,
            metric='actual_income',
            consecutive_days=3,
            direction='down'
        )
        
        assert len(anomalies) > 0
    
    def test_get_anomaly_summary(self, df_with_anomaly):
        """测试异常摘要"""
        detector = AnomalyDetector(threshold=2.0)
        anomalies = detector.detect(df_with_anomaly)
        summary = detector.get_anomaly_summary(anomalies)
        
        assert 'total' in summary
        assert 'by_metric' in summary
        assert 'by_direction' in summary
        assert 'high_severity' in summary
    
    def test_get_anomaly_summary_empty(self):
        """测试空异常列表摘要"""
        detector = AnomalyDetector()
        summary = detector.get_anomaly_summary([])
        
        assert summary['total'] == 0
    
    def test_custom_threshold(self, df_with_anomaly):
        """测试自定义阈值"""
        detector_low = AnomalyDetector(threshold=1.0)
        detector_high = AnomalyDetector(threshold=5.0)
        
        anomalies_low = detector_low.detect(df_with_anomaly, metrics=['actual_income'])
        anomalies_high = detector_high.detect(df_with_anomaly, metrics=['actual_income'])
        
        # 低阈值应该检测到更多异常
        assert len(anomalies_low) >= len(anomalies_high)
    
    def test_detect_empty_df(self):
        """测试空数据"""
        detector = AnomalyDetector()
        anomalies = detector.detect(pd.DataFrame())
        
        assert anomalies == []
    
    def test_detect_missing_metric(self, normal_df):
        """测试缺失指标"""
        detector = AnomalyDetector()
        anomalies = detector.detect(normal_df, metrics=['nonexistent_metric'])
        
        assert anomalies == []
    
    def test_severity_classification(self):
        """测试严重程度分类"""
        detector = AnomalyDetector(threshold=2.0)
        
        # 高严重度
        assert detector._get_severity(5.0, 2.0) == 'high'
        
        # 中等严重度
        assert detector._get_severity(3.5, 2.0) == 'medium'
        
        # 低严重度
        assert detector._get_severity(2.5, 2.0) == 'low'
    
    def test_detect_anomalies_convenience_function(self, df_with_anomaly):
        """测试便捷函数"""
        anomalies = detect_anomalies(df_with_anomaly, method='zscore')
        
        assert isinstance(anomalies, list)


class TestAnomalyDetectorEdgeCases:
    """异常检测器边界情况测试"""
    
    def test_single_value(self):
        """测试单个值"""
        detector = AnomalyDetector()
        df = pd.DataFrame({'actual_income': [1000]})
        
        anomalies = detector.detect(df, metrics=['actual_income'])
        
        # 单个值无法计算异常
        assert anomalies == []
    
    def test_all_same_values(self):
        """测试所有值相同"""
        detector = AnomalyDetector()
        df = pd.DataFrame({'actual_income': [1000] * 10})
        
        anomalies = detector.detect(df, metrics=['actual_income'])
        
        # 标准差为0，无法检测异常
        assert anomalies == []
    
    def test_nan_values(self):
        """测试包含 NaN"""
        detector = AnomalyDetector()
        df = pd.DataFrame({
            'actual_income': [1000, 2000, np.nan, 3000, 50000]
        })
        
        anomalies = detector.detect(df, metrics=['actual_income'])
        
        # 应该能处理 NaN
        assert isinstance(anomalies, list)
    
    def test_negative_values(self):
        """测试负值"""
        detector = AnomalyDetector()
        df = pd.DataFrame({
            'actual_income': [1000, 2000, 3000, -5000]  # 负值可能是异常
        })
        
        anomalies = detector.detect(df, metrics=['actual_income'])
        
        assert isinstance(anomalies, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])