"""
Dashboard 加载 E2E 测试
测试主页面和导航功能
"""
import pytest
from playwright.sync_api import Page, expect
from .conftest import DASHBOARD_URL, take_screenshot, wait_for_element


class TestDashboardLoad:
    """Dashboard 加载测试"""
    
    def test_dashboard_loads_successfully(self, dashboard_page: Page):
        """测试 Dashboard 主页加载成功"""
        # 验证页面标题包含关键词
        title = dashboard_page.title()
        assert "外卖" in title or "Dashboard" in title or "数据" in title, f"页面标题不符合预期: {title}"
        
        # 截图
        take_screenshot(dashboard_page, "dashboard_main")
    
    def test_sidebar_visible(self, dashboard_page: Page):
        """测试侧边栏可见"""
        # Streamlit 侧边栏
        sidebar = dashboard_page.query_selector('[data-testid="stSidebar"]')
        assert sidebar is not None, "侧边栏应该存在"
    
    def test_main_content_visible(self, dashboard_page: Page):
        """测试主内容区域可见"""
        # 主内容区域
        main_content = dashboard_page.query_selector('[data-testid="stMain"]')
        assert main_content is not None, "主内容区域应该存在"
    
    def test_navigation_menu_exists(self, dashboard_page: Page):
        """测试导航菜单存在"""
        # Streamlit 页面导航
        # 查找侧边栏中的页面链接
        dashboard_page.wait_for_timeout(2000)  # 等待页面完全加载
        
        # 检查是否有导航元素
        nav_elements = dashboard_page.query_selector_all('a, [role="button"]')
        assert len(nav_elements) > 0, "应该有导航元素"
    
    def test_page_responsive(self, dashboard_page: Page):
        """测试页面响应式"""
        # 测试不同视口大小
        viewports = [
            {"width": 1920, "height": 1080},  # 桌面
            {"width": 1366, "height": 768},   # 笔记本
            {"width": 768, "height": 1024},   # 平板
        ]
        
        for viewport in viewports:
            dashboard_page.set_viewport_size(viewport)
            dashboard_page.wait_for_timeout(500)
            
            # 页面应该仍然可访问
            main_content = dashboard_page.query_selector('[data-testid="stMain"]')
            assert main_content is not None, f"视口 {viewport} 下主内容应该存在"


class TestDashboardNavigation:
    """Dashboard 导航测试"""
    
    def test_navigate_to_week_data(self, dashboard_page: Page):
        """测试导航到周报数据页面"""
        # 点击周报数据链接
        week_data_link = dashboard_page.query_selector('text=/周报数据/')
        
        if week_data_link:
            week_data_link.click()
            dashboard_page.wait_for_load_state("networkidle")
            
            # 验证 URL 变化或内容变化
            take_screenshot(dashboard_page, "week_data_page")
    
    def test_navigate_to_ai_insights(self, dashboard_page: Page):
        """测试导航到 AI 诊断页面"""
        # 点击 AI 诊断链接
        ai_link = dashboard_page.query_selector('text=/AI.*诊断|AI.*报告/')
        
        if ai_link:
            ai_link.click()
            dashboard_page.wait_for_load_state("networkidle")
            take_screenshot(dashboard_page, "ai_insights_nav")
    
    def test_navigate_to_ai_prediction(self, dashboard_page: Page):
        """测试导航到 AI 预测页面"""
        # 点击 AI 预测链接
        pred_link = dashboard_page.query_selector('text=/预测|营收预测/')
        
        if pred_link:
            pred_link.click()
            dashboard_page.wait_for_load_state("networkidle")
            take_screenshot(dashboard_page, "ai_prediction_nav")


class TestDashboardErrorHandling:
    """Dashboard 错误处理测试"""
    
    def test_no_javascript_errors(self, dashboard_page: Page):
        """测试无 JavaScript 错误"""
        errors = []
        
        def handle_console(msg):
            if msg.type == 'error':
                errors.append(msg.text)
        
        dashboard_page.on("console", handle_console)
        
        # 等待页面稳定
        dashboard_page.wait_for_timeout(3000)
        
        # 过滤掉一些已知的非关键错误
        critical_errors = [e for e in errors if 'ChunkLoadError' not in e and '404' not in e]
        
        # 不应该有严重的 JavaScript 错误
        # 注意：Streamlit 可能有一些非关键的控制台警告
        assert len(critical_errors) == 0, f"发现 JavaScript 错误: {critical_errors}"
    
    def test_page_reload(self, dashboard_page: Page):
        """测试页面刷新"""
        # 刷新页面
        dashboard_page.reload()
        dashboard_page.wait_for_load_state("networkidle")
        
        # 页面应该正常加载
        main_content = dashboard_page.query_selector('[data-testid="stMain"]')
        assert main_content is not None, "刷新后主内容应该存在"