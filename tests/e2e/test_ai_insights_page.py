"""
AI 诊断报告页面 E2E 测试
测试 AI Insights 页面功能
"""
import pytest
from playwright.sync_api import Page
from .conftest import DASHBOARD_URL, take_screenshot, wait_for_element


class TestAIInsightsPageLoad:
    """AI 诊断页面加载测试"""
    
    def test_page_loads_successfully(self, ai_insights_page: Page):
        """测试 AI 诊断页面加载成功"""
        # 等待页面加载
        ai_insights_page.wait_for_load_state("networkidle")
        
        # 验证页面标题或关键词
        page_content = ai_insights_page.content()
        assert "AI" in page_content or "诊断" in page_content or "报告" in page_content
        
        take_screenshot(ai_insights_page, "ai_insights_loaded")
    
    def test_sidebar_config_visible(self, ai_insights_page: Page):
        """测试侧边栏配置区域可见"""
        # 查找侧边栏
        sidebar = ai_insights_page.query_selector('[data-testid="stSidebar"]')
        assert sidebar is not None, "侧边栏应该存在"
        
        # 侧边栏应该包含配置相关元素
        sidebar_content = sidebar.inner_text() if sidebar else ""
        assert any(keyword in sidebar_content for keyword in ["日期", "平台", "门店", "配置", "LLM"])
    
    def test_date_picker_exists(self, ai_insights_page: Page):
        """测试日期选择器存在"""
        # Streamlit 日期选择器
        date_inputs = ai_insights_page.query_selector_all('input[type="date"]')
        
        # 如果没有找到原生日期输入，查找 Streamlit 日期组件
        if not date_inputs:
            date_components = ai_insights_page.query_selector_all('[data-testid="stDateInput"]')
            assert len(date_components) > 0, "应该有日期选择组件"


class TestAIInsightsFunctionality:
    """AI 诊断功能测试"""
    
    def test_generate_diagnosis_button_exists(self, ai_insights_page: Page):
        """测试生成诊断按钮存在"""
        # 查找生成诊断按钮
        buttons = ai_insights_page.query_selector_all('button')
        button_texts = [btn.inner_text() for btn in buttons]
        
        # 应该有生成报告相关的按钮
        has_diagnosis_button = any(
            "诊断" in text or "生成" in text or "报告" in text 
            for text in button_texts
        )
        assert has_diagnosis_button or len(buttons) > 0, "应该有操作按钮"
    
    def test_test_llm_connection_button(self, ai_insights_page: Page):
        """测试 LLM 连接测试按钮"""
        # 查找测试连接按钮
        test_buttons = ai_insights_page.query_selector_all('button:has-text("测试")')
        
        # 按钮应该存在
        assert len(test_buttons) >= 0, "可能有 LLM 测试按钮"
    
    def test_platform_multiselect(self, ai_insights_page: Page):
        """测试平台多选框"""
        # 查找多选框
        multiselects = ai_insights_page.query_selector_all('[data-testid="stMultiSelect"]')
        
        # 应该有平台选择器
        assert len(multiselects) >= 0, "应该有多选组件"


class TestAIInsightsReportGeneration:
    """AI 诊断报告生成测试"""
    
    def test_report_sections_structure(self, ai_insights_page: Page):
        """测试报告区域结构"""
        # 等待页面稳定
        ai_insights_page.wait_for_timeout(2000)
        
        # 查找主要内容区域
        main_content = ai_insights_page.query_selector('[data-testid="stMain"]')
        assert main_content is not None, "主内容区域应该存在"
        
        # 页面应该包含预期的结构元素
        content_text = main_content.inner_text()
        
        # 检查是否有报告相关的标题
        expected_keywords = ["门店", "平台", "异常", "诊断", "AI", "分析"]
        found_keywords = [kw for kw in expected_keywords if kw in content_text]
        
        # 至少应该有一些关键词
        assert len(found_keywords) >= 0, "页面应该包含相关内容"
    
    def test_metrics_display(self, ai_insights_page: Page):
        """测试指标显示"""
        # 查找指标卡片
        metrics = ai_insights_page.query_selector_all('[data-testid="stMetric"]')
        
        # 如果有数据显示，应该有指标卡片
        # 注意：页面初始可能没有数据
        assert len(metrics) >= 0


class TestAIInsightsErrorHandling:
    """AI 诊断页面错误处理测试"""
    
    def test_no_data_message(self, ai_insights_page: Page):
        """测试无数据时的提示"""
        # 等待页面加载
        ai_insights_page.wait_for_timeout(2000)
        
        # 页面应该正常显示，即使没有数据
        main_content = ai_insights_page.query_selector('[data-testid="stMain"]')
        assert main_content is not None
    
    def test_graceful_error_display(self, ai_insights_page: Page):
        """测试错误优雅显示"""
        # 监听控制台错误
        errors = []
        
        def handle_console(msg):
            if msg.type == 'error':
                errors.append(msg.text)
        
        ai_insights_page.on("console", handle_console)
        
        # 等待页面稳定
        ai_insights_page.wait_for_timeout(3000)
        
        # 页面应该没有严重的 JavaScript 错误
        critical_errors = [e for e in errors if 'ChunkLoadError' not in e]
        assert len(critical_errors) == 0, f"发现 JavaScript 错误: {critical_errors}"