#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL 门店映射管理脚本

功能：
    - init: 初始化门店映射表
    - list: 列出所有映射
    - add: 添加映射

使用方法：
    python scripts/etl/store_mapping.py init
    python scripts/etl/store_mapping.py list
"""

import sys
import os
import argparse

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pymysql
from sqlalchemy import create_engine, text
from etl.config import get_connection_string, DB_CONFIG


# ==================== 初始化门店映射表 ====================

def init_store_tables():
    """初始化门店映射表"""
    print("=" * 60)
    print("🏪 门店映射表初始化")
    print("=" * 60)
    
    connection = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    try:
        # 1. 创建品牌门店表
        print("\n正在创建 brand_stores 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brand_stores (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                brand_store_name VARCHAR(100) NOT NULL UNIQUE COMMENT '品牌门店名称',
                store_address VARCHAR(200) COMMENT '门店地址',
                store_type VARCHAR(50) COMMENT '门店类型',
                open_date DATE COMMENT '开店时间',
                contact_phone VARCHAR(20) COMMENT '联系电话',
                contact_person VARCHAR(50) COMMENT '联系人',
                status ENUM('营业中', '关闭', '筹备中') DEFAULT '营业中' COMMENT '门店状态',
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_status (status),
                INDEX idx_name (brand_store_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌门店信息表'
        """)
        print("✅ brand_stores 表创建成功")
        
        # 2. 创建门店映射表
        print("正在创建 store_mapping 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS store_mapping (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                brand_store_id INT NOT NULL COMMENT '品牌门店ID',
                platform VARCHAR(20) NOT NULL COMMENT '平台',
                platform_store_name VARCHAR(100) NOT NULL COMMENT '平台门店名称',
                platform_store_id VARCHAR(50) COMMENT '平台门店ID',
                city VARCHAR(100) COMMENT '门店所在城市',
                is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_platform_store (platform, platform_store_name),
                INDEX idx_brand_store (brand_store_id),
                INDEX idx_platform (platform),
                INDEX idx_active (is_active),
                FOREIGN KEY (brand_store_id) REFERENCES brand_stores(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='门店映射关系表'
        """)
        print("✅ store_mapping 表创建成功")
        
        # 3. 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM brand_stores")
        if cursor.fetchone()[0] > 0:
            print("\n⚠️  brand_stores 表已有数据，跳过插入")
        else:
            # 插入品牌门店数据
            print("\n正在插入品牌门店数据...")
            stores = [
                ('信和店', '深圳市南山区信和广场', '直营店', '0755-12345678', '营业中'),
                ('龙华店', '深圳市龙华区龙华大道', '直营店', '0755-12345679', '营业中'),
                ('壹方城店', '深圳市南山区壹方城购物中心', '直营店', '0755-12345680', '营业中'),
                ('新洲店', '深圳市福田区新洲路', '直营店', '0755-12345681', '营业中'),
                ('塘朗店', '深圳市南山区塘朗路', '直营店', '0755-12345682', '营业中'),
                ('蛇口店', '深圳市南山区蛇口海上世界', '直营店', '0755-12345683', '营业中'),
                ('梅林店', '深圳市福田区梅林路', '直营店', '0755-12345684', '营业中'),
                ('马家龙店', '深圳市南山区马家龙路', '直营店', '0755-12345685', '营业中'),
                ('皇庭店', '深圳市福田区皇庭广场', '直营店', '0755-12345686', '营业中'),
                ('登良店', '深圳市南山区登良路', '直营店', '0755-12345687', '营业中'),
                ('车公庙店', '深圳市福田区车公庙', '直营店', '0755-12345688', '营业中'),
                ('大冲店', '深圳市南山区大冲', '直营店', '0755-12345689', '营业中'),
                ('壹方天地店', '深圳市壹方天地店', '直营店', '0755-12345680', '营业中'),
                ('长兴店', '深圳市长兴店', '直营店', '0755-12345679', '营业中'),
                ('后海店', '深圳市后海店', '直营店', '0755-12345679', '营业中'),
            ]
            
            for store in stores:
                cursor.execute("""
                    INSERT INTO brand_stores (brand_store_name, store_address, store_type, contact_phone, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, store)
            print(f"✅ 已插入 {len(stores)} 条品牌门店数据")
        
        # 4. 检查 store_mapping 是否已有数据
        cursor.execute("SELECT COUNT(*) FROM store_mapping")
        if cursor.fetchone()[0] > 0:
            print("\n⚠️  store_mapping 表已有数据，跳过插入")
        else:
            # 获取门店 ID 映射
            cursor.execute("SELECT id, brand_store_name FROM brand_stores")
            store_ids = {row[1]: row[0] for row in cursor.fetchall()}
            
            # 插入门店映射数据
            print("\n正在插入门店映射数据...")
            mappings = [
                # 美团
                ('信和店', '美团', '雪乡情大地锅(信和广场店)'),
                ('龙华店', '美团', '雪乡情东北菜馆(龙华店)'),
                ('壹方城店', '美团', '雪乡情东北菜馆（壹方城店）'),
                ('壹方天地店', '美团', '雪乡情东北菜馆(壹方天地店)'),
                ('新洲店', '美团', '雪乡情东北菜（新洲店）'),
                ('塘朗店', '美团', '雪乡情东北菜（塘朗店）'),
                ('蛇口店', '美团', '雪乡情东北菜（蛇口店）'),
                ('梅林店', '美团', '雪乡情东北菜馆（梅林店）'),
                ('马家龙店', '美团', '雪乡情东北菜（马家龙店）'),
                ('皇庭店', '美团', '雪乡情东北菜馆（皇庭广场店）'),
                ('登良店', '美团', '雪乡情东北菜（登良店）'),
                ('车公庙店', '美团', '雪乡情东北菜（车公庙店）'),
                ('后海店', '美团', '雪乡情铁锅炖（后海店）'),
                ('大冲店', '美团', '雪乡情东北菜馆（大冲店）'),
                # 京东
                ('车公庙店', '京东', '念东北铁锅炖（车公庙店）'),
                ('马家龙店', '京东', '念东北铁锅炖（马家龙店）'),
                ('长兴店', '京东', '念东北铁锅炖（长兴店）'),
                # 饿了么
                ('车公庙店', '饿了么', '雪乡情东北菜(车公庙店)'),
                ('大冲店', '饿了么', '雪乡情东北菜(大冲店)'),
                ('登良店', '饿了么', '雪乡情东北菜(登良店)'),
                ('皇庭店', '饿了么', '雪乡情东北菜(皇庭广场店)'),
                ('马家龙店', '饿了么', '雪乡情东北菜(马家龙店)'),
                ('梅林店', '饿了么', '雪乡情东北菜(梅林店)'),
                ('蛇口店', '饿了么', '雪乡情东北菜(蛇口店)'),
                ('塘朗店', '饿了么', '雪乡情东北菜(塘朗店)'),
                ('新洲店', '饿了么', '雪乡情东北菜(新洲店)'),
                ('壹方城店', '饿了么', '雪乡情东北菜(壹方城店)'),
                ('壹方天地店', '饿了么', '雪乡情东北菜(壹方天地店)'),
                ('后海店', '饿了么', '雪乡情铁锅炖(后海店)'),
                ('信和店', '饿了么', '雪乡情铁锅炖(信和广场店)'),
            ]
            
            inserted = 0
            for brand_name, platform, platform_name in mappings:
                if brand_name in store_ids:
                    try:
                        cursor.execute("""
                            INSERT INTO store_mapping (brand_store_id, platform, platform_store_name, is_active)
                            VALUES (%s, %s, %s, 1)
                        """, (store_ids[brand_name], platform, platform_name))
                        inserted += 1
                    except pymysql.err.IntegrityError:
                        pass
            print(f"✅ 已插入 {inserted} 条门店映射数据")
        
        connection.commit()
        print("\n🎉 门店映射表初始化完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


# ==================== 列出映射 ====================

def list_mappings():
    """列出所有门店映射"""
    print("=" * 60)
    print("📋 门店映射列表")
    print("=" * 60)
    
    engine = create_engine(get_connection_string(), echo=False)
    
    with engine.connect() as conn:
        # 按平台统计
        stats_query = text("""
            SELECT platform, COUNT(*) as count
            FROM store_mapping
            GROUP BY platform
        """)
        print("\n📊 各平台映射数量:")
        for row in conn.execute(stats_query):
            print(f"   {row.platform}: {row.count} 条")
        
        # 列出所有映射
        list_query = text("""
            SELECT bs.brand_store_name, sm.platform, sm.platform_store_name
            FROM store_mapping sm
            JOIN brand_stores bs ON sm.brand_store_id = bs.id
            ORDER BY sm.platform, bs.brand_store_name
        """)
        print("\n📋 映射详情:")
        print(f"   {'品牌门店':<15} {'平台':<8} {'平台门店名称'}")
        print("   " + "-" * 60)
        for row in conn.execute(list_query):
            print(f"   {row.brand_store_name:<15} {row.platform:<8} {row.platform_store_name[:40]}")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description='ETL 门店映射管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init 命令
    subparsers.add_parser('init', help='初始化门店映射表')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有映射')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_store_tables()
    elif args.command == 'list':
        list_mappings()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()