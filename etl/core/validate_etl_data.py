"""
ETL数据验证脚本
验证2026-01-11到2026-01-18期间ETL导入数据的正确性
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# 导入config模块
from ..config import DB_CONFIG, get_connection_string, TABLE_NAME

# 验证配置
TARGET_START_DATE = '2026-01-11'
TARGET_END_DATE = '2026-01-18'
PREV_WEEK_START = '2026-01-04'
PREV_WEEK_END = '2026-01-10'

# 关键指标列表
KEY_METRICS = [
    'valid_orders', 'actual_income', 'turnover', 'exposure_count', 
    'entry_count', 'store_entry_rate', 'order_conversion_rate',
    'avg_paid_price', 'actual_income'
]

# 数值字段列表
NUMERIC_FIELDS = [
    'actual_income', 'expense', 'turnover', 'original_price', 'packaging_fee',
    'customer_delivery_fee', 'customer_paid', 'avg_paid_price', 'activity_subsidy',
    'platform_service_fee', 'valid_orders', 'invalid_orders', 'merchant_cancelled_orders',
    'exposure_count', 'entry_count', 'exposure_new_customer', 'entry_new_customer',
    'exposure_old_customer', 'entry_old_customer', 'exposure_times', 'entry_times',
    'order_people', 'order_new_customer', 'order_old_customer', 'uv'
]

# 百分比字段列表（应该在0-100之间）
PERCENTAGE_FIELDS = [
    'merchant_cancellation_rate', 'store_entry_rate', 'order_conversion_rate',
    'new_customer_entry_rate', 'new_customer_order_rate', 'old_customer_entry_rate',
    'old_customer_order_rate', 'repurchase_rate', 'five_min_reply_rate',
    'one_min_reply_rate', 'message_reply_rate', 'service_negative_feedback_rate',
    'food_safety_negative_feedback_rate', 'meal_completion_report_rate',
    'net_margin_rate', 'real_net_margin_rate'
]


def create_database_engine():
    """创建数据库连接引擎"""
    engine = create_engine(
        get_connection_string(),
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )
    return engine


def query_data(engine, start_date, end_date):
    """查询指定日期范围的数据"""
    query = text(f"""
        SELECT * FROM {TABLE_NAME}
        WHERE date BETWEEN :start_date AND :end_date
        ORDER BY date, platform, brand_store_name
    """)
    
    df = pd.read_sql(query, engine, params={'start_date': start_date, 'end_date': end_date})
    return df


def validate_completeness(target_df, prev_week_df):
    """验证数据完整性"""
    print("\n" + "="*60)
    print("📊 1. 数据完整性验证")
    print("="*60)
    
    results = {
        'status': '✅ 通过',
        'details': {},
        'issues': []
    }
    
    # 1.1 记录数检查
    total_records = len(target_df)
    prev_records = len(prev_week_df) if not prev_week_df.empty else 0
    
    results['details']['总记录数'] = {
        '当前周': total_records,
        '上一周': prev_records,
        '变化': total_records - prev_records
    }
    
    print(f"\n📋 记录数统计:")
    print(f"   当前周 (2026-01-11 到 2026-01-18): {total_records} 条")
    print(f"   上一周 (2026-01-04 到 2026-01-10): {prev_records} 条")
    print(f"   变化: {total_records - prev_records:+d} 条")
    
    # 1.2 日期范围验证
    dates_in_data = sorted(target_df['date'].unique())
    expected_dates = pd.date_range(start=TARGET_START_DATE, end=TARGET_END_DATE).date
    
    missing_dates = set(expected_dates) - set(dates_in_data)
    extra_dates = set(dates_in_data) - set(expected_dates)
    
    results['details']['日期覆盖'] = {
        '预期日期': [str(d) for d in expected_dates],
        '实际日期': [str(d) for d in dates_in_data],
        '缺失日期': [str(d) for d in sorted(missing_dates)] if missing_dates else [],
        '多余日期': [str(d) for d in sorted(extra_dates)] if extra_dates else []
    }
    
    print(f"\n📅 日期覆盖检查:")
    print(f"   预期日期: {len(expected_dates)} 天")
    print(f"   实际覆盖: {len(dates_in_data)} 天")
    
    if missing_dates:
        print(f"   ⚠️  缺失日期: {', '.join([str(d) for d in sorted(missing_dates)])}")
        results['issues'].append(f"缺失日期: {', '.join([str(d) for d in sorted(missing_dates)])}")
        results['status'] = '⚠️ 有问题'
    
    if extra_dates:
        print(f"   ⚠️  多余日期: {', '.join([str(d) for d in sorted(extra_dates)])}")
        results['issues'].append(f"多余日期: {', '.join([str(d) for d in sorted(extra_dates)])}")
        results['status'] = '⚠️ 有问题'
    
    # 1.3 平台覆盖验证
    platforms_in_data = target_df['platform'].unique()
    results['details']['平台分布'] = {}
    
    print(f"\n🏢 平台分布:")
    for platform in ['美团', '饿了么', '京东']:
        count = len(target_df[target_df['platform'] == platform])
        percentage = count / total_records * 100 if total_records > 0 else 0
        print(f"   {platform}: {count} 条 ({percentage:.2f}%)")
        results['details']['平台分布'][platform] = {
            '记录数': count,
            '占比': round(percentage, 2)
        }
    
    # 1.4 门店数据验证
    stores_per_platform = target_df.groupby('platform')['brand_store_name'].nunique()
    results['details']['门店数量'] = {}
    
    print(f"\n🏪 门店数量:")
    for platform in ['美团', '饿了么', '京东']:
        store_count = stores_per_platform.get(platform, 0)
        print(f"   {platform}: {store_count} 家门店")
        results['details']['门店数量'][platform] = store_count
    
    # 1.5 每日数据分布
    daily_counts = target_df.groupby('date').size()
    results['details']['每日记录数'] = {str(k): v for k, v in daily_counts.items()}
    
    print(f"\n📆 每日记录分布:")
    for date, count in sorted(daily_counts.items()):
        print(f"   {date}: {count} 条")
    
    return results


def validate_data_quality(target_df):
    """验证数据质量"""
    print("\n" + "="*60)
    print("🔍 2. 数据质量验证")
    print("="*60)
    
    results = {
        'status': '✅ 通过',
        'details': {},
        'issues': []
    }
    
    # 2.1 空值检查
    null_stats = {}
    for col in target_df.columns:
        null_count = target_df[col].isnull().sum()
        null_pct = null_count / len(target_df) * 100
        if null_count > 0:
            null_stats[col] = {
                '空值数量': int(null_count),
                '空值占比': round(null_pct, 2)
            }
    
    results['details']['空值统计'] = null_stats
    
    if null_stats:
        print(f"\n⚠️  发现空值字段 (前10个):")
        for col, stats in list(null_stats.items())[:10]:
            print(f"   {col}: {stats['空值数量']} 个空值 ({stats['空值占比']}%)")
    else:
        print(f"\n✅ 无空值")
    
    # 2.2 异常值检查 - 数值字段
    print(f"\n📊 数值字段异常值检查:")
    
    numeric_issues = []
    for field in NUMERIC_FIELDS:
        if field in target_df.columns:
            # 检查负数
            negative_count = (target_df[field] < 0).sum()
            if negative_count > 0:
                issue = f"{field} 有 {negative_count} 个负数值"
                print(f"   ⚠️  {issue}")
                numeric_issues.append(issue)
    
    results['details']['数值异常'] = numeric_issues
    
    if numeric_issues:
        results['issues'].extend(numeric_issues)
        results['status'] = '⚠️ 有问题'
    
    # 2.3 百分比字段验证 (应该在0-100之间)
    print(f"\n📈 百分比字段验证:")
    
    percentage_issues = []
    for field in PERCENTAGE_FIELDS:
        if field in target_df.columns:
            # 排除空值后检查
            non_null_values = target_df[field].dropna()
            if len(non_null_values) > 0:
                out_of_range = non_null_values[(non_null_values < 0) | (non_null_values > 100)]
                if len(out_of_range) > 0:
                    issue = f"{field} 有 {len(out_of_range)} 个值超出0-100范围"
                    print(f"   ⚠️  {issue}")
                    percentage_issues.append(issue)
                else:
                    print(f"   ✅ {field}: 正常")
    
    results['details']['百分比异常'] = percentage_issues
    
    if percentage_issues:
        results['issues'].extend(percentage_issues)
        results['status'] = '⚠️ 有问题'
    
    # 2.4 重复数据验证
    print(f"\n🔄 重复数据检查:")
    
    # 检查是否存在重复的 (date, platform, brand_store_name) 组合
    key_columns = ['date', 'platform', 'brand_store_name']
    duplicates = target_df.duplicated(subset=key_columns, keep=False)
    duplicate_count = duplicates.sum()
    
    if duplicate_count > 0:
        print(f"   ⚠️  发现 {duplicate_count} 条重复记录")
        results['details']['重复记录'] = duplicate_count
        results['issues'].append(f"发现 {duplicate_count} 条重复记录")
        results['status'] = '⚠️ 有问题'
        
        # 显示重复的记录
        duplicate_records = target_df[duplicates].sort_values(key_columns)
        print(f"   重复记录示例 (前5条):")
        for idx, row in duplicate_records.head(5).iterrows():
            print(f"      {row['date']} | {row['platform']} | {row['brand_store_name']}")
    else:
        print(f"   ✅ 无重复记录")
        results['details']['重复记录'] = 0
    
    return results


def validate_week_over_week(target_df, prev_week_df):
    """周环比对比分析"""
    print("\n" + "="*60)
    print("📈 3. 周环比对比分析")
    print("="*60)
    
    results = {
        'status': '✅ 通过',
        'details': {},
        'issues': [],
        'anomalies': []
    }
    
    if prev_week_df.empty:
        print("\n⚠️  上一周无数据，无法进行周环比对比")
        results['issues'].append("上一周无数据，无法进行周环比对比")
        return results
    
    # 3.1 整体指标对比
    print(f"\n📊 整体指标对比:")
    
    for metric in KEY_METRICS:
        if metric in target_df.columns and metric in prev_week_df.columns:
            current_sum = target_df[metric].sum()
            prev_sum = prev_week_df[metric].sum()
            
            if prev_sum != 0:
                change_rate = ((current_sum - prev_sum) / prev_sum) * 100
                symbol = "📈" if change_rate > 0 else "📉"
                print(f"   {metric}:")
                print(f"      上一周: {prev_sum:,.2f}")
                print(f"      当前周: {current_sum:,.2f}")
                print(f"      变化率: {symbol} {change_rate:+.2f}%")
                
                results['details'][metric] = {
                    '上一周': float(prev_sum),
                    '当前周': float(current_sum),
                    '变化率': round(change_rate, 2)
                }
                
                # 识别异常波动（超过50%变化）
                if abs(change_rate) > 50 and metric != 'actual_income':
                    anomaly = f"{metric} 变化率 {change_rate:+.2f}% 超过50%"
                    results['anomalies'].append(anomaly)
                    print(f"      ⚠️  注意: {anomaly}")
    
    # 3.2 按平台对比
    print(f"\n🏢 按平台对比:")
    
    for platform in ['美团', '饿了么', '京东']:
        current_platform = target_df[target_df['platform'] == platform]
        prev_platform = prev_week_df[prev_week_df['platform'] == platform]
        
        if len(prev_platform) == 0:
            print(f"   {platform}: 上一周无数据")
            continue
        
        print(f"\n   {platform}:")
        
        for metric in ['valid_orders', 'actual_income']:
            if metric in current_platform.columns:
                current_sum = current_platform[metric].sum()
                prev_sum = prev_platform[metric].sum()
                
                if prev_sum != 0:
                    change_rate = ((current_sum - prev_sum) / prev_sum) * 100
                    symbol = "📈" if change_rate > 0 else "📉"
                    print(f"      {metric}: {symbol} {change_rate:+.2f}%")
    
    # 3.3 门店级别对比（识别异常门店）
    print(f"\n🏪 门店级别对比（识别异常门店）:")
    
    # 合并两周数据
    merged = pd.merge(
        target_df,
        prev_week_df,
        on=['platform', 'brand_store_name'],
        suffixes=('_current', '_prev'),
        how='outer'
    )
    
    # 计算变化率
    for metric in ['valid_orders', 'actual_income']:
        metric_current = f'{metric}_current'
        metric_prev = f'{metric}_prev'
        
        if metric_current in merged.columns and metric_prev in merged.columns:
            merged[f'{metric}_change_rate'] = (
                (merged[metric_current] - merged[metric_prev]) / merged[metric_prev] * 100
            ).round(2)
            
            # 识别变化率超过100%的门店
            anomaly_stores = merged[
                (merged[f'{metric}_change_rate'].abs() > 100) & 
                (merged[f'{metric}_change_rate'].notnull())
            ]
            
            if len(anomaly_stores) > 0:
                print(f"\n   ⚠️  {metric} 变化率超过100%的门店:")
                for idx, row in anomaly_stores.head(10).iterrows():
                    print(f"      {row['platform']} | {row['brand_store_name']}: "
                          f"{row[f'{metric}_change_rate']:+.2f}%")
                    results['anomalies'].append(
                        f"{row['platform']} {row['brand_store_name']} "
                        f"{metric} 变化率 {row[f'{metric}_change_rate']:+.2f}%"
                    )
    
    if results['anomalies']:
        results['status'] = '⚠️ 有问题'
    
    return results


def validate_logic_consistency(target_df):
    """验证数据逻辑一致性"""
    print("\n" + "="*60)
    print("🧮 4. 数据逻辑一致性验证")
    print("="*60)
    
    results = {
        'status': '✅ 通过',
        'details': {},
        'issues': []
    }
    
    # 4.1 验证转化率计算
    print(f"\n📊 转化率验证:")
    
    conversion_checks = [
        ('store_entry_rate', 'entry_count', 'exposure_count'),
        ('order_conversion_rate', 'order_people', 'entry_count')
    ]
    
    for rate_field, numerator_field, denominator_field in conversion_checks:
        if all(col in target_df.columns for col in [rate_field, numerator_field, denominator_field]):
            # 计算期望的转化率
            df_calc = target_df[[rate_field, numerator_field, denominator_field]].copy()
            
            # 排除分母为0的情况
            df_calc = df_calc[df_calc[denominator_field] > 0]
            
            if len(df_calc) > 0:
                df_calc['expected_rate'] = (
                    df_calc[numerator_field] / df_calc[denominator_field] * 100
                ).round(2)
                
                # 允许误差范围
                tolerance = 1.0
                df_calc['difference'] = abs(df_calc[rate_field] - df_calc['expected_rate'])
                
                mismatch_count = (df_calc['difference'] > tolerance).sum()
                total_count = len(df_calc)
                
                print(f"   {rate_field}:")
                print(f"      验证记录数: {total_count}")
                print(f"      不匹配数量: {mismatch_count}")
                
                if mismatch_count > 0:
                    mismatch_pct = mismatch_count / total_count * 100
                    print(f"      不匹配比例: {mismatch_pct:.2f}%")
                    
                    if mismatch_pct > 10:  # 超过10%的不匹配
                        results['issues'].append(
                            f"{rate_field} 有 {mismatch_count}/{total_count} ({mismatch_pct:.2f}%) 条记录计算不一致"
                        )
                        results['status'] = '⚠️ 有问题'
                        
                        # 显示一些不匹配的例子
                        examples = df_calc[df_calc['difference'] > tolerance].head(5)
                        print(f"      不匹配示例:")
                        for idx, row in examples.iterrows():
                            print(f"         记录率: {row[rate_field]}%, 计算率: {row['expected_rate']}%, "
                                  f"{numerator_field}: {row[numerator_field]}, {denominator_field}: {row[denominator_field]}")
                    else:
                        print(f"      ✅ 在可接受范围内")
                else:
                    print(f"      ✅ 完全匹配")
    
    # 4.2 验证订单数量逻辑
    print(f"\n📦 订单数量逻辑验证:")
    
    # 验证有效订单 + 无效订单 >= 有效订单
    if all(col in target_df.columns for col in ['valid_orders', 'invalid_orders']):
        invalid_issue = (target_df['invalid_orders'] < 0).sum()
        if invalid_issue > 0:
            print(f"   ⚠️  无效订单有 {invalid_issue} 个负数值")
            results['issues'].append(f"无效订单有 {invalid_issue} 个负数值")
            results['status'] = '⚠️ 有问题'
        else:
            print(f"   ✅ 无效订单无负值")
    
    return results


def generate_html_report(completeness_results, quality_results, wow_results, logic_results):
    """生成HTML验证报告"""
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETL数据验证报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
        }}
        .section {{
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        .section-header {{
            background: #3498db;
            color: white;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: bold;
        }}
        .section-content {{
            padding: 20px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .status-pass {{
            background: #2ecc71;
            color: white;
        }}
        .status-warning {{
            background: #f39c12;
            color: white;
        }}
        .status-fail {{
            background: #e74c3c;
            color: white;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .metric-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-size: 24px;
            color: #3498db;
            margin-bottom: 5px;
        }}
        .metric-sub {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #ecf0f1;
            font-weight: bold;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .alert {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .alert-danger {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .summary h2 {{
            margin-bottom: 15px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .summary-item {{
            text-align: center;
        }}
        .summary-value {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .summary-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 ETL数据验证报告</h1>
        <p class="subtitle">验证期间: 2026-01-11 至 2026-01-18 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>📋 验证总结</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">4</div>
                    <div class="summary-label">验证维度</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{len(quality_results.get('details', {}).get('空值统计', {}))}</div>
                    <div class="summary-label">空值字段</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{len(wow_results.get('anomalies', []))}</div>
                    <div class="summary-label">异常数据</div>
                </div>
            </div>
        </div>
"""
    
    # 添加各部分的验证结果
    sections = [
        (completeness_results, "数据完整性验证", "1"),
        (quality_results, "数据质量验证", "2"),
        (wow_results, "周环比对比分析", "3"),
        (logic_results, "数据逻辑一致性验证", "4")
    ]
    
    for result, title, num in sections:
        status_class = "status-pass" if result['status'] == '✅ 通过' else "status-warning"
        
        html_content += f"""
        <div class="section">
            <div class="section-header">
                {num}. {title}
                <span class="status-badge {status_class}">{result['status']}</span>
            </div>
            <div class="section-content">
"""
        
        # 添加问题列表
        if result.get('issues'):
            html_content += '<div class="alert alert-danger"><strong>⚠️ 发现问题:</strong><ul>'
            for issue in result['issues']:
                html_content += f'<li>{issue}</li>'
            html_content += '</ul></div>'
        
        # 添加详情
        if result.get('details'):
            html_content += '<div class="metric-grid">'
            for key, value in result['details'].items():
                if isinstance(value, dict):
                    html_content += f"""
                    <div class="metric-card">
                        <div class="metric-title">{key}</div>
"""
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (int, float)):
                            html_content += f'<div style="margin: 5px 0;">{sub_key}: <span style="color: #3498db; font-weight: bold;">{sub_value:,.2f}</span></div>'
                        else:
                            html_content += f'<div style="margin: 5px 0;">{sub_key}: <span style="color: #3498db; font-weight: bold;">{sub_value}</span></div>'
                    
                    html_content += '</div>'
            
            html_content += '</div>'
        
        # 添加异常列表
        if result.get('anomalies'):
            html_content += '<h3 style="margin-top: 20px; color: #e74c3c;">🚨 异常数据列表</h3><ul>'
            for anomaly in result['anomalies']:
                html_content += f'<li>{anomaly}</li>'
            html_content += '</ul>'
        
        html_content += '</div></div>'
    
    html_content += """
    </div>
</body>
</html>
"""
    
    return html_content


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔍 ETL数据验证程序")
    print("="*60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 验证期间: {TARGET_START_DATE} 至 {TARGET_END_DATE}")
    print(f"📊 对比期间: {PREV_WEEK_START} 至 {PREV_WEEK_END}")
    
    # 创建数据库连接
    print(f"\n📡 连接数据库...")
    engine = create_database_engine()
    
    try:
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    # 查询数据
    print(f"\n📊 查询验证期间数据...")
    target_df = query_data(engine, TARGET_START_DATE, TARGET_END_DATE)
    print(f"✅ 查询到 {len(target_df)} 条记录")
    
    print(f"\n📊 查询上一周数据...")
    prev_week_df = query_data(engine, PREV_WEEK_START, PREV_WEEK_END)
    print(f"✅ 查询到 {len(prev_week_df)} 条记录")
    
    # 执行验证
    completeness_results = validate_completeness(target_df, prev_week_df)
    quality_results = validate_data_quality(target_df)
    wow_results = validate_week_over_week(target_df, prev_week_df)
    logic_results = validate_logic_consistency(target_df)
    
    # 生成报告
    print(f"\n📝 生成验证报告...")
    html_report = generate_html_report(
        completeness_results,
        quality_results,
        wow_results,
        logic_results
    )
    
    # 保存报告
    report_path = "etl_validation_report.html"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    print(f"✅ 报告已保存: {report_path}")
    
    # 保存JSON格式的详细结果
    json_results = {
        'validation_time': datetime.now().isoformat(),
        'target_period': {'start': TARGET_START_DATE, 'end': TARGET_END_DATE},
        'comparison_period': {'start': PREV_WEEK_START, 'end': PREV_WEEK_END},
        'total_records': len(target_df),
        'results': {
            'completeness': completeness_results,
            'quality': quality_results,
            'week_over_week': wow_results,
            'logic': logic_results
        }
    }
    
    json_path = "etl_validation_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, ensure_ascii=False, indent=2)
    print(f"✅ 详细结果已保存: {json_path}")
    
    # 输出验证结论
    print(f"\n" + "="*60)
    print(f"📋 验证结论")
    print(f"="*60)
    
    total_issues = (
        len(completeness_results['issues']) +
        len(quality_results['issues']) +
        len(wow_results['issues']) +
        len(logic_results['issues'])
    )
    
    if total_issues == 0:
        print(f"✅ 验证通过！ETL系统工作正常，未发现问题。")
    else:
        print(f"⚠️  发现 {total_issues} 个问题，请查看详细报告。")
        print(f"\n问题汇总:")
        if completeness_results['issues']:
            print(f"   - 数据完整性: {len(completeness_results['issues'])} 个问题")
        if quality_results['issues']:
            print(f"   - 数据质量: {len(quality_results['issues'])} 个问题")
        if wow_results['issues']:
            print(f"   - 周环比对比: {len(wow_results['issues'])} 个问题")
        if logic_results['issues']:
            print(f"   - 逻辑一致性: {len(logic_results['issues'])} 个问题")
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n📄 查看HTML报告: open {report_path}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()