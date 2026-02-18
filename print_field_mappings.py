#!/usr/bin/env python3
"""
打印ETL系统的字段映射关系
"""
from etl.core.field_mapping import FIELD_MAPPING, FIELD_TYPES

print('='*100)
print('ETL系统字段映射关系')
print('='*100)

# 打印每个平台的映射
for platform in ['meituan', 'eleme', 'jd']:
    platform_name = {
        'meituan': '美团',
        'eleme': '饿了么',
        'jd': '京东'
    }[platform]
    
    print(f'\n{"="*100}')
    print(f'【{platform_name}】字段映射')
    print(f'{"="*100}')
    
    mappings = FIELD_MAPPING[platform]
    
    # 按字段分类打印
    categories = {
        '基础信息字段': ['date', 'brand_store_name', 'platform_store_name', 'store_id', 'city'],
        '财务指标字段': ['actual_income', 'expense', 'turnover', 'net_margin_rate', 'original_price', 
                      'packaging_fee', 'customer_delivery_fee', 'customer_paid', 'avg_paid_price',
                      'activity_subsidy', 'platform_service_fee', 'real_actual_income', 
                      'promotion_cost', 'gift_sausage_cost', 'real_net_margin_rate'],
        '订单数量字段': ['valid_orders', 'invalid_orders', 'merchant_cancelled_orders'],
        '转化率字段': ['merchant_cancellation_rate', 'store_entry_rate', 'order_conversion_rate',
                     'new_customer_entry_rate', 'new_customer_order_rate', 
                     'old_customer_entry_rate', 'old_customer_order_rate', 'repurchase_rate'],
        '流量数据字段': ['exposure_count', 'entry_count', 'exposure_new_customer', 
                      'entry_new_customer', 'exposure_old_customer', 'entry_old_customer',
                      'exposure_times', 'entry_times', 'order_people', 
                      'order_new_customer', 'order_old_customer', 'uv'],
        '评分字段': ['store_score', 'peak_duration_score', 'quality_product_rate_score',
                   'activity_richness_score', 'reject_order_rate_score', 
                   'bad_review_reply_rate_score', 'online_reply_rate_score',
                   'new_merchant_score', 'menu_richness_score', 
                   'decoration_richness_score', 'service_function_score',
                   'product_quality_score', 'service_experience_score',
                   'product_satisfaction', 'packaging_satisfaction'],
        '指标得分字段': ['repurchase_rate_score', 'message_reply_rate_score',
                      'service_negative_feedback_score', 'food_safety_negative_feedback_score'],
        '回复率字段': ['five_min_reply_rate', 'one_min_reply_rate', 'message_reply_rate',
                      'food_safety_negative_feedback_rate'],
        '时间字段': ['basic_duration'],
        '完成率字段': ['meal_completion_report_rate']
    }
    
    for category, fields in categories.items():
        # 只打印该平台有的字段
        platform_fields = [f for f in fields if f in mappings]
        if not platform_fields:
            continue
            
        print(f'\n┌─ {category} ({len(platform_fields)}个) ─' + '─'*40)
        print(f'│ {"MySQL字段名":<30} {"Excel列名":<35} {"数据类型"}')
        print(f'│ {"-"*30} {"-"*35} {"-"*15}')
        
        for field in sorted(platform_fields):
            excel_column = mappings[field]
            field_type = FIELD_TYPES.get(field, '未知')
            
            # 格式化输出
            if excel_column is None:
                excel_column = '(需通过映射表获取)' if field == 'brand_store_name' else '(无对应列)'
                excel_column = f'\033[90m{excel_column}\033[0m'  # 灰色
            
            # 数据类型颜色
            type_colors = {
                'date': '\033[94m',      # 蓝色
                'str': '\033[92m',       # 绿色
                'decimal': '\033[93m',    # 黄色
                'int': '\033[95m',       # 紫色
                'datetime': '\033[96m'    # 青色
            }
            color = type_colors.get(field_type.split('(')[0] if '(' in field_type else field_type, '')
            type_display = f'{color}{field_type}\033[0m' if color else field_type
            
            print(f'│ {field:<30} {excel_column:<35} {type_display}')
        
        print(f'└{"─"*84}')

# 打印字段数据类型映射
print(f'\n{"="*100}')
print('【字段数据类型映射】')
print(f'{"="*100}')

type_categories = {
    '日期类型': ['date'],
    '字符串类型': ['brand_store_name', 'platform_store_name', 'platform'],
    '金额类型（Decimal）': ['actual_income', 'expense', 'turnover', 'net_margin_rate', 'original_price',
                         'packaging_fee', 'customer_delivery_fee', 'customer_paid', 'avg_paid_price',
                         'activity_subsidy', 'platform_service_fee', 'real_actual_income',
                         'promotion_cost', 'gift_sausage_cost', 'real_net_margin_rate'],
    '整数类型': ['valid_orders', 'invalid_orders', 'merchant_cancelled_orders', 'exposure_count',
                'entry_count', 'exposure_new_customer', 'entry_new_customer', 
                'exposure_old_customer', 'entry_old_customer', 'exposure_times', 
                'entry_times', 'order_people', 'order_new_customer', 
                'order_old_customer', 'uv'],
    '百分比类型（Decimal）': ['merchant_cancellation_rate', 'store_entry_rate', 'order_conversion_rate',
                            'new_customer_entry_rate', 'new_customer_order_rate', 
                            'old_customer_entry_rate', 'old_customer_order_rate', 'repurchase_rate',
                            'five_min_reply_rate', 'one_min_reply_rate', 'message_reply_rate',
                            'food_safety_negative_feedback_rate', 'meal_completion_report_rate'],
    '评分类型（Decimal）': ['store_score', 'peak_duration_score', 'quality_product_rate_score',
                          'activity_richness_score', 'reject_order_rate_score',
                          'bad_review_reply_rate_score', 'online_reply_rate_score',
                          'new_merchant_score', 'menu_richness_score',
                          'decoration_richness_score', 'service_function_score',
                          'product_quality_score', 'service_experience_score',
                          'product_satisfaction', 'packaging_satisfaction',
                          'repurchase_rate_score', 'message_reply_rate_score',
                          'service_negative_feedback_score', 'food_safety_negative_feedback_score'],
    '时长类型（Decimal）': ['basic_duration'],
    '系统字段': ['import_time']
}

for category, fields in type_categories.items():
    print(f'\n┌─ {category} ({len(fields)}个) ─' + '─'*50)
    for field in sorted(fields):
        field_type = FIELD_TYPES.get(field, '未知')
        print(f'│ {field:<45} → {field_type}')
    print(f'└{"─"*68}')

print('\n' + '='*100)
print('映射说明：')
print('='*100)
print('• MySQL字段名：数据库表中的字段名（daily_orders表）')
print('• Excel列名：源数据Excel文件中的列名')
print('• 数据类型：字段的数据类型，用于数据导入时的类型转换')
print('• (需通过映射表获取)：该字段需要通过store_mapping表获取')
print('• (无对应列)：该字段在源数据中不存在')
print('='*100)