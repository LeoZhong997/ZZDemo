#!/usr/bin/env python3
"""
导入平台下载的原始源数据到数据库
支持：京东、饿了么、美团三个平台的原始导出文件
"""
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import sys

# ========== 数据库配置（使用统一配置）==========
from ..config import DB_CONFIG, get_connection_string

# ========== 京东平台字段映射 ==========
JD_MAPPING = {
    '门店名称': 'brand_store_name',
    '门店id': 'store_id',
    '日期': 'date',
    '城市': 'city',
    '收入': 'actual_income',
    '营业额': 'turnover',
    '支出': 'expense',
    '活动补贴': 'activity_subsidy',
    '顾客实付': 'customer_paid',
    '有效订单': 'valid_orders',
    '实付单均价': 'avg_paid_price',
    '商家活动成本': 'promotion_cost',
    '佣金': 'commission',
    '配送服务费': 'delivery_service_fee',
    '曝光人数': 'exposure_count',
    '入店人数': 'entry_count',
    '入店转化率': 'store_entry_rate',
    '下单转化率': 'order_conversion_rate',
    '入店次数': 'entry_times',
    '曝光次数': 'exposure_times',
    '活动订单量': 'activity_orders',
    '活动力度': 'activity_strength',
    '投入产出比': 'roi',
    '日均营业时长': 'basic_duration',
    '日均高峰营业时长': 'peak_duration',
    '履约准时率': 'on_time_rate',
    '平均履约时长': 'avg_fulfillment_time',
    '商责介入率': 'merchant_intervention_rate',
}

# ========== 美团平台字段映射 ==========
MEITUAN_MAPPING = {
    '日期': 'date',
    '门店名称': 'brand_store_name',
    '门店id': 'store_id',
    '省份': 'province',
    '门店所在城市': 'city',
    '区县市': 'district',
    '营业收入': 'actual_income',
    '商品原价': 'original_price',
    '包装费': 'packaging_fee',
    '顾客配送费（跑腿/自配送）': 'customer_delivery_fee',
    '补贴及支出': 'expense',
    '商家活动支出': 'merchant_activity_cost',
    '公益捐款': 'charity_donation',
    '其它支出': 'other_expense',
    '优惠前总额': 'total_before_discount',
    '顾客实付': 'customer_paid',
    '有效订单': 'valid_orders',
    '实付单均价': 'avg_paid_price',
    '活动补贴': 'activity_subsidy',
    '平台活动补贴': 'platform_activity_subsidy',
    '平台服务费(含佣金和配送服务费)': 'platform_service_fee',
    '顾客实付（不含券）': 'customer_paid_no_coupon',
    '实付单均价（不含券）': 'avg_paid_price_no_coupon',
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
    '当日流量类型': 'daily_traffic_type',
    '7日流量类型': 'weekly_traffic_type',
    '30日流量类型': 'monthly_traffic_type',
    '下单人数': 'order_people',
    '下单新客': 'order_new_customer',
    '下单老客': 'order_old_customer',
    '取消订单': 'cancelled_orders',
    '商责取消订单': 'merchant_cancelled_orders',
    '商责取消率': 'merchant_cancellation_rate',
    '店铺分': 'store_score',
    '高峰营业时长得分': 'peak_duration_score',
    '优质商品率得分': 'quality_product_rate_score',
    '有效活动丰富度得分': 'activity_richness_score',
    '商家不接单率得分': 'reject_order_rate_score',
    '差评回复率得分': 'bad_review_reply_rate_score',
    '在线联系回复率得分': 'online_reply_rate_score',
    '商家评分得分': 'merchant_score',
    '近30日日均高峰营业时长': 'recent_peak_duration',
    '优质商品率': 'quality_product_rate',
    '有效活动丰富度': 'activity_richness',
    '近30日商家不接单率': 'recent_reject_rate',
    '近30日差评回复率': 'recent_bad_review_reply_rate',
    '近7日日均在线联系回复率': 'recent_online_reply_rate',
    '近30日日均商家评分': 'recent_merchant_score',
    '菜单丰富度得分': 'menu_richness_score',
    '装修丰富度得分': 'decoration_richness_score',
    '服务功能丰富度得分': 'service_function_score',
    '菜单丰富度': 'menu_richness',
    '装修丰富度': 'decoration_richness',
    '服务功能丰富度': 'service_function_richness',
    '出餐完成上报率/配送准时率': 'meal_completion_report_rate',
    '基础营业时长得分': 'basic_duration_score',
    '基础营业时长': 'basic_duration',
    '出餐完成上报率得分/配送准时率得分': 'meal_completion_report_score',
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
}

# ========== 饿了么平台字段映射 ==========
ELEME_MAPPING = {
    '日期': 'date',
    '门店名称': 'brand_store_name',
    '门店编号': 'store_id',
    '营业时长': 'basic_duration',
    '高峰期营业时长': 'peak_duration',
    '省份': 'province',
    '城市名称': 'city',
    '区县名称': 'district',
    '门店地址': 'store_address',
    '首次营业时间': 'first_business_time',
    '是否直营': 'is_direct',
    '设置营业时间段': 'business_time_setting',
    '异常关店时间段': 'abnormal_close_time',
    '异常关店时长': 'abnormal_close_duration',
    '是否开通到店自取': 'has_self_pickup',
    '是否有效门店': 'is_valid_store',
    '有效订单': 'valid_orders',
    '无效订单': 'invalid_orders',
    '收入': 'actual_income',
    '营业额': 'turnover',
    '商品销售额': 'product_sales',
    '打包费': 'packaging_fee',
    '商家应收配送费': 'merchant_delivery_fee',
    '索赔单': 'claim_orders',
    '其他营业额': 'other_turnover',
    '支出': 'expense',
    '平台技术服务费': 'platform_service_fee',
    '活动补贴': 'activity_subsidy',
    '代金券补贴': 'voucher_subsidy',
    '配送费补贴': 'delivery_fee_subsidy',
    '智能满减补贴': 'smart_discount_subsidy',
    '智能满减服务费': 'smart_discount_fee',
    '履约技术服务费': 'fulfillment_service_fee',
    '退单费用': 'refund_fee',
    '其他支出': 'other_expense',
    '顾客实付总额': 'customer_paid',
    '单均实付': 'avg_paid_price',
    '单均收入': 'avg_income',
    '商户原因无效订单数': 'merchant_invalid_orders',
    '曝光人数': 'exposure_count',
    '新客曝光人数': 'exposure_new_customer',
    '老客曝光人数': 'exposure_old_customer',
    '进店人数': 'entry_count',
    '新客进店人数': 'entry_new_customer',
    '老客进店人数': 'entry_old_customer',
    '下单人数': 'order_people',
    '新客下单人数': 'order_new_customer',
    '老客下单人数': 'order_old_customer',
    '进店转化率': 'store_entry_rate',
    '新客进店转化率': 'new_customer_entry_rate',
    '老客进店转化率': 'old_customer_entry_rate',
    '下单转化率': 'order_conversion_rate',
    '新客下单转化率': 'new_customer_order_rate',
    '老客下单转化率': 'old_customer_order_rate',
    '曝光次数': 'exposure_times',
    '进店次数': 'entry_times',
    '下单次数': 'order_times',
    '参与活动数': 'participated_activities',
    '活动订单数': 'activity_orders',
    '活动订单占比': 'activity_order_rate',
    '满减活动订单数': 'discount_activity_orders',
    '超会活动订单数': 'vip_activity_orders',
    '配送活动订单数': 'delivery_activity_orders',
    '投入产出比': 'roi',
    '活动总补贴': 'total_activity_subsidy',
    '饿了么补贴': 'eleme_subsidy',
    '代理商补贴': 'agent_subsidy',
    '商家活动成本（含满减活动）': 'merchant_activity_cost_with_discount',
    '商家活动成本（不含满减活动）': 'merchant_activity_cost_without_discount',
    '营销力度（含满减活动）': 'marketing_strength_with_discount',
    '营销力度（不含满减活动）': 'marketing_strength_without_discount',
    '近7日复购人数': 'recent_7d_repurchase_count',
    '近7日复购率': 'recent_7d_repurchase_rate',
    '近30日复购人数': 'recent_30d_repurchase_count',
    '近30日复购率': 'recent_30d_repurchase_rate',
    '上架商品数': 'listed_products',
    '有交易商品数': 'sold_products',
    '库存不足商品数': 'out_of_stock_products',
    '新上架商品数': 'new_products',
    '活动商品数': 'activity_products',
    '差评订单数': 'bad_review_orders',
    '投诉订单数': 'complaint_orders',
    '投诉订单id': 'complaint_order_ids',
    '出餐超时订单数': 'meal_timeout_orders',
    '出餐超时订单id': 'meal_timeout_order_ids',
    '单均出餐时长': 'avg_meal_time',
    '拒单数': 'rejected_orders',
    '出餐宝扫码出餐订单数': 'scan_meal_orders',
    '商责退单数': 'merchant_refund_orders',
    '商责取消率': 'merchant_cancellation_rate',
    '商责退单率': 'merchant_refund_rate',
    '商责取消数': 'merchant_cancel_count',
    '自配送配送信息未上报订单数': 'self_delivery_not_reported_orders',
    '自配送配送信息未上报订单列表': 'self_delivery_not_reported_list',
    '自配送送达超时订单数': 'self_delivery_timeout_orders',
    '自配送送达超时订单列表': 'self_delivery_timeout_list',
    '自取时长设置值': 'self_pickup_time_setting',
    '单均取餐时长': 'avg_pickup_time',
    '店铺评分': 'store_score',
    '满意度得分': 'satisfaction_score',
    '味道得分': 'taste_score',
    '包装得分': 'packaging_score',
    '近60日好评率': 'recent_60d_good_review_rate',
    '近60日好评数': 'recent_60d_good_review_count',
    '近60日中评率': 'recent_60d_medium_review_rate',
    '近60日中评数': 'recent_60d_medium_review_count',
    '近60日差评率': 'recent_60d_bad_review_rate',
    '近60日差评数': 'recent_60d_bad_review_count',
    '近60日优质评价率': 'recent_60d_high_quality_review_rate',
    '近60日优质评价数': 'recent_60d_high_quality_review_count',
    '近60日订单评价率': 'recent_60d_order_review_rate',
    '近60日订单评价数': 'recent_60d_order_review_count',
    '近60日差评人工回复率': 'recent_60d_bad_review_reply_rate',
    '近30天好评率': 'recent_30d_good_review_rate',
    '近30天好评数': 'recent_30d_good_review_count',
    '近30天中评率': 'recent_30d_medium_review_rate',
    '近30天中评数': 'recent_30d_medium_review_count',
    '近30天差评率': 'recent_30d_bad_review_rate',
    '近30天差评数': 'recent_30d_bad_review_count',
    '近30天优质评价率': 'recent_30d_high_quality_review_rate',
    '近30天优质评价数': 'recent_30d_high_quality_review_count',
    '近30天订单评价率': 'recent_30d_order_review_rate',
    '近30天订单评价数': 'recent_30d_order_review_count',
    '近30天差评人工回复率': 'recent_30d_bad_review_reply_rate',
}

# ========== 数据库连接 ==========
def get_engine():
    """创建数据库连接"""
    return create_engine(get_connection_string(), pool_size=5, max_overflow=10, pool_recycle=3600)

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

def get_db_columns():
    """获取数据库表的所有列名"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("DESCRIBE daily_orders"))
        return set(row[0] for row in result)

def read_jd_file(file_path):
    """读取京东数据"""
    print(f"📄 正在读取京东数据: {file_path}")
    try:
        df = pd.read_excel(file_path, sheet_name='数据')
        df['platform'] = '京东'
        df['platform_store_name'] = df['门店名称']  # 京东只有门店名称
        print(f"✅ 京东数据读取成功，共 {len(df)} 行 {len(df.columns)} 列")
        return df, JD_MAPPING
    except Exception as e:
        print(f"❌ 读取京东数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def read_meituan_file(file_path):
    """读取美团数据"""
    print(f"📄 正在读取美团数据: {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='gbk')
        df['platform'] = '美团'
        df['platform_store_name'] = df['门店名称']
        # 处理日期：美团CSV的日期是YYYYMMDD格式的整数
        if df['日期'].dtype in ['int64', 'object']:
            df['日期'] = pd.to_datetime(df['日期'].astype(str), format='%Y%m%d', errors='coerce').dt.date
        print(f"✅ 美团数据读取成功，共 {len(df)} 行 {len(df.columns)} 列")
        return df, MEITUAN_MAPPING
    except Exception as e:
        print(f"❌ 读取美团数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def read_eleme_file(file_path):
    """读取饿了么数据"""
    print(f"📄 正在读取饿了么数据: {file_path}")
    try:
        df = pd.read_excel(file_path, sheet_name='data')
        df['platform'] = '饿了么'
        df['platform_store_name'] = df['门店名称']  # 饿了么只有门店名称
        print(f"✅ 饿了么数据读取成功，共 {len(df)} 行 {len(df.columns)} 列")
        return df, ELEME_MAPPING
    except Exception as e:
        print(f"❌ 读取饿了么数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def clean_data(df, mapping):
    """清洗和转换数据"""
    print(f"\n🔄 正在清洗数据...")

    # 重命名列（中文 -> 英文）
    df = df.rename(columns=mapping)
    print(f"✅ 已映射 {len(mapping)} 个列名")

    # 确保日期格式正确
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date

    # 添加导入时间
    df['import_time'] = datetime.now()

    # 处理空值
    print("🔄 正在处理空值...")
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)

    # 处理数值字段
    print("🔄 正在处理数值字段...")
    exclude_columns = {'date', 'brand_store_name', 'platform', 'platform_store_name', 'import_time', 'city', 'province', 'district', 'store_id'}
    numeric_fields = [col for col in df.columns if col not in exclude_columns and col in mapping.values()]

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

def import_to_database(df, db_columns):
    """导入数据到数据库"""
    print(f"\n💾 正在导入数据库...")

    try:
        engine = get_engine()

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
    print("🍔 平台源数据导入工具")
    print("="*60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # 步骤1: 测试数据库连接
    if not test_database():
        print("\n❌ 无法连接数据库，程序退出")
        sys.exit(1)

    # 获取数据库列名
    db_columns = get_db_columns()

    # 步骤2: 读取各平台数据
    all_data = []

    # 京东
    df_jd, mapping_jd = read_jd_file('下载源文件/门店_20260112_20260118_jd_szsxxqc_2026-02-10 16_17_24.xlsx')
    if df_jd is not None:
        df_jd = clean_data(df_jd, mapping_jd)
        all_data.append(('京东', df_jd))

    # 美团
    df_mt, mapping_mt = read_meituan_file('下载源文件/门店_全部门店_20260112_20260118_PPZH2669_2026-02-10+16_16_14.csv')
    if df_mt is not None:
        df_mt = clean_data(df_mt, mapping_mt)
        all_data.append(('美团', df_mt))

    # 饿了么
    df_el, mapping_el = read_eleme_file('下载源文件/门店下载_20260112至20260118_全部门店_5296290467_20260210161649743.xlsx')
    if df_el is not None:
        df_el = clean_data(df_el, mapping_el)
        all_data.append(('饿了么', df_el))

    if not all_data:
        print("\n❌ 没有成功读取任何数据，程序退出")
        sys.exit(1)

    # 步骤3: 导入数据
    total_imported = 0
    for platform, df in all_data:
        print(f"\n{'='*60}")
        print(f"📤 导入 {platform} 数据")
        print(f"{'='*60}")
        if import_to_database(df, db_columns):
            total_imported += len(df)

    # 完成
    print("\n" + "="*60)
    print("🎉 导入完成！")
    print("="*60)
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n📊 数据统计:")
    print(f"   总记录数: {total_imported:,}")

    # 平台分布
    print(f"\n   平台分布:")
    for platform, df in all_data:
        print(f"      {platform:6s}: {len(df):,} 条 ({len(df)/total_imported*100:.1f}%)")

    # 查询数据库验证
    print(f"\n🔍 验证数据库记录...")
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) as count FROM daily_orders"))
        count = result.fetchone()[0]
        print(f"   数据库中共有 {count:,} 条记录")

        # 按平台统计
        result = conn.execute(text("SELECT platform, COUNT(*) as count FROM daily_orders GROUP BY platform"))
        print(f"\n   数据库平台分布:")
        for row in result:
            print(f"      {row[0]:6s}: {row[1]:,} 条")

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