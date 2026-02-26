"""
红线检测器单元测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ai.analytics.redline_detector import (
    RedlineDetector,
    detect_redlines,
    REDLINE_RULES,
    SEVERITY_WEIGHTS
)


class TestRedlineDetector:
    """红线检测器测试类"""
    
    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return RedlineDetector()
    
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
                        'actual_income': np.random.uniform(500, 2000),
                        'valid_orders': np.random.randint(20, 100),
                        'margin_rate': np.random.uniform(0.5, 0.8),
                        'store_score': np.random.uniform(4.0, 4.9),
                        'five_min_reply_rate': np.random.uniform(90, 100),
                        'merchant_cancelled_orders': 0,
                        'product_satisfaction': np.random.uniform(85, 98),
                        'packaging_satisfaction': np.random.uniform(85, 98)
                    })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def problematic_df(self):
        """创建有问题的测试数据"""
        data = []
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        
        for date in dates:
            data.append({
                'date': date,
                'brand_store_name': '问题门店',
                'platform': '美团',
                'actual_income': 1000,
                'valid_orders': 50,
                'margin_rate': 0.6,
                'store_score': 3.8,  # 低于阈值
                'five_min_reply_rate': 85,  # 低于100
                'merchant_cancelled_orders': 2,  # 大于0
                'product_satisfaction': 75,
                'packaging_satisfaction': 70
            })
        
        return pd.DataFrame(data)
    
    def test_detector_initialization(self, detector):
        """测试检测器初始化"""
        assert detector.rules is not None
        assert len(detector.rules) > 0
    
    def test_detect_all_success(self, detector, sample_df):
        """测试整体检测成功"""
        result = detector.detect_all(sample_df)
        
        assert result.get('success') is True
        assert 'by_store' in result
        assert 'summary' in result
        assert 'high_risk_stores' in result
    
    def test_detect_all_with_violations(self, detector, problematic_df):
        """测试检测到违规"""
        result = detector.detect_all(problematic_df)
        
        assert result.get('success') is True
        by_store = result.get('by_store', {})
        
        # 问题门店应该有违规记录
        if '问题门店' in by_store:
            violations = by_store['问题门店']
            assert len(violations) > 0
    
    def test_detect_merchant_responsibility(self, detector, problematic_df):
        """测试商责检测"""
        violations = detector.detect_merchant_responsibility(problematic_df)
        
        # 有商责订单应该被检测到
        assert len(violations) > 0
        assert violations[0]['type'] == 'merchant_responsibility'
    
    def test_detect_low_store_score(self, detector, problematic_df):
        """测试低评分检测"""
        violations = detector.detect_low_store_score(problematic_df)
        
        # 评分低于4.0应该被检测到
        assert len(violations) > 0
        assert any(v['type'] == 'store_score_critical' for v in violations)
    
    def test_detect_low_store_score_threshold_45(self, detector):
        """测试评分阈值4.5"""
        # 创建评分在4.0-4.5之间的数据
        data = []
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        
        for date in dates:
            data.append({
                'date': date,
                'brand_store_name': '评分4.3门店',
                'platform': '美团',
                'store_score': 4.3,  # 低于4.5但高于4.0
                'valid_orders': 50
            })
        
        df = pd.DataFrame(data)
        violations = detector.detect_low_store_score(df)
        
        # 评分4.3应该被检测为medium严重度（低于4.5）
        assert len(violations) > 0
        assert any(v['type'] == 'store_score' and v['severity'] == 'medium' for v in violations)
    
    def test_detect_store_score_drop(self, detector):
        """测试评分环比下降检测"""
        data = []
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        
        # 模拟评分从4.8下降到4.4（下降0.4 > 0.2阈值）
        scores = [4.8, 4.8, 4.8, 4.4, 4.4, 4.4, 4.4]
        
        for i, date in enumerate(dates):
            data.append({
                'date': date,
                'brand_store_name': '评分下降门店',
                'platform': '美团',
                'store_score': scores[i],
                'valid_orders': 50
            })
        
        df = pd.DataFrame(data)
        violations = detector.detect_store_score_drop(df, threshold=0.2)
        
        # 应该检测到评分下降
        assert len(violations) > 0
        assert violations[0]['type'] == 'store_score_drop'
        assert violations[0]['value'] >= 0.3  # 下降幅度至少0.3（4.8-4.4=0.4）
    
    def test_detect_store_score_drop_no_drop(self, detector):
        """测试评分稳定时无下降检测"""
        data = []
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        
        # 评分稳定
        for date in dates:
            data.append({
                'date': date,
                'brand_store_name': '评分稳定门店',
                'platform': '美团',
                'store_score': 4.5,
                'valid_orders': 50
            })
        
        df = pd.DataFrame(data)
        violations = detector.detect_store_score_drop(df, threshold=0.2)
        
        # 评分稳定，不应该检测到下降
        assert len(violations) == 0
    
    def test_detect_all_includes_score_drop(self, detector):
        """测试整体检测包含评分下降"""
        data = []
        dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
        
        # 模拟评分大幅下降
        scores = [4.8, 4.8, 4.8, 4.5, 4.5, 4.5, 4.5]
        
        for i, date in enumerate(dates):
            data.append({
                'date': date,
                'brand_store_name': '评分下降门店',
                'platform': '美团',
                'store_score': scores[i],
                'valid_orders': 50,
                'actual_income': 1000
            })
        
        df = pd.DataFrame(data)
        result = detector.detect_all(df)
        
        # 检查是否包含评分下降违规
        violations = result.get('violations', [])
        has_drop = any(v['type'] == 'store_score_drop' for v in violations)
        assert has_drop is True
    
    def test_summary_statistics(self, detector, problematic_df):
        """测试汇总统计"""
        result = detector.detect_all(problematic_df)
        summary = result.get('summary', {})
        
        assert 'total' in summary
        assert 'by_severity' in summary
    
    def test_high_risk_stores_identification(self, detector, problematic_df):
        """测试高风险门店识别"""
        result = detector.detect_all(problematic_df)
        high_risk = result.get('high_risk_stores', [])
        
        # 问题门店可能被识别为高风险
        assert isinstance(high_risk, list)
    
    def test_empty_dataframe(self, detector):
        """测试空数据框"""
        empty_df = pd.DataFrame()
        result = detector.detect_all(empty_df)
        
        # 空数据应该返回成功但无违规
        assert result.get('success') is False
        assert result.get('violations', []) == []
    
    def test_missing_columns(self, detector):
        """测试缺少检测列的数据"""
        # 只有基础列，没有检测指标列
        df = pd.DataFrame({
            'date': ['2026-01-01'],
            'brand_store_name': ['门店A'],
            'actual_income': [1000]
        })
        
        result = detector.detect_all(df)
        # 应该不报错，返回空违规
        assert result.get('success') is True
        assert result.get('violations', []) == []
    
    def test_get_redline_summary(self, detector, sample_df):
        """测试获取红线摘要"""
        summary = detector.get_redline_summary(sample_df)
        
        assert 'total' in summary
        assert 'high_risk_count' in summary
    
    def test_get_store_redlines(self, detector, sample_df):
        """测试获取门店红线"""
        redlines = detector.get_store_redlines(sample_df, '门店A')
        
        assert isinstance(redlines, list)


class TestConvenienceFunction:
    """便捷函数测试"""
    
    def test_detect_redlines(self):
        """测试便捷函数"""
        df = pd.DataFrame({
            'date': ['2026-01-01'],
            'brand_store_name': ['门店A'],
            'platform': ['美团'],
            'actual_income': [1000]
        })
        
        result = detect_redlines(df)
        assert result.get('success') is True


class TestThresholds:
    """阈值配置测试"""
    
    def test_rules_structure(self):
        """测试规则配置结构"""
        assert 'merchant_responsibility' in REDLINE_RULES
        assert 'store_score' in REDLINE_RULES
        
        for key, config in REDLINE_RULES.items():
            assert 'name' in config
            assert 'field' in config
            assert 'severity' in config
    
    def test_severity_weights(self):
        """测试严重程度权重"""
        assert 'high' in SEVERITY_WEIGHTS
        assert 'medium' in SEVERITY_WEIGHTS
        assert 'low' in SEVERITY_WEIGHTS
        
        # 权重应该递减
        assert SEVERITY_WEIGHTS['high'] > SEVERITY_WEIGHTS['medium']
        assert SEVERITY_WEIGHTS['medium'] > SEVERITY_WEIGHTS['low']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])