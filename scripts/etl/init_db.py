"""
数据库初始化脚本
用于创建数据库和表结构
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pymysql
from etl.config.config import DB_CONFIG

def init_database():
    """初始化数据库"""
    # 首先连接 MySQL 服务器（不指定数据库）
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
        print("正在创建数据库 waimai_db...")
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
            # SQL 文件在 etl/config/ 目录下
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sql_file = os.path.join(project_root, 'etl', 'config', 'daily_orders_schema.sql')
            print(f"正在从 {sql_file} 读取表结构...")
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 执行 SQL（移除注释后执行）
            # 由于 pymysql 不能直接执行多条语句，我们需要逐条执行
            # 这里我们手动创建表
            print("正在创建表 daily_orders...")
            
            create_table_sql = """
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
                customer_delivery_fee DECIMAL(10,2) COMMENT '顾客配送费（跑腿/自配送）',
                customer_paid DECIMAL(10,2) COMMENT '顾客实付',
                avg_paid_price DECIMAL(10,2) COMMENT '实付单均价',
                activity_subsidy DECIMAL(10,2) COMMENT '活动补贴',
                platform_service_fee DECIMAL(10,2) COMMENT '平台服务费(含佣金和配送服务费)',
                real_actual_income DECIMAL(10,2) COMMENT '真实实收',
                promotion_cost DECIMAL(10,2) COMMENT '推广花费',
                gift_sausage_cost DECIMAL(10,2) COMMENT '赠红肠成本',
                real_net_margin_rate DECIMAL(5,2) COMMENT '真实到手率（百分比）',
                valid_orders INT DEFAULT 0 COMMENT '有效订单',
                invalid_orders INT DEFAULT 0 COMMENT '无效订单',
                merchant_cancelled_orders INT DEFAULT 0 COMMENT '商责取消订单',
                merchant_cancellation_rate DECIMAL(5,2) COMMENT '商责取消率（百分比）',
                store_entry_rate DECIMAL(5,2) COMMENT '入店转化率（百分比）',
                order_conversion_rate DECIMAL(5,2) COMMENT '下单转化率（百分比）',
                new_customer_entry_rate DECIMAL(5,2) COMMENT '新客入店转化率（百分比）',
                new_customer_order_rate DECIMAL(5,2) COMMENT '新客下单转化率（百分比）',
                old_customer_entry_rate DECIMAL(5,2) COMMENT '老客入店转化率（百分比）',
                old_customer_order_rate DECIMAL(5,2) COMMENT '老客下单转化率（百分比）',
                repurchase_rate DECIMAL(5,2) COMMENT '复购率（百分比）',
                exposure_count INT DEFAULT 0 COMMENT '曝光人数',
                entry_count INT DEFAULT 0 COMMENT '入店人数',
                exposure_new_customer INT DEFAULT 0 COMMENT '曝光新客',
                entry_new_customer INT DEFAULT 0 COMMENT '入店新客',
                exposure_old_customer INT DEFAULT 0 COMMENT '曝光老客',
                entry_old_customer INT DEFAULT 0 COMMENT '入店老客',
                exposure_times INT DEFAULT 0 COMMENT '曝光次数',
                entry_times INT DEFAULT 0 COMMENT '入店次数',
                order_people INT DEFAULT 0 COMMENT '下单人数',
                order_new_customer INT DEFAULT 0 COMMENT '下单新客',
                order_old_customer INT DEFAULT 0 COMMENT '下单老客',
                uv INT DEFAULT 0 COMMENT 'UV',
                store_score DECIMAL(5,2) COMMENT '店铺分',
                peak_duration_score DECIMAL(5,2) COMMENT '高峰营业时长得分',
                quality_product_rate_score DECIMAL(5,2) COMMENT '优质商品率得分',
                activity_richness_score DECIMAL(5,2) COMMENT '有效活动丰富度得分',
                reject_order_rate_score DECIMAL(5,2) COMMENT '商家不接单率得分',
                bad_review_reply_rate_score DECIMAL(5,2) COMMENT '差评回复率得分',
                online_reply_rate_score DECIMAL(5,2) COMMENT '在线联系回复率得分',
                new_merchant_score DECIMAL(5,2) COMMENT '新商家评分',
                menu_richness_score DECIMAL(5,2) COMMENT '菜单丰富度得分',
                decoration_richness_score DECIMAL(5,2) COMMENT '装修丰富度得分',
                service_function_score DECIMAL(5,2) COMMENT '服务功能丰富度得分',
                overall_experience_score DECIMAL(5,2) COMMENT '综合体验分',
                product_quality_score DECIMAL(5,2) COMMENT '商品质量分',
                service_experience_score DECIMAL(5,2) COMMENT '服务体验分',
                product_satisfaction DECIMAL(5,2) COMMENT '商品满意度',
                packaging_satisfaction DECIMAL(5,2) COMMENT '包装满意度',
                old_merchant_score DECIMAL(5,2) COMMENT '旧商家评分',
                repurchase_rate_score DECIMAL(5,2) COMMENT '复购率指标得分',
                message_reply_rate_score DECIMAL(5,2) COMMENT '消息回复率指标得分',
                service_negative_feedback_score DECIMAL(5,2) COMMENT '服务负反馈率指标得分',
                food_safety_negative_feedback_score DECIMAL(5,2) COMMENT '食品安全负反馈率指标得分',
                five_min_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '5分钟回复率',
                one_min_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '1分钟回复率',
                message_reply_rate DECIMAL(5,4) DEFAULT 0 COMMENT '消息回复率',
                food_safety_negative_feedback_rate DECIMAL(5,4) DEFAULT 0 COMMENT '食品安全负反馈率',
                basic_duration DECIMAL(6,1) COMMENT '基础营业时长（小时）',
                meal_completion_report_rate DECIMAL(5,2) COMMENT '出餐完成上报率（百分比）',
                INDEX idx_date (`date`),
                INDEX idx_platform (`platform`),
                INDEX idx_brand_store (`brand_store_name`),
                INDEX idx_date_platform (`date`, `platform`),
                INDEX idx_import_time (`import_time`),
                UNIQUE KEY uk_date_platform_store (`date`, `platform`, `brand_store_name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外卖数据看板 - 每日订单汇总表'
            """
            
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


if __name__ == "__main__":
    print("=" * 50)
    print("外卖数据看板 - 数据库初始化")
    print("=" * 50)
    print(f"\n数据库配置:")
    print(f"  主机: {DB_CONFIG['host']}")
    print(f"  端口: {DB_CONFIG['port']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print(f"  数据库: {DB_CONFIG['database']}")
    print()
    
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        sys.exit(1)