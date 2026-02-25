"""
导出 daily_orders 表数据到 Excel 文件
"""
import os
import sys
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from etl.config import get_connection_string, TABLE_NAME

# 导出目录
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'exports')

def export_to_excel():
    """导出 daily_orders 表到 Excel"""
    # 确保导出目录存在
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'daily_orders_export_{timestamp}.xlsx'
    filepath = os.path.join(EXPORT_DIR, filename)
    
    print(f"正在连接数据库...")
    engine = create_engine(get_connection_string())
    
    print(f"正在查询 {TABLE_NAME} 表...")
    query = f"SELECT * FROM {TABLE_NAME} ORDER BY date DESC, platform, brand_store_name"
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    
    print(f"查询到 {len(df)} 条记录")
    
    # 导出到 Excel
    print(f"正在导出到 {filepath}...")
    df.to_excel(filepath, index=False, engine='openpyxl')
    
    print(f"✅ 导出成功！")
    print(f"   文件路径: {filepath}")
    print(f"   记录数: {len(df)}")
    print(f"   文件大小: {os.path.getsize(filepath) / 1024:.2f} KB")
    
    return filepath

if __name__ == '__main__':
    export_to_excel()