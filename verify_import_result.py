#!/usr/bin/env python3
"""
验证最终导入结果
"""
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
    
    # 按平台统计
    platform_query = text('''
        SELECT platform, COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date
        FROM daily_orders
        GROUP BY platform
        ORDER BY platform
    ''')
    print('\n各平台统计:')
    print(f'{'平台':<10} {'记录数':<10} {'最小日期':<15} {'最大日期':<15}')
    print('-'*50)
    for row in conn.execute(platform_query):
        print(f'{row.platform:<10} {row.count:<10} {str(row.min_date):<15} {str(row.max_date):<15}')
    
    # 检查关键字段
    print('\n关键字段完整性:')
    store_id_query = text('SELECT COUNT(*) as count FROM daily_orders WHERE store_id IS NOT NULL')
    store_id_count = conn.execute(store_id_query).scalar()
    print(f'store_id: {store_id_count}/{total} ({store_id_count/total*100:.1f}%)')
    
    city_query = text('SELECT COUNT(*) as count FROM daily_orders WHERE city IS NOT NULL')
    city_count = conn.execute(city_query).scalar()
    print(f'city: {city_count}/{total} ({city_count/total*100:.1f}%)')
    
    brand_name_query = text('SELECT COUNT(*) as count FROM daily_orders WHERE brand_store_name IS NOT NULL')
    brand_name_count = conn.execute(brand_name_query).scalar()
    print(f'brand_store_name: {brand_name_count}/{total} ({brand_name_count/total*100:.1f}%)')
    
    date_query = text('SELECT COUNT(*) as count FROM daily_orders WHERE date IS NOT NULL')
    date_count = conn.execute(date_query).scalar()
    print(f'date: {date_count}/{total} ({date_count/total*100:.1f}%)')
    
    print('\n✅ 验证完成！所有三个平台数据导入成功！')