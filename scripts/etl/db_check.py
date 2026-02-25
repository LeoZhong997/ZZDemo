#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL 数据库检查脚本

功能：
    - status: 检查数据库当前状态
    - unmapped: 检查未映射的门店记录
    - columns: 检查缺失的列
    - metrics: 检查指标映射
    - verify: 验证导入结果

使用方法：
    python scripts/etl/db_check.py status
    python scripts/etl/db_check.py unmapped
    python scripts/etl/db_check.py columns
    python scripts/etl/db_check.py metrics
    python scripts/etl/db_check.py verify
"""

import sys
import os
import argparse

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from etl.config import get_connection_string, TABLE_NAME


def create_engine_connection():
    """创建数据库连接引擎"""
    return create_engine(get_connection_string(), echo=False)


# ==================== 数据库状态检查 ====================

def check_status():
    """检查数据库当前状态"""
    print("=" * 70)
    print("📊 数据库状态检查")
    print("=" * 70)
    
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 总记录数
        total = conn.execute(text('SELECT COUNT(*) FROM daily_orders')).scalar()
        print(f'\n📌 总记录数: {total}')
        
        if total == 0:
            print('\n⚠️  数据库为空')
            return
        
        # 日期范围统计
        date_query = text('''
            SELECT MIN(date) as min_date, MAX(date) as max_date
            FROM daily_orders
        ''')
        result = conn.execute(date_query).first()
        print(f'📅 日期范围: {result.min_date} 至 {result.max_date}')
        
        # 按平台统计
        platform_query = text('''
            SELECT platform, COUNT(*) as count
            FROM daily_orders
            GROUP BY platform
            ORDER BY count DESC
        ''')
        print('\n📊 各平台数据统计:')
        for row in conn.execute(platform_query):
            print(f'   {row.platform}: {row.count} 条')
        
        # 按日期统计（最近7天）
        recent_query = text('''
            SELECT date, COUNT(*) as count
            FROM daily_orders
            GROUP BY date
            ORDER BY date DESC
            LIMIT 7
        ''')
        print('\n📅 最近7天数据统计:')
        for row in conn.execute(recent_query):
            print(f'   {row.date}: {row.count} 条')
        
        # 按门店统计 Top 10
        store_query = text('''
            SELECT brand_store_name, COUNT(*) as count, SUM(actual_income) as total_income
            FROM daily_orders
            GROUP BY brand_store_name
            ORDER BY total_income DESC
            LIMIT 10
        ''')
        print('\n🏪 门店收入 Top 10:')
        print(f'   {"门店名称":<25} {"记录数":<10} {"总收入":<15}')
        print('   ' + '-' * 50)
        for row in conn.execute(store_query):
            income = f'¥{row.total_income:,.2f}' if row.total_income else '¥0.00'
            print(f'   {row.brand_store_name[:22]:<25} {row.count:<10} {income:<15}')


# ==================== 未映射门店检查 ====================

def check_unmapped():
    """检查未映射的门店记录"""
    print("=" * 70)
    print("🔍 未映射门店检查")
    print("=" * 70)
    
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 检查是否有 store_id 字段
        try:
            query = text('''
                SELECT COUNT(*) as total_missing
                FROM daily_orders
                WHERE store_id IS NULL
            ''')
            total_missing = conn.execute(query).scalar()
        except Exception:
            print('\nℹ️  store_id 字段不存在或无数据')
            total_missing = 0
        
        print(f'\n📌 缺少 store_id 的记录数: {total_missing}')
        
        if total_missing == 0:
            print('\n✅ 所有门店都已映射')
            return
        
        # 按平台统计
        platform_query = text('''
            SELECT platform, COUNT(*) as count
            FROM daily_orders
            WHERE store_id IS NULL
            GROUP BY platform
        ''')
        print('\n📊 按平台统计:')
        for row in conn.execute(platform_query):
            print(f'   {row.platform}: {row.count} 条')
        
        # 查看未映射的门店列表
        store_query = text('''
            SELECT DISTINCT brand_store_name, platform
            FROM daily_orders
            WHERE store_id IS NULL
            LIMIT 20
        ''')
        print('\n📋 未映射门店列表 (前20个):')
        for row in conn.execute(store_query):
            print(f'   [{row.platform}] {row.brand_store_name}')


# ==================== 缺失列检查 ====================

def check_columns():
    """检查数据库表是否有缺失的列"""
    print("=" * 70)
    print("🔍 数据库列检查")
    print("=" * 70)
    
    # 预期存在的列
    expected_columns = [
        'id', 'import_time', 'date', 'brand_store_name', 'platform', 
        'platform_store_name', 'actual_income', 'expense', 'turnover',
        'net_margin_rate', 'original_price', 'packaging_fee', 
        'customer_delivery_fee', 'customer_paid', 'avg_paid_price',
        'activity_subsidy', 'platform_service_fee', 'valid_orders', 
        'invalid_orders', 'exposure_count', 'entry_count', 'order_people'
    ]
    
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 获取当前表的列
        result = conn.execute(text('DESCRIBE daily_orders'))
        existing_columns = set(row[0] for row in result)
    
    print(f'\n📌 现有列数: {len(existing_columns)}')
    
    # 检查缺失的列
    missing_columns = set(expected_columns) - existing_columns
    
    if missing_columns:
        print(f'\n⚠️  缺失的列:')
        for col in missing_columns:
            print(f'   - {col}')
    else:
        print('\n✅ 所有核心列都存在')
    
    # 列出所有列
    print(f'\n📋 当前列列表:')
    for i, col in enumerate(sorted(existing_columns), 1):
        print(f'   {i:2}. {col}')


# ==================== 指标映射检查 ====================

def check_metrics():
    """检查指标映射"""
    print("=" * 70)
    print("🔍 指标映射检查")
    print("=" * 70)
    
    # 读取指标映射文件
    mapping_file = os.path.join(project_root, 'etl', 'core', 'field_mapping.py')
    
    if os.path.exists(mapping_file):
        print(f'\n📄 指标映射文件: {mapping_file}')
        print('   文件存在 ✅')
    else:
        print(f'\n⚠️  指标映射文件不存在: {mapping_file}')
    
    # 检查数据库中的指标数据
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 检查核心指标是否有数据
        metrics = [
            ('actual_income', '商家实收'),
            ('turnover', '营业额'),
            ('valid_orders', '有效订单'),
            ('exposure_count', '曝光人数'),
            ('entry_count', '入店人数'),
        ]
        
        print('\n📊 核心指标数据检查:')
        for field, name in metrics:
            try:
                query = text(f'''
                    SELECT COUNT(*) as total, 
                           SUM(CASE WHEN {field} IS NOT NULL AND {field} != 0 THEN 1 ELSE 0 END) as has_data
                    FROM daily_orders
                ''')
                result = conn.execute(query).first()
                if result.total > 0:
                    coverage = result.has_data / result.total * 100
                    print(f'   {name} ({field}): {result.has_data}/{result.total} ({coverage:.1f}%)')
                else:
                    print(f'   {name} ({field}): 无数据')
            except Exception as e:
                print(f'   {name} ({field}): 检查失败 - {e}')


# ==================== 导入结果验证 ====================

def verify_import():
    """验证导入结果"""
    print("=" * 70)
    print("✅ 导入结果验证")
    print("=" * 70)
    
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 基本统计
        total = conn.execute(text('SELECT COUNT(*) FROM daily_orders')).scalar()
        print(f'\n📌 总记录数: {total}')
        
        if total == 0:
            print('\n⚠️  数据库为空，无法验证')
            return
        
        # 检查重复记录
        dup_query = text('''
            SELECT date, platform, brand_store_name, COUNT(*) as count
            FROM daily_orders
            GROUP BY date, platform, brand_store_name
            HAVING count > 1
            LIMIT 10
        ''')
        duplicates = list(conn.execute(dup_query))
        
        if duplicates:
            print(f'\n⚠️  发现重复记录:')
            for row in duplicates:
                print(f'   {row.date} | {row.platform} | {row.brand_store_name} (x{row.count})')
        else:
            print('\n✅ 无重复记录')
        
        # 检查数据完整性
        null_check = text('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN actual_income IS NULL THEN 1 ELSE 0 END) as null_income,
                SUM(CASE WHEN valid_orders IS NULL THEN 1 ELSE 0 END) as null_orders
            FROM daily_orders
        ''')
        result = conn.execute(null_check).first()
        
        print(f'\n📊 数据完整性:')
        print(f'   总记录: {result.total}')
        print(f'   实收为空: {result.null_income} ({result.null_income/result.total*100:.1f}%)')
        print(f'   订单数为空: {result.null_orders} ({result.null_orders/result.total*100:.1f}%)')
        
        # 检查数据范围
        range_query = text('''
            SELECT 
                MIN(actual_income) as min_income,
                MAX(actual_income) as max_income,
                AVG(actual_income) as avg_income,
                MIN(valid_orders) as min_orders,
                MAX(valid_orders) as max_orders
            FROM daily_orders
        ''')
        result = conn.execute(range_query).first()
        
        print(f'\n📈 数据范围:')
        print(f'   实收: {result.min_income:.2f} ~ {result.max_income:.2f} (avg: {result.avg_income:.2f})')
        print(f'   订单数: {result.min_orders} ~ {result.max_orders}')


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description='ETL 数据库检查工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # status 命令
    subparsers.add_parser('status', help='检查数据库当前状态')
    
    # unmapped 命令
    subparsers.add_parser('unmapped', help='检查未映射的门店记录')
    
    # columns 命令
    subparsers.add_parser('columns', help='检查数据库表列')
    
    # metrics 命令
    subparsers.add_parser('metrics', help='检查指标映射')
    
    # verify 命令
    subparsers.add_parser('verify', help='验证导入结果')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        check_status()
    elif args.command == 'unmapped':
        check_unmapped()
    elif args.command == 'columns':
        check_columns()
    elif args.command == 'metrics':
        check_metrics()
    elif args.command == 'verify':
        verify_import()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()