#!/usr/bin/env python3
"""
补全历史数据的store_id并删除city列

使用方法：
    cd /path/to/ZZDemo
    python etl/scripts/fix_store_id_and_drop_city.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from etl.config import get_connection_string
from etl.core.store_mapper import get_store_mapper

print('='*80)
print('补全store_id并删除city列')
print('='*80)

engine = create_engine(get_connection_string())

# 步骤1: 补全store_id
print('\n📝 步骤 1/3: 补全历史数据的store_id...')

with engine.connect() as conn:
    # 查询缺少store_id的记录
    query = text('''
        SELECT id, platform, brand_store_name, platform_store_name
        FROM daily_orders
        WHERE store_id IS NULL
    ''')
    
    records_to_update = list(conn.execute(query))
    total_count = len(records_to_update)
    
    print(f'   找到 {total_count} 条需要补全store_id的记录')
    
    if total_count > 0:
        # 获取store_mapper
        store_mapper = get_store_mapper()
        
        # 统计
        updated_count = 0
        not_found_count = 0
        
        for record in records_to_update:
            mapping = store_mapper.get_mapping(record.platform, record.brand_store_name)
            
            if mapping and 'brand_store_id' in mapping:
                # 更新store_id
                update_query = text('''
                    UPDATE daily_orders
                    SET store_id = :store_id
                    WHERE id = :id
                ''')
                conn.execute(update_query, {
                    'store_id': mapping['brand_store_id'],
                    'id': record.id
                })
                updated_count += 1
                
                if updated_count % 1000 == 0:
                    print(f'   进度: {updated_count}/{total_count} ({updated_count/total_count*100:.1f}%)')
            else:
                not_found_count += 1
        
        conn.commit()
        
        print(f'\n   ✅ 更新完成:')
        print(f'      成功更新: {updated_count} 条')
        print(f'      未找到映射: {not_found_count} 条')
    else:
        print('   ✅ 所有记录都已包含store_id')

# 步骤2: 删除city列
print('\n📝 步骤 2/3: 删除city列...')

with engine.connect() as conn:
    # 检查city列是否存在
    check_query = text('''
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'daily_orders'
          AND COLUMN_NAME = 'city'
    ''')
    
    city_exists = conn.execute(check_query).fetchone()
    
    if city_exists:
        # 删除city列
        alter_query = text('''
            ALTER TABLE daily_orders
            DROP COLUMN city
        ''')
        conn.execute(alter_query)
        conn.commit()
        print('   ✅ city列已删除')
    else:
        print('   ℹ️  city列不存在，无需删除')

# 步骤3: 验证结果
print('\n📝 步骤 3/3: 验证结果...')

with engine.connect() as conn:
    # 检查剩余的NULL store_id
    null_store_id_count = conn.execute(text('''
        SELECT COUNT(*) FROM daily_orders WHERE store_id IS NULL
    ''')).scalar()
    
    print(f'   缺少store_id的记录数: {null_store_id_count}')
    
    # 检查city列是否还存在
    city_exists = conn.execute(text('''
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'daily_orders'
          AND COLUMN_NAME = 'city'
    ''')).scalar()
    
    print(f'   city列是否存在: {"是" if city_exists > 0 else "否 (已删除)"}')
    
    # 显示表结构
    print('\n📊 当前表结构 (关键字段):')
    desc_query = text('''
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'daily_orders'
        ORDER BY ORDINAL_POSITION
        LIMIT 20
    ''')
    
    print(f'\n{"字段名":<25} {"数据类型":<15} {"可空":<8} {"键"}')
    print('-'*55)
    for row in conn.execute(desc_query):
        print(f'{row.COLUMN_NAME:<25} {row.DATA_TYPE:<15} {row.IS_NULLABLE:<8} {row.COLUMN_KEY or ""}')

print('\n' + '='*80)
print('🎉 操作完成！')
print('='*80)