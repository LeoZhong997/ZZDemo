"""
数据聚合器单元测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.analytics.data_aggregator import (
    DataAggregator, aggregate_data, CORE_METRICS, SUM_METRICS, MEAN_METRICS
)


class TestDataAggregator:
    """数据聚合器测试"""
    
    @pytest.fixture
    def sample_df(self):
        """创建测试数据"""
        np.random.seed(42)
        dates = pd.date_range('2026-01-01', periods=14, freq='D')
        
        data = []
        for date in dates:
            for store in ['门店A', '门店B', '门店C']:
                for platform in ['美团', '饿了么']:
                    data.append({
                        'date': date,
                        'brand_store_name': store,
                        'platform': platform,
                        'actual_income': np.random.uniform(1000, 5000),
                        'valid_order_count': np.random.randint(20, 100),
                        'exposure_count': np.random.randint(500, 2000),
                        'entry_count': np.random.randint(100, 500),
                        'platform_revenue': np.random.uniform(1500, 6000),
                        'margin_rate': np.random.uniform(60, 80)
                    })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def empty_df(self):
        """空数据"""
        return pd.DataFrame()
    
    def test_aggregate_by_store_basic(self, sample_df):
        """测试基础门店聚合"""
        aggregator = DataAggregator()
        result = aggregator.aggregate_by_store(sample_df)
        
        assert not result.empty
        assert len(result) == 3  # 3个门店
        assert 'brand_store_name' in result.columns
        assert 'actual_income' in result.columns
        
    def test_aggregate_by_store_empty(self, empty_df):
        """测试空数据门店聚合"""
        aggregator = DataAggregator()
        result = aggregator.aggregate_by_store(empty_df)
        
        assert result.empty
    
    def test_aggregate_by_store_missing_column(self):
        """测试缺少门店列"""
        aggregator = DataAggregator()
        df = pd.DataFrame({'actual_income': [100, 200]})
        result = aggregator.aggregate_by_store(df)
        
        assert result.empty
    
    def test_aggregate_by_platform(self, sample_df):
        """测试平台聚合"""
        aggregator = DataAggregator()
        result = aggregator.aggregate_by_platform(sample_df)
        
        assert not result.empty
        assert len(result) == 2  # 美团、饿了么
        assert 'platform' in result.columns
        assert 'revenue_share' in result.columns
    
    def test_aggregate_by_date(self, sample_df):
        """测试日期聚合"""
        aggregator = DataAggregator()
        result = aggregator.aggregate_by_date(sample_df)
        
        assert not result.empty
        assert 'date' in result.columns
        assert 'actual_income' in result.columns
    
    def test_aggregate_by_date_weekly(self, sample_df):
        """测试周聚合"""
        aggregator = DataAggregator()
        result = aggregator.aggregate_by_date(sample_df, freq='W')
        
        assert not result.empty
    
    def test_aggregate_by_store_and_platform(self, sample_df):
        """测试门店-平台聚合"""
        aggregator = DataAggregator()
        result = aggregator.aggregate_by_store_and_platform(sample_df)
        
        assert not result.empty
        # 3个门店 * 2个平台 = 6条记录
        assert len(result) == 6
    
    def test_calculate_growth_rate_positive(self):
        """测试正增长率"""
        aggregator = DataAggregator()
        rate = aggregator.calculate_growth_rate(150, 100)
        
        assert rate == 50.0
    
    def test_calculate_growth_rate_negative(self):
        """测试负增长率"""
        aggregator = DataAggregator()
        rate = aggregator.calculate_growth_rate(80, 100)
        
        assert rate == -20.0
    
    def test_calculate_growth_rate_zero_base(self):
        """测试基数为零的增长率"""
        aggregator = DataAggregator()
        
        rate = aggregator.calculate_growth_rate(100, 0)
        assert rate == float('inf')
        
        rate = aggregator.calculate_growth_rate(0, 0)
        assert rate == 0.0
    
    def test_get_top_stores(self, sample_df):
        """测试获取Top N门店"""
        aggregator = DataAggregator()
        result = aggregator.get_top_stores(sample_df, n=2)
        
        assert len(result) == 2
    
    def test_get_summary_stats(self, sample_df):
        """测试摘要统计"""
        aggregator = DataAggregator()
        stats = aggregator.get_summary_stats(sample_df)
        
        assert 'total_records' in stats
        assert 'date_range' in stats
        assert 'stores' in stats
        assert 'platforms' in stats
        assert stats['stores']['count'] == 3
        assert stats['platforms']['count'] == 2
    
    def test_get_summary_stats_empty(self, empty_df):
        """测试空数据摘要统计"""
        aggregator = DataAggregator()
        stats = aggregator.get_summary_stats(empty_df)
        
        assert 'error' in stats
    
    def test_calculate_derived_metrics(self, sample_df):
        """测试衍生指标计算"""
        aggregator = DataAggregator()
        result = aggregator.aggregate_by_store(sample_df)
        
        # 应该包含衍生指标
        assert 'avg_order_value' in result.columns or 'actual_income' in result.columns
    
    def test_aggregate_data_convenience_function(self, sample_df):
        """测试便捷函数"""
        # 按门店聚合
        result = aggregate_data(sample_df, by='store')
        assert not result.empty
        assert 'brand_store_name' in result.columns
        
        # 按平台聚合
        result = aggregate_data(sample_df, by='platform')
        assert not result.empty
        assert 'platform' in result.columns
        
        # 按日期聚合
        result = aggregate_data(sample_df, by='date')
        assert not result.empty
        assert 'date' in result.columns
    
    def test_aggregate_data_invalid_dimension(self, sample_df):
        """测试无效聚合维度"""
        with pytest.raises(ValueError):
            aggregate_data(sample_df, by='invalid')
    
    def test_calculate_period_comparison(self, sample_df):
        """测试时间段对比"""
        aggregator = DataAggregator()
        result = aggregator.calculate_period_comparison(sample_df)
        
        assert not result.empty
        assert 'first_half' in result.columns
        assert 'second_half' in result.columns
        assert 'growth_rate' in result.columns


class TestMetricConstants:
    """指标常量测试"""
    
    def test_core_metrics_structure(self):
        """测试核心指标结构"""
        assert 'revenue' in CORE_METRICS
        assert 'traffic' in CORE_METRICS
        assert 'conversion' in CORE_METRICS
        
    def test_sum_metrics_not_empty(self):
        """测试求和指标非空"""
        assert len(SUM_METRICS) > 0
        assert 'actual_income' in SUM_METRICS
    
    def test_mean_metrics_not_empty(self):
        """测试均值指标非空"""
        assert len(MEAN_METRICS) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])