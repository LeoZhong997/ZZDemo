"""
运行 E2E 测试脚本
启动 Dashboard 并运行 Playwright 测试
"""
import subprocess
import time
import sys
import requests
import os

DASHBOARD_URL = "http://localhost:8501"
DASHBOARD_PORT = 8501


def wait_for_dashboard(timeout: int = 60) -> bool:
    """等待 Dashboard 启动"""
    print(f"等待 Dashboard 启动 ({DASHBOARD_URL})...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(DASHBOARD_URL, timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard 已启动")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    
    print("❌ Dashboard 启动超时")
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("E2E 测试运行脚本")
    print("=" * 60)
    
    # 检查是否需要启动 Dashboard
    dashboard_process = None
    
    try:
        # 检查 Dashboard 是否已运行
        response = requests.get(DASHBOARD_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard 已在运行")
        else:
            raise Exception("Dashboard 未运行")
    except:
        print("启动 Dashboard...")
        # 启动 Dashboard
        dashboard_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", 
             "--server.port", str(DASHBOARD_PORT),
             "--server.headless", "true"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待 Dashboard 启动
        if not wait_for_dashboard():
            if dashboard_process:
                dashboard_process.terminate()
            sys.exit(1)
    
    try:
        # 运行 E2E 测试
        print("\n" + "=" * 60)
        print("运行 Playwright E2E 测试...")
        print("=" * 60 + "\n")
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--tb=short"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        return result.returncode
        
    finally:
        # 清理：关闭 Dashboard（如果是本脚本启动的）
        if dashboard_process:
            print("\n关闭 Dashboard...")
            dashboard_process.terminate()
            try:
                dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dashboard_process.kill()


if __name__ == "__main__":
    sys.exit(main() or 0)