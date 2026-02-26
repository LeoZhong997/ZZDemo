"""
深度诊断引擎单元测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ai.engines.deep_diagnosis_engine import (
    DeepDiagnosisEngine,
    generate_deep_diagnosis
)


class TestDeepDiagnosisEngine:
    """深度诊断引擎测试类"""
    
    @pytest.fixture
    def engine(self):
        """创建引擎实例（无LLM）"""
        return DeepDiagnosisEngine(llm_adapter=None)
    
    @pytest.fixture
    def engine_with_mock_llm(self):
        """创建带Mock LLM的引擎"""
        mock_adapter = Mock()
        mock_adapter.chat.return_value = "这是一份深度诊断报告的模拟输出。"
        return DeepDiagnosisEngine(llm_adapter=mock_adapter)
    
    @pytest.fixture
    def sample_df(self):
        """创建测试数据"""
        np.random.seed(42)
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        
        data = []
        for date in dates:
            for store in ['门店A', '门店B']:
                for platform in ['美团', '饿了么']:
                    data.append({
                        'date': date,
                        'brand_store_name': store,
                        'platform': platform,
                        'actual_income': np.random.uniform(1500, 3000),
                        'valid_orders': int(np.random.uniform(50, 100)),
                        'turnover': np.random.uniform(2500, 5000),
                        'margin_rate': np.random.uniform(0.5, 0.75),
                        'store_score': np.random.uniform(4.0, 4.9),
                        'five_min_reply_rate': np.random.uniform(85, 100),
                        'exposure_count': int(np.random.uniform(3000, 6000)),
                        'entry_count': int(np.random.uniform(400, 800)),
                        'complaint_rate': np.random.uniform(0, 0.05),
                        'refund_rate': np.random.uniform(0.01, 0.05),
                        'bad_review_rate': np.random.uniform(0.01, 0.03)
                    })
        
        return pd.DataFrame(data)
    
    def test_engine_initialization_with_llm(self, engine_with_mock_llm):
        """测试带LLM的引擎初始化"""
        assert engine_with_mock_llm.llm_adapter is not None
        assert engine_with_mock_llm.redline_detector is not None
        assert engine_with_mock_llm.health_analyzer is not None
    
    def test_engine_initialization_without_llm(self, engine):
        """测试不带LLM的引擎初始化"""
        assert engine.llm_adapter is None
        assert engine.redline_detector is not None
        assert engine.health_analyzer is not None
    
    def test_generate_deep_diagnosis_basic(self, engine, sample_df):
        """测试基本深度诊断生成"""
        result = engine.generate_deep_diagnosis(
            df=sample_df,
            period="2026-01-01 至 2026-01-07",
            use_llm=False
        )
        
        assert result.get('success') is True
        assert 'health_data' in result
        assert 'breakpoint_data' in result
        assert 'recommendations' in result
    
    def test_diagnosis_with_events(self, engine, sample_df):
        """测试带事件的诊断"""
        events = [
            {'date': '2026-01-03', 'description': '促销活动', 'event_type': 'promotion'}
        ]
        
        result = engine.generate_deep_diagnosis(
            df=sample_df,
            period="测试周期",
            events=events,
            use_llm=False
        )
        
        assert result.get('success') is True
        assert 'events' in result
    
    def test_diagnosis_without_llm(self, engine, sample_df):
        """测试不使用LLM的诊断"""
        result = engine.generate_deep_diagnosis(
            df=sample_df,
            period="测试周期",
            use_llm=False
        )
        
        assert result.get('success') is True
        assert result.get('llm_analysis') is None
    
    def test_diagnosis_with_llm(self, engine_with_mock_llm, sample_df):
        """测试使用LLM的诊断"""
        result = engine_with_mock_llm.generate_deep_diagnosis(
            df=sample_df,
            period="测试周期",
            use_llm=True
        )
        
        assert result.get('success') is True
        assert result.get('llm_analysis') is not None
    
    def test_empty_dataframe(self, engine):
        """测试空数据"""
        empty_df = pd.DataFrame()
        result = engine.generate_deep_diagnosis(empty_df, period="测试")
        
        assert result.get('success') is False
        assert 'error' in result
    
    def test_generate_store_diagnosis_table(self, engine, sample_df):
        """测试门店诊断表生成"""
        table = engine.generate_store_diagnosis_table(sample_df)
        
        assert isinstance(table, list)
        if len(table) > 0:
            assert 'store_name' in table[0]
            assert 'health_score' in table[0]
            assert 'traffic_light' in table[0]
    
    def test_analyze_common_risks(self, engine, sample_df):
        """测试共性风险分析"""
        result = engine.analyze_common_risks(sample_df)
        
        assert result.get('success') is True
        assert 'common_risks' in result
    
    def test_generate_action_plan(self, engine, sample_df):
        """测试行动清单生成"""
        actions = engine.generate_action_plan(sample_df)
        
        assert isinstance(actions, list)
        if len(actions) > 0:
            assert 'priority' in actions[0]
            assert 'action' in actions[0]
    
    def test_generate_prioritized_suggestions(self, engine, sample_df):
        """测试优先建议生成"""
        result = engine.generate_deep_diagnosis(
            df=sample_df,
            period="测试周期",
            use_llm=False
        )
        
        recommendations = result.get('recommendations', [])
        assert isinstance(recommendations, list)


class TestConvenienceFunction:
    """便捷函数测试"""
    
    def test_generate_deep_diagnosis_function(self):
        """测试便捷函数"""
        df = pd.DataFrame({
            'date': ['2026-01-01', '2026-01-02'],
            'brand_store_name': ['门店A', '门店A'],
            'platform': ['美团', '美团'],
            'actual_income': [2000, 2200],
            'valid_orders': [80, 90],
            'margin_rate': [0.7, 0.72]
        })
        
        result = generate_deep_diagnosis(
            df=df,
            period="测试",
            use_llm=False
        )
        
        assert result is not None
        assert result.get('success') is True


class TestDiagnosisComponents:
    """诊断组件测试"""
    
    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        return DeepDiagnosisEngine(llm_adapter=None)
    
    @pytest.fixture
    def sample_df(self):
        """创建测试数据"""
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        data = []
        for date in dates:
            data.append({
                'date': date,
                'brand_store_name': '门店A',
                'platform': '美团',
                'actual_income': 2600,
                'valid_orders': 80,
                'turnover': 4000,
                'margin_rate': 0.65,
                'store_score': 4.5,
                'five_min_reply_rate': 95,
                'exposure_count': 500,
                'entry_count': 100,
                'complaint_rate': 0.02,
                'refund_rate': 0.03,
                'bad_review_rate': 0.015
            })
        return pd.DataFrame(data)
    
    def test_summary_stats_generation(self, engine, sample_df):
        """测试摘要统计生成"""
        result = engine.generate_deep_diagnosis(
            df=sample_df,
            period="测试",
            use_llm=False
        )
        
        summary_stats = result.get('summary_stats', {})
        assert 'date_range' in summary_stats or 'stores' in summary_stats
    
    def test_health_analysis_in_diagnosis(self, engine, sample_df):
        """测试诊断中的健康度分析"""
        result = engine.generate_deep_diagnosis(
            df=sample_df,
            period="测试",
            use_llm=False
        )
        
        health_data = result.get('health_data', {})
        assert health_data is not None
    
    def test_breakpoint_analysis_in_diagnosis(self, engine, sample_df):
        """测试诊断中的断点分析"""
        result = engine.generate_deep_diagnosis(
            df=sample_df,
            period="测试",
            use_llm=False
        )
        
        breakpoint_data = result.get('breakpoint_data', {})
        assert 'by_store' in breakpoint_data or 'summary' in breakpoint_data


class TestErrorHandling:
    """错误处理测试"""
    
    def test_empty_data_handling(self):
        """测试空数据处理"""
        engine = DeepDiagnosisEngine(llm_adapter=None)
        empty_df = pd.DataFrame()
        
        result = engine.generate_deep_diagnosis(empty_df, period="测试")
        
        assert result.get('success') is False
        assert 'error' in result
    
    def test_missing_columns_handling(self):
        """测试缺少列的处理"""
        engine = DeepDiagnosisEngine(llm_adapter=None)
        df = pd.DataFrame({
            'date': ['2026-01-01'],
            'brand_store_name': ['门店A']
        })
        
        # 应该能处理缺少列的情况
        result = engine.generate_deep_diagnosis(df, period="测试", use_llm=False)
        
        # 不应该抛出异常
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])