#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL 数据库管理脚本

功能：
    - init: 初始化数据库和表结构
    - clear: 清空 daily_orders 表
    - delete: 删除指定日期范围的数据
    - backup: 备份数据到 CSV 和数据库临时表
    - restore: 从备份恢复数据

使用方法：
    python scripts/etl/db_admin.py init
    python scripts/etl/db_admin.py clear
    python scripts/etl/db_admin.py delete --start 2026-01-12 --end 2026-01-18
    python scripts/etl/db_admin.py backup --start 2026-01-11 --end 2026-01-18
    python scripts/etl/db_admin.py restore --file backup.csv
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from etl.config import get_connection_string, DB_CONFIG, TABLE_NAME


def create_engine_connection():
    """创建数据库连接引擎"""
    return create_engine(get_connection_string(), echo=False, pool_size=5, max_overflow=10, pool_recycle=3600)


# ==================== 初始化数据库 ====================

def init_database():
    """初始化数据库和表结构"""
    print("=" * 60)
    print("🔧 数据库初始化")
    print("=" * 60)
    print(f"\n数据库配置:")
    print(f"  主机: {DB_CONFIG['host']}")
    print(f"  端口: {DB_CONFIG['port']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print(f"  数据库: {DB_CONFIG['database']}")
    
    # 连接 MySQL 服务器（不指定数据库）
    connection = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    try:
        # 创建数据库
        print("\n正在创建数据库 waimai_db...")
        cursor.execute("""
            CREATE DATABASE IF NOT EXISTS waimai_db
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)
        print("✅ 数据库创建成功！")
        
        # 切换到该数据库
        cursor.execute("USE waimai_db")
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'daily_orders'")
        if cursor.fetchone():
            print("⚠️  表 daily_orders 已存在，跳过创建")
        else:
            # 读取 SQL 文件并执行
            sql_file = os.path.join(project_root, 'etl', 'config', 'daily_orders_schema.sql')
            print(f"正在从 {sql_file} 读取表结构...")
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            print("正在创建表 daily_orders...")
            
            # 执行建表 SQL
            create_table_sql = _get_create_table_sql()
            cursor.execute(create_table_sql)
            print("✅ 表 daily_orders 创建成功！")
        
        connection.commit()
        print("\n🎉 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def _get_create_table_sql():
    """获取建表 SQL"""
    return """
    CREATE TABLE daily_orders (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
        import_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据导入时间',
        `date` DATE NOT NULL COMMENT '订单日期',
        brand_store_name VARCHAR(100) COMMENT '品牌门店名称',
        platform VARCHAR(20) NOT NULL COMMENT '平台（美团/饿了么/京东）',
        platform_store_name VARCHAR(100) COMMENT '平台门店名称',
        actual_income DECIMAL(10,2) COMMENT '商家实收',
        expense DECIMAL(10,2) COMMENT '支出',
        turnover DECIMAL(10,2) COMMENT '营业额',
        net_margin_rate DECIMAL(5,2) COMMENT '到手率（百分比）',
        original_price DECIMAL(10,2) COMMENT '商品原价',
        packaging_fee DECIMAL(10,2) COMMENT '包装费',
        customer_delivery_fee DECIMAL(10,2) COMMENT '顾客配送费',
        customer_paid DECIMAL(10,2) COMMENT '顾客实付',
        avg_paid_price DECIMAL(10,2) COMMENT '实付单均价',
        activity_subsidy DECIMAL(10,2) COMMENT '活动补贴',
        platform_service_fee DECIMAL(10,2) COMMENT '平台服务费',
        real_actual_income DECIMAL(10,2) COMMENT '真实实收',
        promotion_cost DECIMAL(10,2) COMMENT '推广花费',
        gift_sausage_cost DECIMAL(10,2) COMMENT '赠红肠成本',
        real_net_margin_rate DECIMAL(5,2) COMMENT '真实到手率',
        valid_orders INT DEFAULT 0 COMMENT '有效订单',
        invalid_orders INT DEFAULT 0 COMMENT '无效订单',
        merchant_cancelled_orders INT DEFAULT 0 COMMENT '商责取消订单',
        merchant_cancellation_rate DECIMAL(5,2) COMMENT '商责取消率',
        store_entry_rate DECIMAL(5,2) COMMENT '入店转化率',
        order_conversion_rate DECIMAL(5,2) COMMENT '下单转化率',
        exposure_count INT DEFAULT 0 COMMENT '曝光人数',
        entry_count INT DEFAULT 0 COMMENT '入店人数',
        order_people INT DEFAULT 0 COMMENT '下单人数',
        uv INT DEFAULT 0 COMMENT 'UV',
        INDEX idx_date (`date`),
        INDEX idx_platform (`platform`),
        INDEX idx_brand_store (`brand_store_name`),
        INDEX idx_date_platform (`date`, `platform`),
        UNIQUE KEY uk_date_platform_store (`date`, `platform`, `brand_store_name`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外卖数据看板 - 每日订单汇总表'
    """


# ==================== 清空表 ====================

def clear_table():
    """清空 daily_orders 表"""
    print("=" * 60)
    print("🗑️  清空 daily_orders 表")
    print("=" * 60)
    
    engine = create_engine_connection()
    
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


# ==================== 删除指定日期数据 ====================

def delete_period(start_date: str, end_date: str):
    """删除指定日期范围的数据"""
    print("=" * 60)
    print("🗑️  删除指定日期范围数据")
    print("=" * 60)
    print(f"📅 日期范围: {start_date} 至 {end_date}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 查询要删除的数据量
        count_query = text(f"""
            SELECT COUNT(*) as count
            FROM {TABLE_NAME}
            WHERE date BETWEEN :start_date AND :end_date
        """)
        result = conn.execute(count_query, {'start_date': start_date, 'end_date': end_date})
        count = result.fetchone()[0]
        
        print(f"\n📊 找到 {count} 条记录将被删除")
        
        if count == 0:
            print("ℹ️  无需删除")
            return
        
        # 确认删除
        confirm = input('⚠️  确定要删除这些数据吗？(yes/no): ')
        if confirm.lower() != 'yes':
            print('❌ 操作已取消')
            return
        
        # 删除数据
        delete_query = text(f"""
            DELETE FROM {TABLE_NAME}
            WHERE date BETWEEN :start_date AND :end_date
        """)
        
        result = conn.execute(delete_query, {'start_date': start_date, 'end_date': end_date})
        conn.commit()
        
        print(f"✅ 已删除 {result.rowcount} 条记录")
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# ==================== 备份数据 ====================

def backup_data(start_date: str, end_date: str):
    """备份指定日期范围的数据"""
    print("=" * 60)
    print("💾 ETL 数据备份")
    print("=" * 60)
    print(f"📅 日期范围: {start_date} 至 {end_date}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    engine = create_engine_connection()
    
    # 查询要备份的数据
    print(f"\n📊 查询数据...")
    query = text(f"""
        SELECT * FROM {TABLE_NAME}
        WHERE date BETWEEN :start_date AND :end_date
        ORDER BY date, platform, brand_store_name
    """)
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={'start_date': start_date, 'end_date': end_date})
    
    print(f"✅ 查询到 {len(df)} 条记录")
    
    if len(df) == 0:
        print("⚠️  没有数据需要备份")
        return
    
    # 保存为 CSV 文件
    backup_dir = os.path.join(project_root, "etl", "data", "backup")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    start_str = start_date.replace('-', '')
    end_str = end_date.replace('-', '')
    backup_file = os.path.join(backup_dir, f"daily_orders_backup_{start_str}_{end_str}_{timestamp}.csv")
    
    df.to_csv(backup_file, index=False, encoding='utf-8-sig')
    print(f"✅ 备份文件已保存: {backup_file}")
    
    # 也备份到数据库临时表
    temp_table = f"{TABLE_NAME}_backup_{timestamp}"
    print(f"\n💾 创建数据库备份表: {temp_table}")
    
    with engine.connect() as conn:
        # 创建临时表
        conn.execute(text(f"CREATE TABLE {temp_table} LIKE {TABLE_NAME}"))
        
        # 插入数据
        insert_query = text(f"""
            INSERT INTO {temp_table}
            SELECT * FROM {TABLE_NAME}
            WHERE date BETWEEN :start_date AND :end_date
        """)
        result = conn.execute(insert_query, {'start_date': start_date, 'end_date': end_date})
        
        conn.commit()
        print(f"✅ 数据库备份完成: {result.rowcount} 条记录")
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"✅ 备份完成！")
    
    return backup_file, temp_table


# ==================== 恢复数据 ====================

def restore_data(backup_file: str):
    """从备份文件恢复数据"""
    print("=" * 60)
    print("📥 恢复数据")
    print("=" * 60)
    print(f"📄 备份文件: {backup_file}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not os.path.exists(backup_file):
        print(f"❌ 备份文件不存在: {backup_file}")
        return
    
    # 读取备份文件
    print("\n📊 读取备份文件...")
    df = pd.read_csv(backup_file, encoding='utf-8-sig')
    print(f"✅ 读取成功，共 {len(df)} 条记录")
    
    engine = create_engine_connection()
    
    with engine.connect() as conn:
        # 获取数据库列名
        result = conn.execute(text('DESCRIBE daily_orders'))
        db_columns = set(row[0] for row in result)
        
        # 只保留数据库存在的列
        df_columns = set(df.columns)
        final_columns = list(df_columns & db_columns)
        df_to_import = df[final_columns]
        
        # 将 NaN 替换为 None
        df_to_import = df_to_import.where(pd.notnull(df_to_import), None)
        
        print(f"\n📋 准备导入 {len(df_to_import)} 条记录")
        
        # 导入数据
        rows_inserted = 0
        batch_size = 1000
        
        for chunk_start in range(0, len(df_to_import), batch_size):
            chunk_end = min(chunk_start + batch_size, len(df_to_import))
            chunk = df_to_import.iloc[chunk_start:chunk_end]
            
            # 使用 INSERT IGNORE 避免重复
            columns_str = ', '.join([f'`{col}`' for col in chunk.columns])
            values_str = ', '.join([f':{col}' for col in chunk.columns])
            
            insert_stmt = text(f"""
                INSERT IGNORE INTO daily_orders ({columns_str}) VALUES ({values_str})
            """)
            
            # 转换数据
            records = chunk.to_dict('records')
            result = conn.execute(insert_stmt, records)
            rows_inserted += result.rowcount
            conn.commit()
            
            print(f'   进度: {chunk_end}/{len(df_to_import)} ({chunk_end/len(df_to_import)*100:.1f}%)')
        
        print(f'\n✅ 导入完成! 成功插入: {rows_inserted} 条')
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description='ETL 数据库管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init 命令
    subparsers.add_parser('init', help='初始化数据库和表结构')
    
    # clear 命令
    subparsers.add_parser('clear', help='清空 daily_orders 表')
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除指定日期范围的数据')
    delete_parser.add_argument('--start', required=True, help='开始日期 (YYYY-MM-DD)')
    delete_parser.add_argument('--end', required=True, help='结束日期 (YYYY-MM-DD)')
    
    # backup 命令
    backup_parser = subparsers.add_parser('backup', help='备份指定日期范围的数据')
    backup_parser.add_argument('--start', required=True, help='开始日期 (YYYY-MM-DD)')
    backup_parser.add_argument('--end', required=True, help='结束日期 (YYYY-MM-DD)')
    
    # restore 命令
    restore_parser = subparsers.add_parser('restore', help='从备份文件恢复数据')
    restore_parser.add_argument('--file', required=True, help='备份文件路径')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_database()
    elif args.command == 'clear':
        clear_table()
    elif args.command == 'delete':
        delete_period(args.start, args.end)
    elif args.command == 'backup':
        backup_data(args.start, args.end)
    elif args.command == 'restore':
        restore_data(args.file)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()