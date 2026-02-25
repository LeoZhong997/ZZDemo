#!/usr/bin/env python3
"""
从外卖源数据.xlsx恢复2026-01-11之前的历史数据

使用方法：
    cd /path/to/ZZDemo
    python etl/scripts/restore_historical_data.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from sqlalchemy import create_engine, text
from etl.config import get_connection_string
from datetime import datetime

print('='*80)
print('从外卖源数据.xlsx恢复历史数据')
print('='*80)

file_path = os.path.join(project_root, 'etl/data/sources/目标源数据/外卖源数据.xlsx')

# 读取源数据
print('\n📄 读取外卖源数据.xlsx...')
df = pd.read_excel(file_path, sheet_name=0)
print(f'✅ 读取成功，共 {len(df)} 条记录')

# 过滤2026-01-11之前的数据
print('\n🔍 过滤2026-01-11之前的数据...')
df['日期'] = pd.to_datetime(df['日期']).dt.date
df_before_20260111 = df[df['日期'] < pd.Timestamp('2026-01-11').date()]
print(f'✅ 筛选出 {len(df_before_20260111)} 条2026-01-11之前的数据')

# 统计各平台数据量
print('\n📊 各平台数据统计:')
for platform in df_before_20260111['平台'].unique():
    count = len(df_before_20260111[df_before_20260111['平台'] == platform])
    print(f'   {platform}: {count} 条')

# 统计日期范围
print('\n📅 日期范围统计:')
print(f'   最小日期: {df_before_20260111["日期"].min()}')
print(f'   最大日期: {df_before_20260111["日期"].max()}')
print(f'   唯一日期数: {df_before_20260111["日期"].nunique()}')

# 重命名列以匹配数据库表结构
print('\n🔄 调整列名...')
column_mapping = {
    '日期': 'date',
    '品牌门店名称': 'brand_store_name',
    '平台': 'platform',
    '平台门店名称': 'platform_store_name',
    '商家实收': 'actual_income',
    '营业额': 'turnover',
    '有效订单': 'valid_orders',
    '无效订单': 'invalid_orders',
    '商品原价': 'goods_original_price',
    '包装费': 'packaging_fee',
    '顾客实付': 'customer_paid',
    '活动补贴': 'activity_subsidy',
    '平台服务费(含佣金和配送服务费)': 'platform_service_fee'
}

df_import = df_before_20260111.rename(columns=column_mapping)
print(f'✅ 列名映射完成')

# 添加缺失的字段（设为NULL）
print('\n📝 添加缺失字段...')
required_fields = ['store_id', 'city', 'income', 'customer_paid', 'discounts', 
                   'commission', 'delivery_fee', 'service_fee', 'store_entry_rate', 
                   'order_conversion_rate', 'repurchase_rate']

for field in required_fields:
    if field not in df_import.columns:
        df_import[field] = None
print(f'✅ 已添加缺失字段')

# 添加导入时间
df_import['import_time'] = datetime.now()

# 将NaN替换为None（MySQL不接受NaN）
df_import = df_import.replace({float('nan'): None})

# 获取数据库表结构，只保留存在的列
print('\n📡 连接数据库...')
engine = create_engine(get_connection_string())

with engine.connect() as conn:
    # 获取数据库列名
    result = conn.execute(text('DESCRIBE daily_orders'))
    db_columns = set(row[0] for row in result)
    
    # 只保留数据库存在的列
    df_columns = set(df_import.columns)
    final_columns = list(df_columns & db_columns)
    df_to_import = df_import[final_columns]
    
    if len(final_columns) < len(df_import.columns):
        removed = list(df_columns - set(final_columns))
        print(f'\n⚠️  跳过{len(removed)}个数据库不存在的列: {removed[:5]}...')
    
    print(f'\n📋 准备导入 {len(df_to_import)} 条记录')
    print(f'   列数: {len(df_to_import.columns)}')
    
    # 导入数据
    print('\n💾 开始导入数据...')
    from sqlalchemy.dialects.mysql import insert
    
    rows_inserted = 0
    batch_size = 1000
    
    for chunk_start in range(0, len(df_to_import), batch_size):
        chunk_end = min(chunk_start + batch_size, len(df_to_import))
        chunk = df_to_import.iloc[chunk_start:chunk_end]
        
        # 使用INSERT IGNORE避免重复
        insert_stmt = text(f"""
            INSERT IGNORE INTO daily_orders
            ({', '.join([f'`{col}`' for col in chunk.columns])})
            VALUES ({', '.join([':' + col for col in chunk.columns])})
        """)
        
        result = conn.execute(insert_stmt, chunk.to_dict('records'))
        rows_inserted += result.rowcount
        conn.commit()
        
        print(f'   进度: {chunk_end}/{len(df_to_import)} ({chunk_end/len(df_to_import)*100:.1f}%)')
    
    print(f'\n✅ 导入完成!')
    print(f'   成功插入: {rows_inserted} 条')
    
    # 验证结果
    print('\n🔍 验证导入结果...')
    
    # 查询总记录数
    total_count = conn.execute(text('SELECT COUNT(*) FROM daily_orders')).scalar()
    print(f'   当前数据库总记录数: {total_count}')
    
    # 查询日期范围
    date_range = conn.execute(text('''
        SELECT MIN(date) as min_date, MAX(date) as max_date
        FROM daily_orders
    ''')).first()
    print(f'   日期范围: {date_range.min_date} 至 {date_range.max_date}')
    
    # 查询各平台数据量
    platform_stats = conn.execute(text('''
        SELECT platform, COUNT(*) as count
        FROM daily_orders
        GROUP BY platform
        ORDER BY platform
    '''))
    print(f'\n📊 各平台数据统计:')
    for row in platform_stats:
        print(f'   {row.platform}: {row.count} 条')
    
    # 查询2026-01-11之前的记录数
    old_data_count = conn.execute(text('''
        SELECT COUNT(*) FROM daily_orders
        WHERE date < "2026-01-11"
    ''')).scalar()
    print(f'\n✅ 2026-01-11之前的记录数: {old_data_count} 条')

print('\n' + '='*80)
print('🎉 数据恢复完成！')
print('='*80)