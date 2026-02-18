#!/usr/bin/env python3
"""
检查外卖源数据.xlsx文件的结构和内容
"""
import pandas as pd

print('='*80)
print('检查外卖源数据.xlsx文件')
print('='*80)

file_path = 'etl/data/sources/目标源数据/外卖源数据.xlsx'

# 读取文件
try:
    # 读取所有sheet
    xls = pd.ExcelFile(file_path)
    print(f'\n📄 文件: {file_path}')
    print(f'📊 Sheet列表: {xls.sheet_names}')
    
    # 读取第一个sheet
    df = pd.read_excel(file_path, sheet_name=0)
    print(f'\n📋 第一个sheet统计:')
    print(f'   行数: {len(df)}')
    print(f'   列数: {len(df.columns)}')
    print(f'\n   列名: {list(df.columns)}')
    
    # 检查日期列
    date_cols = [col for col in df.columns if '日期' in str(col) or 'date' in str(col).lower()]
    print(f'\n📅 日期相关列: {date_cols}')
    
    if date_cols:
        date_col = date_cols[0]
        print(f'\n📅 {date_col}列统计:')
        print(f'   数据类型: {df[date_col].dtype}')
        print(f'   唯一日期数: {df[date_col].nunique()}')
        print(f'   日期范围: {df[date_col].min()} 至 {df[date_col].max()}')
        print(f'\n   所有唯一日期:')
        for date in sorted(df[date_col].unique()):
            count = len(df[df[date_col] == date])
            print(f'      {date}: {count}条')
    
    # 检查平台列
    platform_cols = [col for col in df.columns if '平台' in str(col) or 'platform' in str(col).lower()]
    print(f'\n🏪 平台相关列: {platform_cols}')
    
    if platform_cols:
        platform_col = platform_cols[0]
        print(f'\n🏪 {platform_col}列统计:')
        print(f'   唯一平台: {df[platform_col].unique()}')
    
    # 显示前5行数据
    print(f'\n📄 前5行数据预览:')
    print(df.head(5).to_string())
    
except Exception as e:
    print(f'\n❌ 读取文件失败: {e}')
    import traceback
    traceback.print_exc()