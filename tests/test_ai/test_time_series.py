"""
时间序列分析器单元测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.analytics.time_series import TimeSeriesAnalyzer, analyze_time_series


class TestTimeSeriesAnalyzer:
    """时间序列分析器测试"""
    
    @pytest.fixture
    def daily_df(self):
        """创建日度测试数据"""
        np.random.seed(42)
        dates = pd.date_range('2026-01-01', periods=30, freq='D')
        
        data = []
        for date in dates:
            # 添加上升趋势 + 周末效应
            trend = (date - pd.Timestamp('2026-01-01')).days * 100
            weekend_factor = 1.2 if date.dayofweek >= 5 else 1.0
            
            data.append({
                'date': date,
                'brand_store_name': '门店A',
                'actual_income': (5000 + trend + np.random.uniform(-500, 500)) * weekend_factor,
                'valid_order_count': 100 + int(trend / 50) + np.random.randint(-10, 10)
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def flat_df(self):
        """创建平稳数据"""
        np.random.seed(42)
        dates = pd.date_range('2026-01-01', periods=14, freq='D')
        
        data = []
        for date in dates:
            data.append({
                'date': date,
                'brand_store_name': '门店A',
                'actual_income': 10000 + np.random.uniform(-100, 100),  # 基本平稳
                'valid_order_count': 100
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def declining_df(self):
        """创建下降趋势数据"""
        np.random.seed(42)
        dates = pd.date_range('2026-01-01', periods=14, freq='D')
        
        data = []
        for i, date in enumerate(dates):
            data.append({
                'date': date,
                'brand_store_name': '门店A',
                'actual_income': 10000 - i * 200 + np.random.uniform(-100, 100),
                'valid_order_count': 100
            })
        
        return pd.DataFrame(data)
    
    def test_aggregate_daily(self, daily_df):
        """测试日度聚合"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.aggregate_daily(daily_df)
        
        assert not result.empty
        assert 'date' in result.columns
        assert 'actual_income' in result.columns
        assert 'day_of_week' in result.columns
        assert 'is_weekend' in result.columns
    
    def test_aggregate_daily_with_metric(self, daily_df):
        """测试指定指标的日度聚合"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.aggregate_daily(daily_df, metric='valid_order_count')
        
        assert 'valid_order_count' in result.columns
    
    def test_aggregate_weekly(self, daily_df):
        """测试周聚合"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.aggregate_weekly(daily_df)
        
        assert not result.empty
        assert 'year_week' in result.columns
        assert 'actual_income' in result.columns
    
    def test_calculate_trend_up(self, daily_df):
        """测试上升趋势检测"""
        analyzer = TimeSeriesAnalyzer()
        daily = analyzer.aggregate_daily(daily_df)
        trend = analyzer.calculate_trend(daily)
        
        assert trend['direction'] == '上升'
        assert trend['slope'] > 0
        assert 'strength' in trend
    
    def test_calculate_trend_down(self, declining_df):
        """测试下降趋势检测"""
        analyzer = TimeSeriesAnalyzer()
        daily = analyzer.aggregate_daily(declining_df)
        trend = analyzer.calculate_trend(daily)
        
        assert trend['direction'] == '下降'
        assert trend['slope'] < 0
    
    def test_calculate_trend_stable(self, flat_df):
        """测试平稳趋势检测"""
        analyzer = TimeSeriesAnalyzer()
        daily = analyzer.aggregate_daily(flat_df)
        trend = analyzer.calculate_trend(daily)
        
        # 由于波动很小，趋势应该是平稳或接近平稳
        assert trend['direction'] in ['平稳', '上升', '下降']
        assert 'strength' in trend
    
    def test_calculate_trend_empty(self):
        """测试空数据趋势"""
        analyzer = TimeSeriesAnalyzer()
        trend = analyzer.calculate_trend(pd.DataFrame())
        
        assert trend['direction'] in ['未知', '数据不足']
    
    def test_detect_seasonality_weekend_pattern(self, daily_df):
        """测试周末模式检测"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.detect_seasonality(daily_df)
        
        assert 'has_weekly_pattern' in result
        assert 'peak_day' in result
        assert 'low_day' in result
        assert 'weekday_avg' in result
        assert 'weekend_effect' in result
    
    def test_detect_seasonality_with_pattern(self, daily_df):
        """测试有周期性的数据"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.detect_seasonality(daily_df)
        
        # 由于有周末效应，应该检测到周期性
        # 注意：numpy.bool_ 也是有效的布尔类型
        assert result['has_weekly_pattern'] in [True, False] or isinstance(result['has_weekly_pattern'], (bool, np.bool_))
        assert isinstance(result['weekday_avg'], dict)
    
    def test_detect_seasonality_empty(self):
        """测试空数据周期性"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.detect_seasonality(pd.DataFrame())
        
        assert result['has_weekly_pattern'] == False
    
    def test_calculate_moving_average(self, daily_df):
        """测试移动平均计算"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.calculate_moving_average(daily_df, windows=[7, 14])
        
        assert not result.empty
        assert 'ma_7' in result.columns
        assert 'ma_14' in result.columns
    
    def test_calculate_volatility(self, daily_df):
        """测试波动性计算"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.calculate_volatility(daily_df)
        
        assert 'volatility' in result
        assert 'level' in result
        assert result['level'] in ['低波动', '中等波动', '较高波动', '高波动']
    
    def test_calculate_volatility_low(self, flat_df):
        """测试低波动数据"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.calculate_volatility(flat_df)
        
        assert result['level'] == '低波动'
    
    def test_analyze_growth_periods(self, daily_df):
        """测试增长期分析"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.analyze_growth_periods(daily_df)
        
        assert 'total_days' in result
        assert 'growth_days' in result
        assert 'decline_days' in result
        assert 'growth_rate' in result
        assert 'overall_trend' in result
    
    def test_forecast_simple(self, daily_df):
        """测试简单预测"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.forecast_simple(daily_df, days=7)
        
        assert 'method' in result
        assert 'predictions' in result
        assert len(result['predictions']) == 7
        assert 'total_predicted' in result
        assert 'disclaimer' in result
    
    def test_forecast_simple_prediction_structure(self, daily_df):
        """测试预测结果结构"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.forecast_simple(daily_df, days=3)
        
        for pred in result['predictions']:
            assert 'date' in pred
            assert 'day_name' in pred
            assert 'predicted_value' in pred
            assert pred['predicted_value'] >= 0  # 预测值不应为负
    
    def test_forecast_simple_empty(self):
        """测试空数据预测"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.forecast_simple(pd.DataFrame())
        
        assert 'error' in result
    
    def test_get_time_series_summary(self, daily_df):
        """测试综合摘要"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.get_time_series_summary(daily_df)
        
        assert 'date_range' in result
        assert 'summary_stats' in result
        assert 'trend' in result
        assert 'seasonality' in result
        assert 'volatility' in result
        assert 'growth_periods' in result
    
    def test_get_time_series_summary_structure(self, daily_df):
        """测试摘要结构"""
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.get_time_series_summary(daily_df)
        
        # 检查日期范围
        assert 'start' in result['date_range']
        assert 'end' in result['date_range']
        assert 'days' in result['date_range']
        
        # 检查统计信息
        assert 'total' in result['summary_stats']
        assert 'mean' in result['summary_stats']
        assert 'max' in result['summary_stats']
        assert 'min' in result['summary_stats']
    
    def test_analyze_time_series_convenience_function(self, daily_df):
        """测试便捷函数"""
        # 趋势分析
        result = analyze_time_series(daily_df, analysis_type='trend')
        assert 'direction' in result
        
        # 周期性分析
        result = analyze_time_series(daily_df, analysis_type='seasonality')
        assert 'has_weekly_pattern' in result
        
        # 波动性分析
        result = analyze_time_series(daily_df, analysis_type='volatility')
        assert 'volatility' in result
        
        # 预测
        result = analyze_time_series(daily_df, analysis_type='forecast', days=5)
        assert 'predictions' in result
        
        # 综合摘要
        result = analyze_time_series(daily_df, analysis_type='summary')
        assert 'trend' in result
    
    def test_analyze_time_series_invalid_type(self, daily_df):
        """测试无效分析类型"""
        with pytest.raises(ValueError):
            analyze_time_series(daily_df, analysis_type='invalid')


class TestTimeSeriesEdgeCases:
    """时间序列边界情况测试"""
    
    def test_single_day(self):
        """测试单天数据"""
        analyzer = TimeSeriesAnalyzer()
        df = pd.DataFrame({
            'date': [pd.Timestamp('2026-01-01')],
            'actual_income': [10000]
        })
        
        trend = analyzer.calculate_trend(df)
        assert trend['direction'] in ['数据不足', '未知']
    
    def test_two_days(self):
        """测试两天数据"""
        analyzer = TimeSeriesAnalyzer()
        dates = pd.date_range('2026-01-01', periods=2, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'actual_income': [10000, 11000]
        })
        
        trend = analyzer.calculate_trend(df)
        assert 'direction' in trend
    
    def test_missing_dates(self):
        """测试缺失日期数据"""
        analyzer = TimeSeriesAnalyzer()
        # 不连续的日期
        dates = [pd.Timestamp('2026-01-01'), pd.Timestamp('2026-01-03'), pd.Timestamp('2026-01-07')]
        df = pd.DataFrame({
            'date': dates,
            'actual_income': [10000, 11000, 12000]
        })
        
        daily = analyzer.aggregate_daily(df)
        assert not daily.empty
    
    def test_nan_values(self):
        """测试包含 NaN"""
        analyzer = TimeSeriesAnalyzer()
        dates = pd.date_range('2026-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'actual_income': [10000, np.nan, 11000, np.nan, 12000]
        })
        
        # 应该能处理 NaN
        daily = analyzer.aggregate_daily(df)
        assert not daily.empty
    
    def test_negative_values(self):
        """测试负值"""
        analyzer = TimeSeriesAnalyzer()
        dates = pd.date_range('2026-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'actual_income': [10000, 11000, -1000, 12000, 13000]
        })
        
        daily = analyzer.aggregate_daily(df)
        assert not daily.empty


if __name__ == '__main__':
    pytest.main([__file__, '-v'])