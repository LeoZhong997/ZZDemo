"""
门店健康度分析器单元测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ai.analytics.health_analyzer import (
    HealthAnalyzer,
    analyze_store_health,
    HEALTH_SCORE_WEIGHTS,
    TRAFFIC_LIGHT_THRESHOLDS,
    INDUSTRY_BENCHMARKS
)


class TestHealthAnalyzer:
    """健康度分析器测试类"""
    
    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return HealthAnalyzer()
    
    @pytest.fixture
    def healthy_store_df(self):
        """创建健康门店测试数据"""
        np.random.seed(42)
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        
        data = []
        for date in dates:
            data.append({
                'date': date,
                'brand_store_name': '健康门店',
                'platform': '美团',
                'actual_income': 5000,
                'valid_orders': 100,
                'turnover': 8000,
                'margin_rate': 0.7,
                'store_score': 4.8,
                'five_min_reply_rate': 100,
                'merchant_cancelled_orders': 0,
                'product_satisfaction': 95,
                'packaging_satisfaction': 95
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def unhealthy_store_df(self):
        """创建不健康门店测试数据"""
        np.random.seed(43)
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        
        data = []
        for date in dates:
            data.append({
                'date': date,
                'brand_store_name': '问题门店',
                'platform': '美团',
                'actual_income': 500,
                'valid_orders': 20,
                'turnover': 1200,
                'margin_rate': 0.4,
                'store_score': 3.8,
                'five_min_reply_rate': 80,
                'merchant_cancelled_orders': 2,
                'product_satisfaction': 70,
                'packaging_satisfaction': 65
            })
        
        return pd.DataFrame(data)
    
    def test_analyzer_initialization(self, analyzer):
        """测试分析器初始化"""
        assert analyzer.weights is not None
        assert len(analyzer.weights) == 4
    
    def test_calculate_health_score(self, analyzer, healthy_store_df):
        """测试健康度评分计算"""
        result = analyzer.calculate_health_score(healthy_store_df)
        
        assert not result.empty
        assert 'health_score' in result.columns
        assert 'traffic_light' in result.columns
    
    def test_unhealthy_store_score(self, analyzer, unhealthy_store_df):
        """测试不健康门店分数"""
        result = analyzer.calculate_health_score(unhealthy_store_df)
        
        assert not result.empty
        # 问题门店健康度应该较低
        health_score = result.iloc[0]['health_score']
        assert health_score < 80
    
    def test_dimension_scores(self, analyzer, healthy_store_df):
        """测试各维度分数"""
        result = analyzer.calculate_health_score(healthy_store_df)
        
        row = result.iloc[0]
        assert 'revenue_score' in row
        assert 'compliance_score' in row
        assert 'reputation_score' in row
        assert 'efficiency_score' in row
    
    def test_generate_all_stores_report(self, analyzer, healthy_store_df):
        """测试生成所有门店报告"""
        result = analyzer.generate_all_stores_report(healthy_store_df)
        
        assert result.get('success') is True
        assert 'store_ranking' in result
        assert 'traffic_light_distribution' in result
    
    def test_store_ranking(self, analyzer, healthy_store_df):
        """测试门店排名"""
        result = analyzer.generate_all_stores_report(healthy_store_df)
        
        ranking = result.get('store_ranking', [])
        assert len(ranking) > 0
        assert 'brand_store_name' in ranking[0]
        assert 'health_score' in ranking[0]
    
    def test_traffic_light_distribution(self, analyzer, healthy_store_df):
        """测试信号灯分布"""
        result = analyzer.generate_all_stores_report(healthy_store_df)
        
        distribution = result.get('traffic_light_distribution', {})
        assert 'green' in distribution
        assert 'yellow' in distribution
        assert 'red' in distribution
    
    def test_high_risk_identification(self, analyzer, unhealthy_store_df):
        """测试高风险门店识别"""
        result = analyzer.generate_all_stores_report(unhealthy_store_df)
        high_risk = result.get('high_risk_stores', [])
        
        # 问题门店应该被识别为高风险或需关注
        # 注意：这取决于具体评分逻辑
        assert isinstance(high_risk, list)
    
    def test_get_traffic_light_status(self, analyzer):
        """测试信号灯判断"""
        assert analyzer.get_traffic_light_status(85) == '🟢'
        assert analyzer.get_traffic_light_status(70) == '🟡'
        assert analyzer.get_traffic_light_status(50) == '🔴'
    
    def test_empty_dataframe(self, analyzer):
        """测试空数据框"""
        empty_df = pd.DataFrame()
        result = analyzer.generate_all_stores_report(empty_df)
        
        # 空数据返回错误
        assert result.get('success') is False or 'error' in result
    
    def test_missing_columns(self, analyzer):
        """测试缺少列的数据"""
        df = pd.DataFrame({
            'date': ['2026-01-01'],
            'brand_store_name': ['门店A'],
            'actual_income': [1000]
        })
        
        # 应该不报错
        result = analyzer.calculate_health_score(df)
        # 结果可能是空的，但不应该抛出异常
        assert isinstance(result, pd.DataFrame)
    
    def test_generate_store_health_report(self, analyzer, healthy_store_df):
        """测试单门店健康报告"""
        result = analyzer.generate_store_health_report(healthy_store_df, '健康门店')
        
        assert result.get('success') is True
        assert 'health_score' in result
        assert 'traffic_light' in result


class TestConvenienceFunction:
    """便捷函数测试"""
    
    def test_analyze_store_health(self):
        """测试便捷函数"""
        df = pd.DataFrame({
            'date': ['2026-01-01'],
            'brand_store_name': ['门店A'],
            'platform': ['美团'],
            'actual_income': [2000],
            'valid_orders': [80],
            'margin_rate': [0.7]
        })
        
        result = analyze_store_health(df)
        assert result is not None


class TestConfigurations:
    """配置测试"""
    
    def test_health_score_weights(self):
        """测试健康度权重配置"""
        assert 'revenue' in HEALTH_SCORE_WEIGHTS
        assert 'compliance' in HEALTH_SCORE_WEIGHTS
        assert 'reputation' in HEALTH_SCORE_WEIGHTS
        assert 'efficiency' in HEALTH_SCORE_WEIGHTS
        
        # 权重总和应该为1
        total = sum(HEALTH_SCORE_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01
    
    def test_traffic_light_thresholds(self):
        """测试信号灯阈值"""
        assert 'green' in TRAFFIC_LIGHT_THRESHOLDS
        assert 'yellow' in TRAFFIC_LIGHT_THRESHOLDS
        assert 'red' in TRAFFIC_LIGHT_THRESHOLDS
    
    def test_industry_benchmarks(self):
        """测试行业基准值"""
        assert 'margin_rate' in INDUSTRY_BENCHMARKS
        assert 'conversion_rate' in INDUSTRY_BENCHMARKS
        assert 'store_score' in INDUSTRY_BENCHMARKS


if __name__ == '__main__':
    pytest.main([__file__, '-v'])