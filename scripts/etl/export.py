#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL 数据导出脚本

功能：
    - 导出数据到 Excel 文件

使用方法：
    python scripts/etl/export.py --start 2026-01-11 --end 2026-01-18
    python scripts/etl/export.py --output report.xlsx
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
from sqlalchemy import create_engine, text
from etl.config import get_connection_string, TABLE_NAME


def export_to_excel(start_date: str = None, end_date: str = None, output_file: str = None):
    """导出数据到 Excel"""
    print("=" * 60)
    print("📤 数据导出")
    print("=" * 60)
    
    engine = create_engine(get_connection_string(), echo=False)
    
    # 构建查询
    query = f"SELECT * FROM {TABLE_NAME}"
    params = {}
    
    if start_date and end_date:
        query += " WHERE date BETWEEN :start_date AND :end_date"
        params = {'start_date': start_date, 'end_date': end_date}
        print(f"\n📅 日期范围: {start_date} 至 {end_date}")
    
    query += " ORDER BY date, platform, brand_store_name"
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)
    
    print(f"📊 查询到 {len(df)} 条记录")
    
    if len(df) == 0:
        print("⚠️  没有数据可导出")
        return
    
    # 生成输出文件名
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(project_root, 'etl', 'data', 'exports', f'daily_orders_{timestamp}.xlsx')
    
    # 确保目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 导出到 Excel
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"✅ 导出完成: {output_file}")
    print(f"   文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")


def main():
    parser = argparse.ArgumentParser(description='ETL 数据导出工具')
    
    parser.add_argument('--start', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    export_to_excel(args.start, args.end, args.output)


if __name__ == '__main__':
    main()