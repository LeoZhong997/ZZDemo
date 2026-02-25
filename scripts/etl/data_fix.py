#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL 数据修复脚本

功能：
    - conversion: 修复转化率格式（小数转百分比）
    - duplicates: 清理重复数据
    - store_id: 修复缺失的 store_id

使用方法：
    python scripts/etl/data_fix.py conversion
    python scripts/etl/data_fix.py duplicates
    python scripts/etl/data_fix.py store_id
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


# ==================== 修复转化率 ====================

def fix_conversion_rates():
    """修复数据库中的转化率值（从小数格式转换为百分比格式）"""
    print("=" * 60)
    print("🔄 修复转化率数据")
    print("=" * 60)
    
    engine = create_engine_connection()
    
    # 需要转换的转化率字段
    conversion_fields = [
        'store_entry_rate', 'order_conversion_rate',
        'new_customer_entry_rate', 'new_customer_order_rate',
        'old_customer_entry_rate', 'old_customer_order_rate',
        'repurchase_rate', 'five_min_reply_rate', 'one_min_reply_rate',
        'message_reply_rate', 'service_negative_feedback_rate',
        'food_safety_negative_feedback_rate', 'meal_completion_report_rate',
        'merchant_cancellation_rate', 'net_margin_rate', 'real_net_margin_rate'
    ]
    
    for field in conversion_fields:
        print(f"\n📊 更新 {field}...")
        
        with engine.connect() as conn:
            # 执行更新（将小于1的正值乘以100）
            update_query = text(f"""
                UPDATE {TABLE_NAME}
                SET {field} = {field} * 100
                WHERE {field} < 1 AND {field} > 0
            """)
            result = conn.execute(update_query)
            conn.commit()
            
            if result.rowcount > 0:
                print(f"   ✅ 更新了 {result.rowcount} 条记录")
            else:
                print(f"   ℹ️  无需更新")
    
    print(f"\n✅ 转化率修复完成！")


# ==================== 清理重复数据 ====================

def cleanup_duplicates():
    """清理数据库中的重复数据"""
    print("=" * 60)
    print("🧹 清理重复数据")
    print("=" * 60)
    
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 检查重复记录
        dup_query = text(f"""
            SELECT date, platform, brand_store_name, COUNT(*) as count
            FROM {TABLE_NAME}
            GROUP BY date, platform, brand_store_name
            HAVING count > 1
        """)
        duplicates = list(conn.execute(dup_query))
        
        if not duplicates:
            print("\n✅ 没有发现重复数据")
            return
        
        print(f"\n⚠️  发现 {len(duplicates)} 组重复数据")
        
        # 确认清理
        confirm = input('确认要清理重复数据吗？(yes/no): ')
        if confirm.lower() != 'yes':
            print('❌ 操作已取消')
            return
        
        # 删除重复记录（保留 ID 最小的）
        delete_query = text(f"""
            DELETE t1 FROM {TABLE_NAME} t1
            INNER JOIN (
                SELECT date, platform, brand_store_name, MIN(id) as min_id
                FROM {TABLE_NAME}
                GROUP BY date, platform, brand_store_name
                HAVING COUNT(*) > 1
            ) t2 ON t1.date = t2.date 
                AND t1.platform = t2.platform 
                AND t1.brand_store_name = t2.brand_store_name
            WHERE t1.id > t2.min_id
        """)
        
        result = conn.execute(delete_query)
        conn.commit()
        
        print(f"✅ 已删除 {result.rowcount} 条重复记录")


# ==================== 修复 store_id ====================

def fix_store_id():
    """修复缺失的 store_id"""
    print("=" * 60)
    print("🔧 修复 store_id")
    print("=" * 60)
    
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 检查 store_id 字段是否存在
        try:
            count_query = text(f"""
                SELECT COUNT(*) FROM {TABLE_NAME} WHERE store_id IS NULL
            """)
            missing_count = conn.execute(count_query).scalar()
        except Exception:
            print("\nℹ️  store_id 字段不存在")
            return
        
        print(f"\n📌 缺少 store_id 的记录: {missing_count}")
        
        if missing_count == 0:
            print("✅ 所有记录都有 store_id")
            return
        
        # 通过 store_mapping 更新 store_id
        update_query = text(f"""
            UPDATE {TABLE_NAME} d
            INNER JOIN store_mapping s ON d.platform = s.platform 
                AND d.platform_store_name = s.platform_store_name
            SET d.store_id = s.brand_store_id
            WHERE d.store_id IS NULL
        """)
        
        result = conn.execute(update_query)
        conn.commit()
        
        print(f"✅ 已更新 {result.rowcount} 条记录")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description='ETL 数据修复工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # conversion 命令
    subparsers.add_parser('conversion', help='修复转化率格式')
    
    # duplicates 命令
    subparsers.add_parser('duplicates', help='清理重复数据')
    
    # store_id 命令
    subparsers.add_parser('store_id', help='修复缺失的 store_id')
    
    args = parser.parse_args()
    
    if args.command == 'conversion':
        fix_conversion_rates()
    elif args.command == 'duplicates':
        cleanup_duplicates()
    elif args.command == 'store_id':
        fix_store_id()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()