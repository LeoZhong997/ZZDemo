#!/usr/bin/env python3
"""
直接导入外卖源数据到数据库（完整版）
包含中文列名到英文字段名的映射
"""
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import sys

# ========== 数据库配置 ==========
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '1203',
    'database': 'waimai_db'
}

# ========== 列名映射：中文列名 -> 英文字段名 ==========
COLUMN_MAPPING = {
    '日期': 'date',
    '品牌门店名称': 'brand_store_name',
    '平台': 'platform',
    '平台门店名称': 'platform_store_name',
    '商家实收': 'actual_income',
    '支出': 'expense',
    '营业额': 'turnover',
    '到手率': 'net_margin_rate',
    '有效订单': 'valid_orders',
    '无效订单': 'invalid_orders',
    '商品原价': 'original_price',
    '包装费': 'packaging_fee',
    '顾客配送费（跑腿/自配送）': 'customer_delivery_fee',
    '顾客实付': 'customer_paid',
    '实付单均价': 'avg_paid_price',
    '活动补贴': 'activity_subsidy',
    '平台服务费(含佣金和配送服务费)': 'platform_service_fee',
    '曝光人数': 'exposure_count',
    '入店人数': 'entry_count',
    '入店转化率': 'store_entry_rate',
    '下单转化率': 'order_conversion_rate',
    '曝光新客': 'exposure_new_customer',
    '入店新客': 'entry_new_customer',
    '新客入店转化率': 'new_customer_entry_rate',
    '新客下单转化率': 'new_customer_order_rate',
    '曝光老客': 'exposure_old_customer',
    '入店老客': 'entry_old_customer',
    '老客入店转化率': 'old_customer_entry_rate',
    '老客下单转化率': 'old_customer_order_rate',
    '曝光次数': 'exposure_times',
    '入店次数': 'entry_times',
    '下单人数': 'order_people',
    '下单新客': 'order_new_customer',
    '下单老客': 'order_old_customer',
    '商责取消订单': 'merchant_cancelled_orders',
    '商责取消率': 'merchant_cancellation_rate',
    '店铺分': 'store_score',
    '高峰营业时长得分': 'peak_duration_score',
    '优质商品率得分': 'quality_product_rate_score',
    '有效活动丰富度得分': 'activity_richness_score',
    '商家不接单率得分': 'reject_order_rate_score',
    '差评回复率得分': 'bad_review_reply_rate_score',
    '在线联系回复率得分': 'online_reply_rate_score',
    '新商家评分': 'new_merchant_score',
    '菜单丰富度得分': 'menu_richness_score',
    '装修丰富度得分': 'decoration_richness_score',
    '服务功能丰富度得分': 'service_function_score',
    '5分钟在线联系回复率': 'five_min_reply_rate',
    '1分钟在线联系回复率': 'one_min_reply_rate',
    '基础营业时长': 'basic_duration',
    '真实实收': 'real_actual_income',
    '推广花费': 'promotion_cost',
    '出餐完成上报率': 'meal_completion_report_rate',
    'UV': 'uv',
    '赠红肠成本': 'gift_sausage_cost',
    '真实到手率': 'real_net_margin_rate',
    '综合体验分': 'overall_experience_score',
    '商品质量分': 'product_quality_score',
    '服务体验分': 'service_experience_score',
    '商品满意度': 'product_satisfaction',
    '包装满意度': 'packaging_satisfaction',
    '复购率指标得分': 'repurchase_rate_score',
    '复购率': 'repurchase_rate',
    '消息回复率指标得分': 'message_reply_rate_score',
    '消息回复率': 'message_reply_rate',
    '服务负反馈率指标得分': 'service_negative_feedback_score',
    '食品安全负反馈率指标得分': 'food_safety_negative_feedback_score',
    '食品安全负反馈率': 'food_safety_negative_feedback_rate',
    '旧商家评分': 'old_merchant_score',
}

# ========== 数据库连接 ==========
def get_engine():
    """创建数据库连接"""
    connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8mb4"
    return create_engine(connection_string, pool_size=5, max_overflow=10, pool_recycle=3600)

def test_database():
    """测试数据库连接"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def load_data():
    """读取Excel数据"""
    print("📄 正在读取外卖源数据...")

    file_path = "目标源数据/外卖源数据.xlsx"
    try:
        df = pd.read_excel(file_path, sheet_name="源数据")
        print(f"✅ 数据读取成功")
        print(f"   总行数: {len(df)}")
        print(f"   总列数: {len(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ 读取Excel失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def clean_data(df):
    """清洗和转换数据"""
    print("\n🔄 正在重命名列...")

    # 重命名列（中文 -> 英文）
    df = df.rename(columns=COLUMN_MAPPING)
    print(f"✅ 已映射 {len(COLUMN_MAPPING)} 个列名")

    # 确保日期格式正确
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date

    # 添加导入时间
    df['import_time'] = datetime.now()

    # 处理空值
    print("🔄 正在处理空值...")
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)

    # 处理数值字段（包括金额和百分比）
    print("🔄 正在处理数值字段...")
    
    # 获取所有需要数值处理的列（所有英文列名，除了日期和字符串字段）
    exclude_columns = {'date', 'brand_store_name', 'platform', 'platform_store_name', 'import_time'}
    numeric_fields = [col for col in df.columns if col not in exclude_columns and col in COLUMN_MAPPING.values()]
    
    for col in numeric_fields:
        if col in df.columns:
            if df[col].dtype == 'object':
                # 去掉百分号、逗号、空格、货币符号等
                df[col] = df[col].astype(str)
                df[col] = df[col].str.replace('%', '').replace(',', '').replace('¥', '').replace('$', '')
                df[col] = df[col].str.replace('nan', '0').replace('NaN', '0').replace('c', '0')
                df[col] = df[col].str.strip()
                # 转换为数值
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 处理订单数量等整数字段
    integer_fields = ['valid_orders', 'invalid_orders', 'merchant_cancelled_orders', 
                    'exposure_count', 'entry_count', 'exposure_new_customer', 
                    'entry_new_customer', 'exposure_old_customer', 'entry_old_customer',
                    'exposure_times', 'entry_times', 'order_people', 
                    'order_new_customer', 'order_old_customer', 'uv']
    for col in integer_fields:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    print(f"✅ 数据清洗完成")
    return df

def import_data(df):
    """导入数据到数据库"""
    print("\n💾 正在导入数据库...")

    try:
        engine = get_engine()

        # 获取数据库表的列名
        with engine.connect() as conn:
            result = conn.execute(text("DESCRIBE daily_orders"))
            db_columns = set(row[0] for row in result)

        df_columns = set(df.columns)

        # 只保留数据库中存在的列
        final_columns = list(df_columns & db_columns)
        df_to_import = df[final_columns]

        if len(final_columns) < len(df_columns):
            removed = list(df_columns - db_columns)
            print(f"⚠️  跳过 {len(removed)} 个数据库不存在的列: {', '.join(removed[:5])}...")

        # 分批导入
        batch_size = 1000
        total_rows = len(df_to_import)
        batches = (total_rows + batch_size - 1) // batch_size

        for i in range(batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, total_rows)

            batch_df = df_to_import.iloc[start_idx:end_idx]

            # 写入数据库
            batch_df.to_sql(
                name='daily_orders',
                con=engine,
                if_exists='append',
                index=False,
                method='multi'
            )

            print(f"   进度: {end_idx}/{total_rows} ({end_idx/total_rows*100:.1f}%)")

        print(f"\n✅ 数据导入成功！共导入 {total_rows} 条记录")
        return True

    except Exception as e:
        print(f"❌ 数据导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*60)
    print("🍔 外卖数据导入工具")
    print("="*60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # 步骤1: 测试数据库连接
    if not test_database():
        print("\n❌ 无法连接数据库，程序退出")
        sys.exit(1)

    # 步骤2: 读取数据
    df = load_data()
    if df is None:
        sys.exit(1)

    # 步骤3: 清洗数据
    df = clean_data(df)

    # 步骤4: 导入数据
    if import_data(df):
        print("\n" + "="*60)
        print("🎉 导入完成！")
        print("="*60)
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 显示导入统计
        print(f"\n📊 数据统计:")
        print(f"   总记录数: {len(df)}")
        if 'platform' in df.columns:
            print(f"\n   平台分布:")
            for platform, count in df['platform'].value_counts().items():
                print(f"      {platform:10s}: {count:5d} 条 ({count/len(df)*100:.1f}%)")
        if 'date' in df.columns:
            print(f"\n   日期范围: {df['date'].min()} ~ {df['date'].max()}")

        # 查询数据库验证
        print(f"\n🔍 验证数据库记录...")
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM daily_orders"))
            count = result.fetchone()[0]
            print(f"   数据库中共有 {count:,} 条记录")
    else:
        print("\n❌ 导入失败")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 程序发生异常:")
        import traceback
        traceback.print_exc()
        sys.exit(1)
