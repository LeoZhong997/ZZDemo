#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空 daily_orders 表的脚本

用于在重新导入数据前清空现有数据。
注意：此操作不可逆，数据将永久删除！

使用方法：
    cd /path/to/ZZDemo
    python etl/scripts/clear_daily_orders.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from etl.config import get_connection_string


def clear_daily_orders():
    """清空 daily_orders 表"""
    engine = create_engine(get_connection_string())
    
    with engine.connect() as conn:
        # 先查看当前记录数
        count_result = conn.execute(text('SELECT COUNT(*) FROM daily_orders')).scalar()
        
        if count_result == 0:
            print('ℹ️  daily_orders 表已经是空的，无需清空')
            return
        
        print(f'📊 当前 daily_orders 表有 {count_result} 条记录')
        
        # 确认清空操作
        confirm = input('⚠️  确定要清空所有数据吗？此操作不可逆！(yes/no): ')
        
        if confirm.lower() != 'yes':
            print('❌ 操作已取消')
            return
        
        # 清空表
        conn.execute(text('TRUNCATE TABLE daily_orders'))
        conn.commit()
        
        print(f'✅ daily_orders 表已清空，删除了 {count_result} 条记录')


if __name__ == '__main__':
    print('=' * 50)
    print('🗑️  清空 daily_orders 表')
    print('=' * 50)
    
    try:
        clear_daily_orders()
    except Exception as e:
        print(f'❌ 清空失败: {e}')
        sys.exit(1)
    
    print('=' * 50)