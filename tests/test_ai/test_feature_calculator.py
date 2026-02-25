"""
特征计算器单元测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.analytics.feature_calculator import (
    FeatureCalculator, calculate_features, DEFAULT_SCORE_WEIGHTS
)


class TestFeatureCalculator:
    """特征计算器测试"""
    
    @pytest.fixture
    def sample_df(self):
        """创建测试数据"""
        np.random.seed(42)
        
        data = []
        for store in ['门店A', '门店B', '门店C']:
            data.append({
                'brand_store_name': store,
                'actual_income': np.random.uniform(10000, 50000),
                'valid_order_count': np.random.randint(100, 500),
                'margin_rate': np.random.uniform(60, 80),
                'conversion_rate': np.random.uniform(10, 25),
                'exposure_count': np.random.randint(1000, 5000),
                'entry_count': np.random.randint(200, 800)
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def time_series_df(self):
        """创建时间序列测试数据"""
        np.random.seed(42)
        dates = pd.date_range('2026-01-01', periods=14, freq='D')
        
        data = []
        for date in dates:
            data.append({
                'date': date,
                'brand_store_name': '门店A',
                'actual_income': 10000 + np.random.uniform(-1000, 1000),
                'valid_order_count': 100 + np.random.randint(-10, 10)
            })
        
        return pd.DataFrame(data)
    
    def test_calculate_ranking_basic(self, sample_df):
        """测试基础排名计算"""
        calculator = FeatureCalculator()
        result = calculator.calculate_ranking(sample_df, 'actual_income')
        
        assert not result.empty
        assert 'rank' in result.columns
        assert 'rank_label' in result.columns
        assert 'percentile' in result.columns
        assert len(result) == 3
    
    def test_calculate_ranking_ascending(self, sample_df):
        """测试升序排名"""
        calculator = FeatureCalculator()
        result = calculator.calculate_ranking(sample_df, 'actual_income', ascending=True)
        
        # 排名1应该是最小值
        first_rank = result[result['rank'] == 1].iloc[0]
        assert first_rank['actual_income'] == sample_df['actual_income'].min()
    
    def test_calculate_ranking_descending(self, sample_df):
        """测试降序排名"""
        calculator = FeatureCalculator()
        result = calculator.calculate_ranking(sample_df, 'actual_income', ascending=False)
        
        # 排名1应该是最大值
        first_rank = result[result['rank'] == 1].iloc[0]
        assert first_rank['actual_income'] == sample_df['actual_income'].max()
    
    def test_calculate_funnel_metrics(self, sample_df):
        """测试转化漏斗计算"""
        calculator = FeatureCalculator()
        result = calculator.calculate_funnel_metrics(sample_df)
        
        assert 'exposure_to_entry' in result
        assert 'entry_to_order' in result
        assert 'overall_conversion' in result
        assert 'funnel_data' in result
        assert 'drop_off' in result
    
    def test_calculate_funnel_metrics_empty(self):
        """测试空数据漏斗计算"""
        calculator = FeatureCalculator()
        result = calculator.calculate_funnel_metrics(pd.DataFrame())
        
        assert 'error' in result
    
    def test_calculate_store_score(self):
        """测试门店评分计算"""
        calculator = FeatureCalculator()
        
        metrics = {
            'actual_income': 50000,
            'valid_order_count': 500,
            'margin_rate': 75,
            'conversion_rate': 15
        }
        
        score = calculator.calculate_store_score(metrics)
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_calculate_store_score_with_custom_weights(self):
        """测试自定义权重评分"""
        calculator = FeatureCalculator()
        
        metrics = {
            'actual_income': 50000,
            'valid_order_count': 500,
            'margin_rate': 75,
            'conversion_rate': 15
        }
        
        weights = {
            'revenue': 0.5,
            'orders': 0.2,
            'margin_rate': 0.2,
            'conversion': 0.1
        }
        
        score = calculator.calculate_store_score(metrics, weights)
        
        assert 0 <= score <= 100
    
    def test_calculate_store_scores_batch(self, sample_df):
        """测试批量评分计算"""
        calculator = FeatureCalculator()
        result = calculator.calculate_store_scores_batch(sample_df)
        
        assert not result.empty
        assert 'score' in result.columns
        assert 'grade' in result.columns
        assert len(result) == len(sample_df)
    
    def test_calculate_store_scores_batch_ordering(self, sample_df):
        """测试批量评分排序"""
        calculator = FeatureCalculator()
        result = calculator.calculate_store_scores_batch(sample_df)
        
        # 应该按分数降序排列
        scores = result['score'].tolist()
        assert scores == sorted(scores, reverse=True)
    
    def test_score_to_grade(self):
        """测试分数转评级"""
        calculator = FeatureCalculator()
        
        assert calculator._score_to_grade(95) == 'A+'
        assert calculator._score_to_grade(85) == 'A'
        assert calculator._score_to_grade(75) == 'B+'
        assert calculator._score_to_grade(65) == 'B'
        assert calculator._score_to_grade(55) == 'C'
        assert calculator._score_to_grade(45) == 'D'
        assert calculator._score_to_grade(35) == 'E'
    
    def test_calculate_performance_tier(self, sample_df):
        """测试表现分层"""
        calculator = FeatureCalculator()
        result = calculator.calculate_performance_tier(sample_df, 'actual_income')
        
        assert 'tier' in result.columns
        # 检查分层是否为 A-E
        tiers = set(result['tier'].tolist())
        assert tiers.issubset({'A', 'B', 'C', 'D', 'E'})
    
    def test_calculate_comparison_metrics(self, sample_df):
        """测试对比指标计算"""
        calculator = FeatureCalculator()
        
        # 创建前后两期数据
        current_df = sample_df.copy()
        previous_df = sample_df.copy()
        previous_df['actual_income'] = previous_df['actual_income'] * 0.9  # 减少10%
        
        result = calculator.calculate_comparison_metrics(current_df, previous_df)
        
        assert not result.empty
        assert 'actual_income_change' in result.columns
        assert 'actual_income_growth' in result.columns
    
    def test_calculate_comparison_metrics_empty_previous(self, sample_df):
        """测试前一期数据为空的对比"""
        calculator = FeatureCalculator()
        
        result = calculator.calculate_comparison_metrics(sample_df, pd.DataFrame())
        
        assert not result.empty
        # 变化应该为0
        assert 'actual_income_change' in result.columns
    
    def test_calculate_wow_growth(self, time_series_df):
        """测试环比增长计算"""
        calculator = FeatureCalculator()
        result = calculator.calculate_wow_growth(time_series_df, 'actual_income')
        
        assert not result.empty
        assert 'wow_growth' in result.columns
    
    def test_safe_growth_rate(self):
        """测试安全增长率计算"""
        calculator = FeatureCalculator()
        
        # 正常情况
        rate = calculator._safe_growth_rate(110, 100)
        assert rate == 10.0
        
        # 基数为零
        rate = calculator._safe_growth_rate(100, 0)
        assert rate == 100.0
        
        # 都为零
        rate = calculator._safe_growth_rate(0, 0)
        assert rate == 0.0
    
    def test_calculate_features_convenience_function(self, sample_df):
        """测试便捷函数"""
        # 排名
        result = calculate_features(sample_df, 'ranking')
        assert 'rank' in result.columns
        
        # 漏斗
        result = calculate_features(sample_df, 'funnel')
        assert 'exposure_to_entry' in result
        
        # 评分
        result = calculate_features(sample_df, 'score')
        assert 'score' in result.columns
    
    def test_calculate_features_all(self, sample_df):
        """测试计算所有特征"""
        result = calculate_features(sample_df, 'all')
        
        assert 'ranking' in result
        assert 'funnel' in result
        assert 'scores' in result
    
    def test_calculate_features_invalid_type(self, sample_df):
        """测试无效特征类型"""
        with pytest.raises(ValueError):
            calculate_features(sample_df, 'invalid_type')


class TestDefaultScoreWeights:
    """默认评分权重测试"""
    
    def test_weights_sum(self):
        """测试权重总和"""
        total = sum(DEFAULT_SCORE_WEIGHTS.values())
        assert total == 1.0
    
    def test_weights_positive(self):
        """测试权重为正"""
        for key, value in DEFAULT_SCORE_WEIGHTS.items():
            assert value > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])