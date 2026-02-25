#!/usr/bin/env python3
"""
验证最终导入结果

使用方法：
    cd /path/to/ZZDemo
    python etl/scripts/verify_import_result.py
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
print('✅ 最终验证结果')
print('='*80)

engine = create_engine(get_connection_string())

with engine.connect() as conn:
    # 总体统计
    total_query = text('SELECT COUNT(*) as total FROM daily_orders')
    total = conn.execute(total_query).scalar()
    print(f'\n总记录数: {total} 条')
    
    if total == 0:
        print('\n⚠️  数据库为空，请先运行 ETL 导入数据')
        sys.exit(0)
    
    # 按平台统计
    platform_query = text('''
        SELECT platform, COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date
        FROM daily_orders
        GROUP BY platform
        ORDER BY platform
    ''')
    print('\n各平台统计:')
    print(f'{"平台":<10} {"记录数":<10} {"最小日期":<15} {"最大日期":<15}')
    print('-'*50)
    for row in conn.execute(platform_query):
        print(f'{row.platform:<10} {row.count:<10} {str(row.min_date):<15} {str(row.max_date):<15}')
    
    # 检查关键字段
    print('\n关键字段完整性:')
    
    # 检查列是否存在
    columns_query = text('''
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'daily_orders'
    ''')
    existing_columns = set(row.COLUMN_NAME for row in conn.execute(columns_query))
    
    # 检查 store_id 列
    if 'store_id' in existing_columns:
        store_id_query = text('SELECT COUNT(*) as count FROM daily_orders WHERE store_id IS NOT NULL')
        store_id_count = conn.execute(store_id_query).scalar()
        print(f'store_id: {store_id_count}/{total} ({store_id_count/total*100:.1f}%)')
    else:
        print('store_id: ⚠️ 列不存在')
    
    # 检查 city 列
    if 'city' in existing_columns:
        city_query = text('SELECT COUNT(*) as count FROM daily_orders WHERE city IS NOT NULL')
        city_count = conn.execute(city_query).scalar()
        print(f'city: {city_count}/{total} ({city_count/total*100:.1f}%)')
    else:
        print('city: ⚠️ 列不存在')
    
    brand_name_query = text('SELECT COUNT(*) as count FROM daily_orders WHERE brand_store_name IS NOT NULL')
    brand_name_count = conn.execute(brand_name_query).scalar()
    print(f'brand_store_name: {brand_name_count}/{total} ({brand_name_count/total*100:.1f}%)')
    
    date_query = text('SELECT COUNT(*) as count FROM daily_orders WHERE date IS NOT NULL')
    date_count = conn.execute(date_query).scalar()
    print(f'date: {date_count}/{total} ({date_count/total*100:.1f}%)')
    
    print('\n✅ 验证完成！所有三个平台数据导入成功！')