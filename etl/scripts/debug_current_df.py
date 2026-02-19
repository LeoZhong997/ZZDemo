"""
调试脚本：导出与前端 current_df 相同的数据
用于分析"分平台营收趋势"图表问题
"""
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from etl.config import get_connection_string, ALL_PLATFORMS

# 导出目录
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'exports')

def get_data(start_date, end_date, platforms, stores=None):
    """
    与 app.py 中完全相同的查询逻辑
    """
    try:
        engine = create_engine(get_connection_string())
        conditions = []
        params = {}
        conditions.append("date BETWEEN :start_date AND :end_date")
        params['start_date'] = start_date
        params['end_date'] = end_date
        if platforms:
            placeholders = ','.join([f':platform_{i}' for i in range(len(platforms))])
            conditions.append(f"platform IN ({placeholders})")
            for i, platform in enumerate(platforms):
                params[f'platform_{i}'] = platform
        if stores:
            placeholders = ','.join([f':store_{i}' for i in range(len(stores))])
            conditions.append(f"brand_store_name IN ({placeholders})")
            for i, store in enumerate(stores):
                params[f'store_{i}'] = store
        where_clause = ' AND '.join(conditions)
        query = f"""
        SELECT * FROM daily_orders
        WHERE {where_clause}
        ORDER BY date DESC, platform
        """
        print(f"执行的SQL:\n{query}")
        print(f"参数: {params}")
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df
    except Exception as e:
        print(f"数据库查询失败: {e}")
        return pd.DataFrame()

def debug_export():
    """导出 current_df 数据用于调试"""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # 获取数据库最大日期（与前端逻辑相同）
    engine = create_engine(get_connection_string())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MAX(date) as max_date FROM daily_orders"))
        max_date = result.scalar()
    
    if max_date:
        end_date = max_date
        start_date = max_date - timedelta(days=7)
    else:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
    
    print(f"日期范围: {start_date} ~ {end_date}")
    print(f"平台: {ALL_PLATFORMS}")
    print()
    
    # 获取数据
    current_df = get_data(start_date, end_date, ALL_PLATFORMS, stores=None)
    
    if current_df.empty:
        print("❌ 没有查询到数据")
        return
    
    print(f"\n总记录数: {len(current_df)}")
    
    # 导出完整数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(EXPORT_DIR, f'current_df_debug_{timestamp}.xlsx')
    current_df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"\n✅ 完整数据已导出: {filepath}")
    
    # 打印统计信息
    print("\n" + "="*60)
    print("数据统计分析")
    print("="*60)
    
    print(f"\n各平台记录数:")
    print(current_df['platform'].value_counts())
    
    print(f"\n各平台 actual_income 汇总:")
    income_summary = current_df.groupby('platform')['actual_income'].agg(['sum', 'mean', 'count'])
    print(income_summary)
    
    print(f"\n各平台 valid_orders 汇总:")
    orders_summary = current_df.groupby('platform')['valid_orders'].agg(['sum', 'mean', 'count'])
    print(orders_summary)
    
    print(f"\n各平台 turnover 汇总:")
    turnover_summary = current_df.groupby('platform')['turnover'].agg(['sum', 'mean', 'count'])
    print(turnover_summary)
    
    print(f"\n按日期、平台的 actual_income 汇总:")
    pivot_income = current_df.pivot_table(values='actual_income', index='date', columns='platform', aggfunc='sum')
    print(pivot_income)
    
    print(f"\n按日期、平台的 valid_orders 汇总:")
    pivot_orders = current_df.pivot_table(values='valid_orders', index='date', columns='platform', aggfunc='sum')
    print(pivot_orders)
    
    print(f"\n按日期、平台的 turnover 汇总:")
    pivot_turnover = current_df.pivot_table(values='turnover', index='date', columns='platform', aggfunc='sum')
    print(pivot_turnover)
    
    # 检查是否有空值
    print(f"\n各平台 actual_income 空值数量:")
    null_counts_income = current_df.groupby('platform')['actual_income'].apply(lambda x: x.isna().sum())
    print(null_counts_income)
    
    print(f"\n各平台 valid_orders 空值数量:")
    null_counts_orders = current_df.groupby('platform')['valid_orders'].apply(lambda x: x.isna().sum())
    print(null_counts_orders)
    
    print(f"\n各平台 turnover 空值数量:")
    null_counts_turnover = current_df.groupby('platform')['turnover'].apply(lambda x: x.isna().sum())
    print(null_counts_turnover)
    
    # 检查数据类型
    print(f"\n数据类型:")
    print(f"  actual_income: {current_df['actual_income'].dtype}")
    print(f"  valid_orders: {current_df['valid_orders'].dtype}")
    print(f"  turnover: {current_df['turnover'].dtype}")
    
    return filepath

if __name__ == '__main__':
    debug_export()