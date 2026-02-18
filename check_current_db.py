#!/usr/bin/env python3
"""
检查当前数据库实际状态
"""
from sqlalchemy import create_engine, text
from etl.config import get_connection_string

print('='*80)
print('当前数据库状态检查')
print('='*80)

engine = create_engine(get_connection_string())

with engine.connect() as conn:
    # 总记录数
    total = conn.execute(text('SELECT COUNT(*) FROM daily_orders')).scalar()
    print(f'\n总记录数: {total}')
    
    # 日期范围统计
    date_query = text('''
        SELECT MIN(date) as min_date, MAX(date) as max_date
        FROM daily_orders
    ''')
    result = conn.execute(date_query).first()
    print(f'日期范围: {result.min_date} 至 {result.max_date}')
    
    # 按平台和日期统计
    platform_date_query = text('''
        SELECT platform, date, COUNT(*) as count
        FROM daily_orders
        GROUP BY platform, date
        ORDER BY platform, date
    ''')
    print('\n各平台日期分布:')
    print(f'{"平台":<10} {"日期":<15} {"记录数":<10}')
    print('-'*35)
    for row in conn.execute(platform_date_query):
        print(f'{row.platform:<10} {str(row.date):<15} {row.count:<10}')
    
    # 检查是否有2026-01-11之前的数据
    old_data_query = text('''
        SELECT platform, COUNT(*) as count
        FROM daily_orders
        WHERE date < "2026-01-11"
        GROUP BY platform
    ''')
    old_data = list(conn.execute(old_data_query))
    if old_data:
        print('\n2026-01-11之前的数据:')
        for row in old_data:
            print(f'  {row.platform}: {row.count}条')
    else:
        print('\n⚠️  未找到2026-01-11之前的数据（可能已被删除）')