"""
预测分析引擎单元测试
测试 PredictionEngine 及相关功能
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from ai.engines.prediction_engine import (
    PredictionEngine,
    predict_revenue,
    analyze_trend,
    predict_by_store
)
from ai.prompts.prediction_prompts import (
    PREDICTION_SYSTEM_PROMPT,
    REVENUE_PREDICTION_TEMPLATE,
    TREND_ANALYSIS_TEMPLATE,
    HOLIDAY_EFFECT_TEMPLATE,
    STORE_PREDICTION_TEMPLATE,
    build_revenue_prediction_prompt,
    build_trend_analysis_prompt,
    build_holiday_effect_prompt,
    build_store_prediction_prompt,
    format_historical_summary,
    format_trend_data,
    format_predictions,
    format_seasonality,
    format_growth_analysis,
    format_store_predictions
)


# ========== 测试数据 ==========
@pytest.fixture
def sample_df():
    """创建测试用 DataFrame"""
    np.random.seed(42)
    dates = pd.date_range(start='2026-01-01', periods=14, freq='D')
    
    data = []
    for date in dates:
        for store in ['门店A', '门店B']:
            for platform in ['美团', '饿了么']:
                base_income = np.random.uniform(500, 1500)
                data.append({
                    'date': date,
                    'brand_store_name': store,
                    'platform': platform,
                    'actual_income': base_income,
                    'valid_orders': int(base_income / 25),
                    'platform_revenue': base_income * 1.2,
                    'margin_rate': 0.75,
                    'exposure_count': int(base_income * 10),
                    'entry_count': int(base_income * 2),
                    'conversion_rate': 0.15
                })
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_daily_data():
    """创建日度聚合测试数据"""
    np.random.seed(42)
    dates = pd.date_range(start='2026-01-01', periods=14, freq='D')
    
    data = []
    for i, date in enumerate(dates):
        # 创建上升趋势
        base = 1000 + i * 50 + np.random.uniform(-100, 100)
        data.append({
            'date': date,
            'actual_income': base,
            'valid_orders': int(base / 25),
            'exposure_count': int(base * 10),
            'entry_count': int(base * 2)
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def mock_llm_adapter():
    """创建 Mock LLM 适配器"""
    adapter = Mock()
    adapter.chat.return_value = "这是 AI 分析结果"
    adapter.stream_chat.return_value = iter(["这", "是", "分析"])
    adapter.test_connection.return_value = {'success': True, 'latency_ms': 100}
    return adapter


# ========== Prompt 模板测试 ==========
class TestPredictionPrompts:
    """测试预测 Prompt 模板"""
    
    def test_system_prompt_exists(self):
        """测试系统提示词存在"""
        assert PREDICTION_SYSTEM_PROMPT is not None
        assert len(PREDICTION_SYSTEM_PROMPT) > 100
        assert "预测" in PREDICTION_SYSTEM_PROMPT or "分析" in PREDICTION_SYSTEM_PROMPT
    
    def test_revenue_prediction_template_format(self):
        """测试营收预测模板格式化"""
        result = REVENUE_PREDICTION_TEMPLATE.format(
            period="2026-01-01 至 2026-01-14",
            historical_summary="- 总营收: ¥10,000",
            avg_daily_revenue=1000,
            std_revenue=200,
            max_revenue=1500,
            min_revenue=800,
            trend_direction="上升",
            trend_strength="0.75",
            prediction_days=7,
            prediction_method="线性趋势外推",
            trend_data="| 日期 | 值 |",
            model_predictions="| 日期 | 预测值 |"
        )
        assert "营收预测分析" in result
        assert "2026-01-01 至 2026-01-14" in result
    
    def test_format_historical_summary(self):
        """测试历史摘要格式化"""
        summary = {
            'date_range': {'start': '2026-01-01', 'end': '2026-01-14', 'days': 14},
            'revenue': {'total': 100000, 'daily_avg': 7142.86},
            'orders': {'total': 4000, 'daily_avg': 285.71}
        }
        result = format_historical_summary(summary)
        assert "日期范围" in result
        assert "总营收" in result
        assert "总订单" in result
    
    def test_format_trend_data(self):
        """测试趋势数据格式化"""
        data = [
            {'date': '2026-01-01', 'actual_income': 1000},
            {'date': '2026-01-02', 'actual_income': 1100},
            {'date': '2026-01-03', 'actual_income': 1050}
        ]
        result = format_trend_data(data)
        assert "| 日期 | 值 |" in result
        assert "2026-01-01" in result
    
    def test_format_predictions(self):
        """测试预测数据格式化"""
        predictions = [
            {'date': '2026-01-15', 'predicted_value': 1200, 
             'confidence_lower': 1000, 'confidence_upper': 1400},
            {'date': '2026-01-16', 'predicted_value': 1250,
             'confidence_lower': 1050, 'confidence_upper': 1450}
        ]
        result = format_predictions(predictions)
        assert "| 日期 | 预测值 |" in result
        assert "2026-01-15" in result
    
    def test_format_seasonality(self):
        """测试周期性数据格式化"""
        seasonality = {
            'has_weekly_pattern': True,
            'peak_day': '周六',
            'low_day': '周二',
            'weekend_effect_label': '正向',
            'weekday_avg': {'周一': 1000, '周二': 900, '周六': 1200}
        }
        result = format_seasonality(seasonality)
        assert "存在周期性" in result
        assert "高峰日" in result
        assert "周六" in result
    
    def test_format_growth_analysis(self):
        """测试增长分析格式化"""
        growth = {
            'total_days': 14,
            'growth_days': 8,
            'decline_days': 6,
            'growth_rate': 57.1,
            'max_growth_streak': 4,
            'max_decline_streak': 2,
            'overall_trend': '上升'
        }
        result = format_growth_analysis(growth)
        assert "增长天数" in result
        assert "下降天数" in result
        assert "上升" in result
    
    def test_build_revenue_prediction_prompt(self):
        """测试构建营收预测 Prompt"""
        historical_summary = {
            'date_range': {'start': '2026-01-01', 'end': '2026-01-14', 'days': 14},
            'revenue': {'total': 100000, 'daily_avg': 7142.86},
            'trend': {'direction': '上升', 'strength': 0.75}
        }
        trend_data = [
            {'date': '2026-01-01', 'actual_income': 1000},
            {'date': '2026-01-02', 'actual_income': 1100}
        ]
        model_predictions = [
            {'date': '2026-01-15', 'predicted_value': 1200}
        ]
        
        result = build_revenue_prediction_prompt(
            historical_summary=historical_summary,
            trend_data=trend_data,
            model_predictions=model_predictions,
            period="2026-01-01 至 2026-01-14",
            prediction_days=7
        )
        
        assert "营收预测分析" in result
        assert "预测天数: 7" in result
    
    def test_build_trend_analysis_prompt(self):
        """测试构建趋势分析 Prompt"""
        trend_data = [{'date': '2026-01-01', 'actual_income': 1000}]
        trend_stats = {'direction': '上升', 'strength': 0.75, 'daily_change': 50, 'r_squared': 0.85}
        seasonality = {'has_weekly_pattern': True, 'peak_day': '周六'}
        growth_analysis = {'overall_trend': '上升'}
        
        result = build_trend_analysis_prompt(
            period="2026-01-01 至 2026-01-14",
            metric='actual_income',
            trend_data=trend_data,
            trend_stats=trend_stats,
            seasonality=seasonality,
            growth_analysis=growth_analysis
        )
        
        assert "趋势分析" in result
        assert "实收" in result
    
    def test_build_holiday_effect_prompt(self):
        """测试构建节假日效应 Prompt"""
        holiday_data = [{'date': '2026-01-01', 'actual_income': 1500}]
        normal_data = [{'date': '2026-01-05', 'actual_income': 1000}]
        
        result = build_holiday_effect_prompt(
            period="2026-01-01 至 2026-01-14",
            holiday_info="春节: 2026-01-01",
            holiday_data=holiday_data,
            normal_data=normal_data,
            holiday_avg=1500,
            normal_avg=1000
        )
        
        assert "节假日效应分析" in result
        assert "春节" in result
    
    def test_build_store_prediction_prompt(self):
        """测试构建门店预测 Prompt"""
        store_predictions = [
            {'store_name': '门店A', 'predicted_total': 10000, 'trend': '上升', 'confidence': 0.85}
        ]
        
        result = build_store_prediction_prompt(
            period="2026-01-01 至 2026-01-14",
            prediction_days=7,
            store_predictions=store_predictions,
            total_predicted=10000,
            overall_trend="上升"
        )
        
        assert "门店预测对比" in result
        assert "门店A" in result


# ========== PredictionEngine 测试 ==========
class TestPredictionEngine:
    """测试预测分析引擎"""
    
    def test_init_with_default_adapter(self, mock_llm_adapter):
        """测试默认初始化"""
        with patch('ai.engines.prediction_engine.get_llm_adapter', return_value=mock_llm_adapter):
            engine = PredictionEngine()
            assert engine.llm_adapter is not None
    
    def test_init_with_custom_adapter(self, mock_llm_adapter):
        """测试使用自定义适配器初始化"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        assert engine.llm_adapter == mock_llm_adapter
    
    def test_predict_revenue_empty_data(self, mock_llm_adapter):
        """测试空数据预测"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.predict_revenue(pd.DataFrame())
        
        assert result['success'] is False
        assert "空" in result['analysis'] or "不足" in result['analysis']
    
    def test_predict_revenue_insufficient_data(self, mock_llm_adapter):
        """测试数据不足预测"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        # 只有2天数据
        df = pd.DataFrame({
            'date': pd.date_range(start='2026-01-01', periods=2),
            'actual_income': [1000, 1100],
            'brand_store_name': ['门店A', '门店A'],
            'platform': ['美团', '美团']
        })
        result = engine.predict_revenue(df)
        
        assert result['success'] is False
    
    def test_predict_revenue_success(self, sample_df, mock_llm_adapter):
        """测试成功预测"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.predict_revenue(sample_df, days=7)
        
        assert result['success'] is True
        assert 'predictions' in result
        assert len(result['predictions']) == 7
        assert result['trend'] in ['上升', '下降', '平稳']
        assert 'analysis' in result
    
    def test_predict_revenue_with_confidence(self, sample_df, mock_llm_adapter):
        """测试带置信区间的预测"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.predict_revenue(sample_df, days=7, include_confidence=True)
        
        assert result['success'] is True
        for pred in result['predictions']:
            assert 'confidence_lower' in pred
            assert 'confidence_upper' in pred
            assert pred['confidence_lower'] <= pred['predicted_value'] <= pred['confidence_upper']
    
    def test_analyze_trend_empty_data(self, mock_llm_adapter):
        """测试空数据趋势分析"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.analyze_trend(pd.DataFrame())
        
        assert result['success'] is False
    
    def test_analyze_trend_success(self, sample_df, mock_llm_adapter):
        """测试成功趋势分析"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.analyze_trend(sample_df, metric='actual_income')
        
        assert result['success'] is True
        assert 'trend' in result
        assert 'seasonality' in result
        assert 'analysis' in result
    
    def test_analyze_holiday_effect_no_dates(self, sample_df, mock_llm_adapter):
        """测试无节假日日期时的周末效应分析"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.analyze_holiday_effect(sample_df)
        
        # 应该返回周末效应分析
        assert result['success'] is True
        assert '周末' in result['holiday_impact'].get('holiday_name', '') or 'weekend' in str(result).lower()
    
    def test_analyze_holiday_effect_with_dates(self, sample_df, mock_llm_adapter):
        """测试带节假日日期的效应分析"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        holiday_dates = ['2026-01-01', '2026-01-02']
        result = engine.analyze_holiday_effect(
            sample_df,
            holiday_dates=holiday_dates,
            holiday_name="元旦"
        )
        
        assert result['success'] is True
        assert 'holiday_impact' in result
    
    def test_predict_by_store_empty_data(self, mock_llm_adapter):
        """测试空数据门店预测"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.predict_by_store(pd.DataFrame())
        
        assert result['success'] is False
    
    def test_predict_by_store_success(self, sample_df, mock_llm_adapter):
        """测试成功门店预测"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.predict_by_store(sample_df, days=7, top_n=10)
        
        assert result['success'] is True
        assert 'store_predictions' in result
        assert 'total_predicted' in result
        assert 'analysis' in result
    
    def test_predict_by_platform_success(self, sample_df, mock_llm_adapter):
        """测试成功平台预测"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.predict_by_platform(sample_df, days=7)
        
        assert result['success'] is True
        assert 'platform_predictions' in result
    
    def test_get_prediction_summary(self, sample_df, mock_llm_adapter):
        """测试获取预测综合摘要"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.get_prediction_summary(sample_df, days=7)
        
        assert result['success'] is True
        assert 'revenue_prediction' in result
        assert 'trend_analysis' in result
        assert 'store_predictions' in result
        assert 'platform_predictions' in result
    
    def test_empty_prediction_result(self, mock_llm_adapter):
        """测试空预测结果"""
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine._empty_prediction_result("测试错误")
        
        assert result['success'] is False
        assert result['predictions'] == []
        assert "测试错误" in result['analysis']


# ========== 便捷函数测试 ==========
class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_predict_revenue_function(self, sample_df, mock_llm_adapter):
        """测试 predict_revenue 便捷函数"""
        with patch('ai.engines.prediction_engine.get_llm_adapter', return_value=mock_llm_adapter):
            result = predict_revenue(sample_df, days=7)
            assert 'success' in result
    
    def test_analyze_trend_function(self, sample_df, mock_llm_adapter):
        """测试 analyze_trend 便捷函数"""
        with patch('ai.engines.prediction_engine.get_llm_adapter', return_value=mock_llm_adapter):
            result = analyze_trend(sample_df, metric='actual_income')
            assert 'success' in result
    
    def test_predict_by_store_function(self, sample_df, mock_llm_adapter):
        """测试 predict_by_store 便捷函数"""
        with patch('ai.engines.prediction_engine.get_llm_adapter', return_value=mock_llm_adapter):
            result = predict_by_store(sample_df, days=7, top_n=5)
            assert 'success' in result


# ========== 错误处理测试 ==========
class TestErrorHandling:
    """测试错误处理"""
    
    def test_llm_call_failure(self, sample_df):
        """测试 LLM 调用失败"""
        mock_adapter = Mock()
        mock_adapter.chat.side_effect = Exception("API Error")
        
        engine = PredictionEngine(llm_adapter=mock_adapter)
        result = engine.predict_revenue(sample_df)
        
        # 应该返回部分结果，但 AI 分析不可用
        assert "不可用" in result['analysis'] or "Error" in result['analysis']
    
    def test_data_aggregation_failure(self, mock_llm_adapter):
        """测试数据聚合失败"""
        # 创建无法聚合的数据
        df = pd.DataFrame({'invalid': [1, 2, 3]})
        
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        result = engine.predict_revenue(df)
        
        assert result['success'] is False


# ========== 性能测试 ==========
class TestPerformance:
    """测试性能"""
    
    def test_large_dataset_performance(self, mock_llm_adapter):
        """测试大数据集性能"""
        import time
        
        # 创建大数据集
        np.random.seed(42)
        dates = pd.date_range(start='2026-01-01', periods=30, freq='D')
        stores = [f'门店{i}' for i in range(20)]
        
        data = []
        for date in dates:
            for store in stores:
                for platform in ['美团', '饿了么']:
                    data.append({
                        'date': date,
                        'brand_store_name': store,
                        'platform': platform,
                        'actual_income': np.random.uniform(500, 1500),
                        'valid_orders': 50,
                        'platform_revenue': 1000,
                        'margin_rate': 0.75,
                        'exposure_count': 1000,
                        'entry_count': 200,
                        'conversion_rate': 0.15
                    })
        
        df = pd.DataFrame(data)
        
        engine = PredictionEngine(llm_adapter=mock_llm_adapter)
        
        start_time = time.time()
        result = engine.predict_revenue(df, days=7)
        elapsed_time = time.time() - start_time
        
        # 应该在合理时间内完成（< 5秒，排除 LLM 调用时间）
        assert elapsed_time < 5.0
        assert result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])