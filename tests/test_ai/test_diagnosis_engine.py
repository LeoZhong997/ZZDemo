"""
智能诊断引擎单元测试
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from ai.engines.diagnosis_engine import DiagnosisEngine, generate_diagnosis, quick_diagnosis


class TestDiagnosisEngine:
    """DiagnosisEngine 测试类"""
    
    def setup_method(self):
        """每个测试方法前的初始化"""
        # 创建 Mock LLM Adapter
        self.mock_llm = Mock()
        self.mock_llm.chat.return_value = "这是 AI 生成的诊断报告"
        
        # 创建测试数据
        self.test_df = pd.DataFrame({
            'date': pd.date_range('2026-02-18', periods=7),
            'brand_store_name': ['门店A', '门店A', '门店B', '门店B', '门店C', '门店C', '门店A'],
            'platform': ['美团', '饿了么', '美团', '饿了么', '美团', '饿了么', '美团'],
            'actual_income': [1000, 800, 1200, 900, 500, 400, 1100],
            'valid_orders': [50, 40, 60, 45, 25, 20, 55],
            'turnover': [1200, 1000, 1500, 1100, 600, 500, 1300],
            'exposure_count': [1000, 800, 1200, 900, 500, 400, 1100],
            'entry_count': [200, 160, 240, 180, 100, 80, 220],
            'margin_rate': [83.3, 80.0, 80.0, 81.8, 83.3, 80.0, 84.6]
        })
        
        # 使用 Mock LLM 创建引擎
        self.engine = DiagnosisEngine(llm_adapter=self.mock_llm)
    
    def test_init(self):
        """测试初始化"""
        assert self.engine is not None
        assert self.engine.llm_adapter is not None
        assert self.engine.data_aggregator is not None
        assert self.engine.anomaly_detector is not None
    
    def test_init_without_llm_adapter(self):
        """测试不传入 LLM 适配器的初始化"""
        with patch('ai.engines.diagnosis_engine.get_llm_adapter') as mock_get_adapter:
            mock_get_adapter.return_value = self.mock_llm
            engine = DiagnosisEngine()
            assert engine is not None
    
    def test_generate_full_diagnosis_empty_data(self):
        """测试空数据生成诊断"""
        empty_df = pd.DataFrame()
        result = self.engine.generate_full_diagnosis(empty_df)
        
        assert result['success'] is False
        assert 'store_ranking' in result
        assert len(result['store_ranking']) == 0
    
    def test_generate_full_diagnosis_basic(self):
        """测试基础诊断生成"""
        result = self.engine.generate_full_diagnosis(self.test_df, period="测试周期")
        
        assert result['success'] is True
        assert 'store_ranking' in result
        assert 'platform_comparison' in result
        assert 'anomalies' in result
        assert 'ai_summary' in result
        assert result['period'] == "测试周期"
        
        # 验证 LLM 被调用
        self.mock_llm.chat.assert_called_once()
    
    def test_generate_full_diagnosis_with_top_n(self):
        """测试带 top_n 参数的诊断生成"""
        result = self.engine.generate_full_diagnosis(self.test_df, top_n=2)
        
        assert result['success'] is True
    
    def test_compare_stores(self):
        """测试门店对比"""
        result = self.engine.compare_stores(
            self.test_df, 
            store_names=['门店A', '门店B']
        )
        
        assert result['success'] is True
        assert 'data' in result
        assert 'analysis' in result
    
    def test_compare_stores_empty_list(self):
        """测试空门店列表对比"""
        result = self.engine.compare_stores(self.test_df, store_names=[])
        
        assert 'data' in result
        assert len(result['data']) == 0
    
    def test_compare_stores_not_found(self):
        """测试门店未找到"""
        result = self.engine.compare_stores(
            self.test_df, 
            store_names=['不存在的门店']
        )
        
        assert 'data' in result
        assert len(result['data']) == 0
    
    def test_compare_platforms(self):
        """测试平台对比"""
        result = self.engine.compare_platforms(self.test_df)
        
        assert result['success'] is True
        assert 'data' in result
        assert 'analysis' in result
    
    def test_compare_platforms_empty_data(self):
        """测试空数据平台对比"""
        empty_df = pd.DataFrame()
        result = self.engine.compare_platforms(empty_df)
        
        assert 'data' in result
        assert len(result['data']) == 0
    
    def test_quick_diagnosis(self):
        """测试快速诊断"""
        result = self.engine.quick_diagnosis(self.test_df)
        
        assert result['success'] is True
        assert 'summary' in result
        assert 'stats' in result
    
    def test_quick_diagnosis_empty_data(self):
        """测试空数据快速诊断"""
        empty_df = pd.DataFrame()
        result = self.engine.quick_diagnosis(empty_df)
        
        assert result['success'] is False
    
    def test_detect_anomalies(self):
        """测试异常检测"""
        result = self.engine.detect_anomalies(self.test_df)
        
        assert 'anomalies' in result
        assert 'count' in result
    
    def test_detect_anomalies_empty_data(self):
        """测试空数据异常检测"""
        empty_df = pd.DataFrame()
        result = self.engine.detect_anomalies(empty_df)
        
        assert result['anomalies'] == []
        assert result['count'] == 0
    
    def test_get_store_performance(self):
        """测试获取门店表现"""
        result = self.engine.get_store_performance(self.test_df, '门店A')
        
        assert result['success'] is True
        assert result['store_name'] == '门店A'
        assert 'metrics' in result
        assert 'daily_data' in result
    
    def test_get_store_performance_not_found(self):
        """测试获取不存在门店的表现"""
        result = self.engine.get_store_performance(self.test_df, '不存在的门店')
        
        assert result['success'] is False
    
    def test_llm_error_handling(self):
        """测试 LLM 调用错误处理"""
        self.mock_llm.chat.side_effect = Exception("API 调用失败")
        
        result = self.engine.generate_full_diagnosis(self.test_df)
        
        # 应该仍然返回结果，但 ai_summary 包含错误信息
        assert 'ai_summary' in result
        assert '不可用' in result['ai_summary'] or '失败' in result['ai_summary']
    
    def test_elapsed_time_recorded(self):
        """测试耗时记录"""
        result = self.engine.generate_full_diagnosis(self.test_df)
        
        assert 'elapsed_time' in result
        assert result['elapsed_time'] >= 0


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def setup_method(self):
        """每个测试方法前的初始化"""
        self.test_df = pd.DataFrame({
            'date': pd.date_range('2026-02-18', periods=3),
            'brand_store_name': ['门店A', '门店B', '门店C'],
            'platform': ['美团', '饿了么', '美团'],
            'actual_income': [1000, 1200, 500],
            'valid_orders': [50, 60, 25],
            'turnover': [1200, 1500, 600],
            'exposure_count': [1000, 1200, 500],
            'entry_count': [200, 240, 100],
            'margin_rate': [83.3, 80.0, 83.3]
        })
    
    @patch('ai.engines.diagnosis_engine.get_llm_adapter')
    def test_generate_diagnosis(self, mock_get_adapter):
        """测试 generate_diagnosis 便捷函数"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "诊断报告"
        mock_get_adapter.return_value = mock_llm
        
        result = generate_diagnosis(self.test_df)
        
        assert 'store_ranking' in result
        assert 'ai_summary' in result
    
    @patch('ai.engines.diagnosis_engine.get_llm_adapter')
    def test_quick_diagnosis_func(self, mock_get_adapter):
        """测试 quick_diagnosis 便捷函数"""
        mock_llm = Mock()
        mock_llm.chat.return_value = "快速诊断摘要"
        mock_get_adapter.return_value = mock_llm
        
        result = quick_diagnosis(self.test_df)
        
        assert isinstance(result, str)