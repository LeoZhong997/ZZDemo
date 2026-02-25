"""
Prompt 构建器单元测试
"""
import pytest
from ai.core.prompt_builder import PromptBuilder, build_diagnosis_prompt, build_qa_prompt


class TestPromptBuilder:
    """PromptBuilder 测试类"""
    
    def setup_method(self):
        """每个测试方法前的初始化"""
        self.builder = PromptBuilder()
    
    def test_init(self):
        """测试初始化"""
        assert self.builder is not None
    
    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        system_prompt = self.builder.get_system_prompt()
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
    
    def test_build_diagnosis_prompt_basic(self):
        """测试构建诊断报告 Prompt - 基础"""
        store_ranking = [
            {"brand_store_name": "门店A", "actual_income": 10000, "valid_orders": 100}
        ]
        platform_comparison = [
            {"platform": "美团", "actual_income": 5000}
        ]
        anomalies = []
        
        prompt = self.builder.build_diagnosis_prompt(
            store_ranking=store_ranking,
            platform_comparison=platform_comparison,
            anomalies=anomalies,
            period="本周"
        )
        
        assert isinstance(prompt, str)
        assert "本周" in prompt
        assert "门店A" in prompt or "门店" in prompt
    
    def test_build_diagnosis_prompt_with_anomalies(self):
        """测试构建诊断报告 Prompt - 包含异常"""
        store_ranking = [
            {"brand_store_name": "门店A", "actual_income": 10000}
        ]
        platform_comparison = []
        anomalies = [
            {"store": "门店A", "metric": "实收", "deviation": -20, "severity": "高"}
        ]
        
        prompt = self.builder.build_diagnosis_prompt(
            store_ranking=store_ranking,
            platform_comparison=platform_comparison,
            anomalies=anomalies,
            period="本周"
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_build_qa_prompt(self):
        """测试构建问答 Prompt"""
        question = "这周销售额怎么样？"
        relevant_data = {
            "total_revenue": 100000,
            "total_orders": 1000,
            "date_range": "2026-02-18 至 2026-02-25"
        }
        
        prompt = self.builder.build_qa_prompt(question, relevant_data)
        
        assert isinstance(prompt, str)
        assert "这周销售额怎么样" in prompt
        assert "100000" in prompt or "销售额" in prompt.lower() or "revenue" in prompt.lower()
    
    def test_build_store_comparison_prompt(self):
        """测试构建门店对比 Prompt"""
        comparison_data = [
            {"brand_store_name": "门店A", "actual_income": 10000},
            {"brand_store_name": "门店B", "actual_income": 8000}
        ]
        store_names = ["门店A", "门店B"]
        
        prompt = self.builder.build_store_comparison_prompt(comparison_data, store_names)
        
        assert isinstance(prompt, str)
        assert "门店A" in prompt
        assert "门店B" in prompt
    
    def test_build_suggestion_prompt(self):
        """测试构建建议 Prompt"""
        store_metrics = [
            {"brand_store_name": "门店A", "actual_income": 10000}
        ]
        platform_metrics = [
            {"platform": "美团", "actual_income": 5000}
        ]
        issues = [
            {"issue": "转化率偏低", "impact": "订单减少"}
        ]
        
        prompt = self.builder.build_suggestion_prompt(
            store_metrics=store_metrics,
            platform_metrics=platform_metrics,
            issues=issues,
            focus_area="all"
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestBuildDiagnosisPrompt:
    """build_diagnosis_prompt 便捷函数测试"""
    
    def test_basic(self):
        """基础测试"""
        store_ranking = [
            {"brand_store_name": "测试门店", "actual_income": 5000}
        ]
        
        prompt = build_diagnosis_prompt(
            store_ranking=store_ranking,
            platform_comparison=[],
            anomalies=[],
            period="测试周期"
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_empty_inputs(self):
        """空输入测试"""
        prompt = build_diagnosis_prompt(
            store_ranking=[],
            platform_comparison=[],
            anomalies=[],
            period="空数据测试"
        )
        
        assert isinstance(prompt, str)


class TestBuildQAPrompt:
    """build_qa_prompt 便捷函数测试"""
    
    def test_basic(self):
        """基础测试"""
        question = "测试问题"
        relevant_data = {"key": "value"}
        
        prompt = build_qa_prompt(question, relevant_data)
        
        assert isinstance(prompt, str)
        assert "测试问题" in prompt
    
    def test_empty_data(self):
        """空数据测试"""
        prompt = build_qa_prompt("问题", {})
        
        assert isinstance(prompt, str)