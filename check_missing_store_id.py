#!/usr/bin/env python3
"""
检查缺少store_id的历史数据
"""
from sqlalchemy import create_engine, text
from etl.config import get_connection_string
from etl.core.store_mapper import get_store_mapper

print('='*80)
print('检查缺少store_id的历史数据')
print('='*80)

engine = create_engine(get_connection_string())

with engine.connect() as conn:
    # 查询缺少store_id的记录
    query = text('''
        SELECT COUNT(*) as total_missing
        FROM daily_orders
        WHERE store_id IS NULL
    ''')
    total_missing = conn.execute(query).scalar()
    
    print(f'\n📊 缺少store_id的记录总数: {total_missing}')
    
    if total_missing > 0:
        # 按平台统计
        platform_query = text('''
            SELECT platform, COUNT(*) as count
            FROM daily_orders
            WHERE store_id IS NULL
            GROUP BY platform
        ''')
        print('\n📋 按平台统计:')
        for row in conn.execute(platform_query):
            print(f'   {row.platform}: {row.count} 条')
        
        # 按日期范围统计
        date_query = text('''
            SELECT 
                MIN(date) as min_date,
                MAX(date) as max_date,
                COUNT(*) as count
            FROM daily_orders
            WHERE store_id IS NULL
        ''')
        date_result = conn.execute(date_query).first()
        print(f'\n📅 日期范围:')
        print(f'   最小日期: {date_result.min_date}')
        print(f'   最大日期: {date_result.max_date}')
        
        # 查看前10条示例
        sample_query = text('''
            SELECT date, platform, brand_store_name, platform_store_name
            FROM daily_orders
            WHERE store_id IS NULL
            LIMIT 10
        ''')
        print('\n📄 前10条示例记录:')
        print(f'{"日期":<15} {"平台":<10} {"品牌门店名称":<20} {"平台门店名称"}')
        print('-'*65)
        for row in conn.execute(sample_query):
            print(f'{str(row.date):<15} {row.platform:<10} {row.brand_store_name:<20} {str(row.platform_store_name)[:30]}')
        
        # 检查store_mapper能否映射这些门店
        print('\n🔍 测试store_mapper映射能力:')
        store_mapper = get_store_mapper()
        
        test_query = text('''
            SELECT DISTINCT platform, brand_store_name
            FROM daily_orders
            WHERE store_id IS NULL
            LIMIT 20
        ''')
        
        mapped_count = 0
        unmapped_stores = []
        
        for row in conn.execute(test_query):
            mapped_store_id = store_mapper.get_store_id(row.platform, row.brand_store_name)
            if mapped_store_id:
                mapped_count += 1
                print(f'   ✅ {row.platform} - {row.brand_store_name} -> store_id: {mapped_store_id}')
            else:
                unmapped_stores.append(f'{row.platform} - {row.brand_store_name}')
        
        if unmapped_stores:
            print(f'\n   ⚠️  无法映射的门店:')
            for store in unmapped_stores[:10]:
                print(f'      {store}')
        
        print(f'\n📊 映射能力统计:')
        print(f'   测试记录数: {mapped_count + len(unmapped_stores)}')
        print(f'   可映射: {mapped_count}')
        print(f'   不可映射: {len(unmapped_stores)}')