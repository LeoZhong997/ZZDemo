#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL系统运行脚本

从项目根目录运行ETL系统
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """
    主函数：运行ETL系统
    """
    print("="*70)
    print("🍔 外卖数据看板 - ETL系统")
    print("="*70)
    print()
    
    # 导入ETL主模块
    try:
        from etl.core.etl_main import main as etl_main_func
        etl_main_func()
    except ImportError as e:
        print(f"❌ 导入ETL模块失败: {e}")
        print("请确保etl目录结构正确")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ETL运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()