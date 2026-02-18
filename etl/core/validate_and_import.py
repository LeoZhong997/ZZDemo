#!/usr/bin/env python3
"""
下载源数据导入ETL系统并逐列校验
支持：美团、饿了么、京东三个平台
"""
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import sys
import numpy as np

# ========== 数据库配置（使用统一配置）==========
from ..config import DB_CONFIG, get_connection_string

# ========== 列名映射：中文列名 -> 英文字段名 ==========
COLUMN_MAPPING = {
    # 基础信息
    '日期': 'date',
    '品牌门店名称': 'brand_store_name',
    '平台': 'platform',
    '平台门店名称': 'platform_store_name',
    
    # 财务指标
    '商家实收': 'actual_income',
    '收入': 'actual_income',
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

# 数据质量校验类
class DataValidator:
    """数据质量校验器"""
    
    def __init__(self, df, platform):
        self.df = df
        self.platform = platform
        self.issues = []
        self.warnings = []
        
    def validate_column(self, col_name, col_type='numeric'):
        """校验单列"""
        issues = []
        col_data = self.df[col_name]
        
        if col_data.isnull().all():
            issues.append(f"   ⚠️  列完全为空")
        else:
            # 检查空值比例
            null_ratio = col_data.isnull().sum() / len(col_data)
            if null_ratio > 0.1:
                issues.append(f"   ⚠️  空值率过高: {null_ratio*100:.1f}%")
            
            if col_type == 'numeric':
                # 检查是否为数值类型
                non_numeric = col_data.apply(lambda x: isinstance(x, str))
                if non_numeric.sum() > 0:
                    issues.append(f"   ⚠️  包含{non_numeric.sum()}个非数值字符串")
                    samples = non_numeric.dropna().head(3).tolist()
                    for sample in samples:
                        issues.append(f"      示例: {sample}")
            
            # 检查异常值
            if col_type == 'numeric':
                try:
                    q1 = col_data.quantile(0.25)
                    q3 = col_data.quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                    if len(outliers) > 0:
                        issues.append(f"   ⚠️  发现{len(outliers)}个异常值（超出IQR范围）")
                        if len(outliers) <= 5:
                            for idx, val in outliers.head(5).items():
                                issues.append(f"      异常值: {val}")
                except Exception as e:
                    issues.append(f"   ⚠️  异常值检查失败: {e}")
            
            return issues
    
    def validate_all(self):
        """执行所有校验"""
        print(f"\n{'='*60}")
        print(f"🔍 数据质量校验 - {self.platform}")
        print(f"{'='*60}")
        
        # 必需列校验
        required_columns = ['date', 'platform', 'brand_store_name']
        for col in required_columns:
            if col not in self.df.columns:
                self.issues.append(f"❌ 缺少必需列: {col}")
        
        # 逐列校验
        for col in self.df.columns:
            col_issues = []
            
            # 日期列校验
            if '日期' in col or col == 'date':
                try:
                    if not pd.to_datetime(self.df[col], errors='coerce').isnull().all():
                        invalid_dates = pd.to_datetime(self.df[col], errors='coerce').isnull().sum()
                        if invalid_dates > 0:
                            col_issues.append(f"   ⚠️  包含{invalid_dates}个无效日期")
                except:
                    col_issues.append(f"   ⚠️ 日期格式异常")
            
            # 金额列校验
            elif any(keyword in col for keyword in ['实收', '收入', '支出', '营业额', '金额', '金额', '费', '补贴', '花费', '成本']):
                if self.df[col].dtype != 'object':
                    col_issues.extend(self.validate_column(col, 'numeric'))
            
            # 订单量列校验
            elif any(keyword in col for keyword in ['订单', '人数', '次数', '单量', '曝光', '入店', '下单']):
                if self.df[col].dtype != 'object':
                    col_issues.extend(self.validate_column(col, 'numeric'))
            
            # 百分比列校验
            elif '率' in col or '转化' in col or '比' in col:
                if self.df[col].dtype != 'object':
                    # 检查是否在合理范围（0-100）
                    numeric_values = pd.to_numeric(self.df[col], errors='coerce')
                    out_of_range = numeric_values[(numeric_values < 0) | (numeric_values > 100)]
                    if len(out_of_range) > 0:
                        col_issues.append(f"   ⚠️  包含{len(out_of_range)}个超出0-100%范围的值")
            
            if col_issues:
                self.warnings.append(f"\n📋 列: {col}")
                for issue in col_issues:
                    self.warnings.append(issue)
                    print(issue)
        
        # 平台名称校验
        if 'platform' in self.df.columns:
            unique_platforms = self.df['platform'].unique()
            print(f"\n🏪 平台值: {list(unique_platforms)}")
            
            # 检查是否有异常平台值
            valid_platforms = ['美团', '饿了么', '京东', 'meituan', 'eleme', 'jd']
            for platform in unique_platforms:
                if platform not in valid_platforms:
                    self.issues.append(f"❌ 异常平台值: {platform}")
        
        return self.issues, self.warnings


def get_engine():
    """创建数据库连接"""
    return create_engine(get_connection_string(), pool_size=5, max_overflow=10, pool_recycle=3600)


def load_and_validate_file(file_path, platform, file_type='xlsx'):
    """加载并校验单个文件"""
    print(f"\n{'='*70}")
    print(f"📄 处理文件: {file_path}")
    print(f"🏪 平台: {platform}")
    print(f"{'='*70}")
    
    try:
        # 读取数据
        if file_type == 'xlsx':
            xls = pd.ExcelFile(file_path)
            sheet_name = xls.sheet_names[0]
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:  # CSV
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'gb18030']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"   ✅ 使用编码: {encoding}")
                    break
                except:
                    if encoding == 'gb18030':
                        raise
                    continue
            else:
                df = pd.read_csv(file_path, encoding='utf-8', error_bad_lines=False)
        
        print(f"   ✅ 数据读取成功: {len(df)} 行, {len(df.columns)} 列")
        print(f"   📅 日期范围: {df.iloc[:, 0:1].min()} ~ {df.iloc[:, 0:1].max()}")
        
        # 执行数据质量校验
        validator = DataValidator(df, platform)
        issues, warnings = validator.validate_all()
        
        return df, issues, warnings
        
    except Exception as e:
        error_msg = f"❌ 文件处理失败: {e}"
        print(error_msg)
        return None, [error_msg], []


def clean_and_import(df, platform):
    """清洗并导入数据到数据库"""
    print(f"\n{'='*60}")
    print(f"🔄 清洗数据")
    print(f"{'='*60}")
    
    try:
        # 重命名列
        df = df.rename(columns=COLUMN_MAPPING)
        print(f"   ✅ 列名映射完成")
        
        # 确保日期格式
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        # 添加平台标识
        if 'platform' not in df.columns:
            df['platform'] = platform
        
        # 清洗数值列
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 清洗百分比列
        percentage_cols = [col for col in df.columns if ('率' in str(col) or '转化' in str(col))]
        for col in percentage_cols:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace('%', '').replace(',', '').replace('nan', '0').replace('NaN', '0').replace('c', '0').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 添加导入时间
        df['import_time'] = datetime.now()
        
        print(f"   ✅ 数据清洗完成")
        
        # 获取数据库列名
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("DESCRIBE daily_orders"))
            db_columns = set(row[0] for row in result)
        
        # 只保留数据库存在的列
        df_columns = set(df.columns)
        final_columns = list(df_columns & db_columns)
        df_to_import = df[final_columns]
        
        if len(final_columns) < len(df.columns):
            removed = list(df_columns - db_columns)
            print(f"   ⚠️  跳过{len(removed)}个数据库不存在的列: {', '.join(removed[:5])}...")
        
        # 导入数据库
        print(f"\n💾 导入数据库...")
        df_to_import.to_sql(
            name='daily_orders',
            con=engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        print(f"   ✅ 导入完成: {len(df_to_import)} 条记录")
        return True
        
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("="*70)
    print("🍔 下载源数据导入与校验系统")
    print("="*70)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 源文件目录: 下载源文件")
    
    total_imported = 0
    total_issues = 0
    total_warnings = 0
    
    all_platforms_results = []
    
    # 定义文件映射
    file_mapping = [
        {
            'file': '门店_20260112_20260118_jd_szsxxqc_2026-02-10 16_17_24.xlsx',
            'platform': '京东',
            'type': 'xlsx'
        },
        {
            'file': '门店_全部门店_20260112_20260118_PPZH2669_2026-02-10+16_16_14.csv',
            'platform': '饿了么',
            'type': 'csv'
        },
        {
            'file': '门店下载_20260112至20260118_全部门店_5296290467_20260210161649743.xlsx',
            'platform': '美团',
            'type': 'xlsx'
        }
    ]
    
    # 处理每个文件
    for mapping in file_mapping:
        file_path = f"下载源文件/{mapping['file']}"
        platform = mapping['platform']
        file_type = mapping['type']
        
        df, issues, warnings = load_and_validate_file(file_path, platform, file_type)

        if df is None:
            all_platforms_results.append({
                'platform': platform,
                'file': mapping['file'],
                'rows': 0,
                'issues': issues,
                'warnings': warnings,
                'success': False
            })
            continue

        all_platforms_results.append({
            'platform': platform,
            'file': mapping['file'],
            'rows': len(df),
            'issues': issues,
            'warnings': warnings,
            'success': False
        })

        # 导入数据
        success = clean_and_import(df, platform)

        all_platforms_results[-1]['success'] = success
        if success:
            total_imported += len(df)
        total_issues += len(issues)
        total_warnings += len(warnings)
    
    # 生成最终报告
    print(f"\n{'='*70}")
    print(f"📊 最终报告")
    print(f"{'='*70}")
    
    print(f"\n✅ 总体统计:")
    print(f"   总文件数: {len(file_mapping)}")
    print(f"   成功导入: {sum(1 for r in all_platforms_results if r['success'])}/{len(file_mapping)} 个平台")
    print(f"   总记录数: {total_imported:,}")
    print(f"   总问题数: {total_issues}")
    print(f"   总警告数: {total_warnings}")
    
    # 平台详细报告
    print(f"\n🏪 平台详细报告:")
    for result in all_platforms_results:
        status = "✅ 成功" if result['success'] else "❌ 失败"
        print(f"\n   {result['platform']}: {status}")
        print(f"      文件: {result['file']}")
        print(f"      记录数: {result['rows']}")
        print(f"      问题数: {len(result['issues'])}")
        print(f"      警告数: {len(result['warnings'])}")
        
        if result['warnings']:
            print(f"\n      警告详情（前10条）:")
            for warning in result['warnings'][:10]:
                print(f"         {warning}")
        
        if result['issues']:
            print(f"\n      问题详情:")
            for issue in result['issues']:
                print(f"         {issue}")
    
    # 数据库验证
    print(f"\n🔍 数据库验证:")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as total, COUNT(DISTINCT CONCAT(date, '-', platform)) as unique_daily FROM daily_orders"))
            row = result.fetchone()
            total = row[0]
            unique_daily = row[1]
            print(f"   总记录数: {total:,}")
            print(f"   唯一日记录数: {unique_daily:,}")
            
            # 按平台统计
            result = conn.execute(text("SELECT platform, COUNT(*) as count FROM daily_orders GROUP BY platform"))
            platform_counts = result.fetchall()
            print(f"\n   数据库平台分布:")
            for platform, count in platform_counts:
                print(f"      {platform[0]:10s}: {count:,} 条")
    except Exception as e:
        print(f"   ❌ 数据库验证失败: {e}")
    
    print(f"\n{'='*70}")
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")


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