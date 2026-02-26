"""
Playwright E2E 测试配置
提供 fixtures 和通用测试工具
"""
import pytest
import subprocess
import time
import requests
import os
import sys
from playwright.sync_api import Page, Browser, BrowserContext

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ========== 配置常量 ==========
DASHBOARD_HOST = "localhost"
DASHBOARD_PORT = 8501
DASHBOARD_URL = f"http://{DASHBOARD_HOST}:{DASHBOARD_PORT}"
STARTUP_TIMEOUT = 30  # Dashboard 启动超时（秒）
PAGE_LOAD_TIMEOUT = 15  # 页面加载超时（秒）


# ========== Fixtures ==========
@pytest.fixture(scope="module")
def dashboard_process():
    """
    启动 Streamlit Dashboard 进程
    模块级别 fixture，整个测试模块只启动一次
    """
    # 启动 Dashboard
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", 
         "--server.headless", "true",
         "--server.port", str(DASHBOARD_PORT)],
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待 Dashboard 启动
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            response = requests.get(DASHBOARD_URL, timeout=2)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        process.kill()
        pytest.fail(f"Dashboard 启动超时 ({STARTUP_TIMEOUT}秒)")
    
    # 返回进程对象
    yield process
    
    # 清理：终止进程
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture(scope="function")
def dashboard_page(page: Page, dashboard_process):
    """
    Dashboard 页面 fixture
    每个测试函数独立的页面对象
    """
    page.set_default_timeout(PAGE_LOAD_TIMEOUT * 1000)
    page.goto(DASHBOARD_URL)
    # 等待页面加载完成
    page.wait_for_load_state("networkidle")
    yield page


@pytest.fixture(scope="function")
def ai_insights_page(page: Page, dashboard_process):
    """
    AI 诊断报告页面 fixture
    """
    page.set_default_timeout(PAGE_LOAD_TIMEOUT * 1000)
    page.goto(f"{DASHBOARD_URL}/ai_insights")
    page.wait_for_load_state("networkidle")
    yield page


@pytest.fixture(scope="function")
def ai_prediction_page(page: Page, dashboard_process):
    """
    AI 预测分析页面 fixture
    """
    page.set_default_timeout(PAGE_LOAD_TIMEOUT * 1000)
    page.goto(f"{DASHBOARD_URL}/ai_prediction")
    page.wait_for_load_state("networkidle")
    yield page


# ========== 辅助函数 ==========
def wait_for_element(page: Page, selector: str, timeout: int = 10000):
    """等待元素出现"""
    return page.wait_for_selector(selector, timeout=timeout)


def take_screenshot(page: Page, name: str):
    """截图保存"""
    screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    page.screenshot(path=os.path.join(screenshot_dir, f"{name}.png"))


def is_element_visible(page: Page, selector: str) -> bool:
    """检查元素是否可见"""
    try:
        element = page.query_selector(selector)
        return element is not None and element.is_visible()
    except Exception:
        return False


def get_element_text(page: Page, selector: str) -> str:
    """获取元素文本"""
    try:
        element = page.query_selector(selector)
        return element.inner_text() if element else ""
    except Exception:
        return ""


def click_and_wait(page: Page, selector: str, wait_time: int = 1000):
    """点击并等待"""
    page.click(selector)
    page.wait_for_timeout(wait_time)