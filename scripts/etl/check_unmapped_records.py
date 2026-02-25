#!/usr/bin/env python3
"""
检查未找到映射的记录

使用方法：
    cd /path/to/ZZDemo
    python etl/scripts/check_unmapped_records.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from etl.config import get_connection_string

print('='*80)
print('检查未找到映射的记录')
print('='*80)

engine = create_engine(get_connection_string())

with engine.connect() as conn:
    # 查询未找到映射的记录（store_id仍为NULL）
    query = text('''
        SELECT DISTINCT platform, brand_store_name, COUNT(*) as count
        FROM daily_orders
        WHERE store_id IS NULL
        GROUP BY platform, brand_store_name
        ORDER BY platform, count DESC
    ''')
    
    unmapped_records = list(conn.execute(query))
    
    print(f'\n📊 未找到映射的门店: {len(unmapped_records)} 个')
    
    if unmapped_records:
        print(f'\n{"平台":<10} {"品牌门店名称":<20} {"记录数":<10}')
        print('-'*45)
        
        total_unmapped = 0
        for record in unmapped_records:
            print(f'{record.platform:<10} {record.brand_store_name:<20} {record.count:<10}')
            total_unmapped += record.count
        
        print(f'\n总记录数: {total_unmapped}')
        
        # 按平台统计
        print(f'\n📋 按平台统计:')
        platform_query = text('''
            SELECT platform, COUNT(*) as count
            FROM daily_orders
            WHERE store_id IS NULL
            GROUP BY platform
        ''')
        for row in conn.execute(platform_query):
            print(f'   {row.platform}: {row.count} 条')
        
        # 检查store_mapping表中有哪些映射
        print(f'\n🔍 store_mapping表中的映射:')
        mapping_query = text('''
            SELECT 
                sm.platform,
                bs.brand_store_name,
                COUNT(*) as count
            FROM store_mapping sm
            INNER JOIN brand_stores bs ON sm.brand_store_id = bs.id
            WHERE sm.is_active = 1
            GROUP BY sm.platform, bs.brand_store_name
            ORDER BY sm.platform, bs.brand_store_name
            LIMIT 50
        ''')
        
        print(f'\n{"平台":<10} {"品牌门店名称":<20} {"映射状态"}')
        print('-'*40)
        for row in conn.execute(mapping_query):
            # 检查daily_orders中是否有此组合
            exists = conn.execute(text('''
                SELECT COUNT(*) FROM daily_orders
                WHERE platform = :platform AND brand_store_name = :brand_store_name
                LIMIT 1
            '''), {
                'platform': row.platform,
                'brand_store_name': row.brand_store_name
            }).scalar()
            
            status = '✅ 已使用' if exists > 0 else '⚪ 未使用'
            print(f'{row.platform:<10} {row.brand_store_name:<20} {status}')

print('\n💡 建议:')
print('   1. 对于未映射的门店，需要在门店管理界面添加映射关系')
print('   2. 或者检查brand_store_name是否与store_mapping表中的名称一致')
print('   3. 添加映射后，可以重新运行此脚本来补全store_id')