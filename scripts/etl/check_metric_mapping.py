"""
根据 etl/data/sources/目标源数据/metrics_list.xlsx 的不同数据表指标名称，建议统一的映射关系
以更正etl/core/field_mapping.py的FIELD_MAPPING字典
"""

import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from etl.core.field_mapping import FIELD_MAPPING


def check_metric_mapping():
    """检查并生成字段映射建议"""
    
    # 1. 加载表格 metrics_list.xlsx
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'etl', 'data', 'sources', '目标源数据', 'metrics_list.xlsx'
    )
    
    df = pd.read_excel(excel_path, sheet_name='指标')
    
    # 打印列名以便调试
    print("="*80)
    print("Excel列名:", df.columns.tolist())
    print("="*80 + "\n")
    
    # 获取列名（处理可能的空格）
    col_base = '数据表指标名称 D '  # 注意列名可能有尾随空格
    col_meituan = '美团外卖指标名称A'
    col_eleme = '饿了么外卖指标名称B'
    col_jd = '京东外卖指标名称C'
    
    # 2. 检查 FIELD_MAPPING 中 base 字典的 values 与 df 的"数据表指标名称 D"的差异
    base_mapping = FIELD_MAPPING['base']
    base_values = set(base_mapping.values())
    # 过滤掉 None 值
    base_values = {v for v in base_values if v is not None}
    
    excel_base_metrics = set(df[col_base].dropna().tolist())
    
    # 在 base 中但不在 Excel 中的指标
    missing_in_excel = base_values - excel_base_metrics
    # 在 Excel 中但不在 base 中的指标
    extra_in_excel = excel_base_metrics - base_values
    
    print("【1. Base字典与Excel '数据表指标名称 D' 差异分析】")
    print("-"*60)
    print(f"Base字典中的指标数量: {len(base_values)}")
    print(f"Excel中的指标数量: {len(excel_base_metrics)}")
    print()
    
    if missing_in_excel:
        print(f"⚠️  在Base字典中存在，但在Excel中缺失的指标 ({len(missing_in_excel)}):")
        for item in sorted(missing_in_excel):
            print(f"   - {item}")
        print()
    
    if extra_in_excel:
        print(f"ℹ️  在Excel中存在，但在Base字典中缺失的指标 ({len(extra_in_excel)}):")
        for item in sorted(extra_in_excel):
            print(f"   - {item}")
        print()
    
    if not missing_in_excel and not extra_in_excel:
        print("✅ Base字典与Excel完全一致！")
        print()
    
    # 创建反向映射：从 base 的 value 找到 key
    reverse_base = {v: k for k, v in base_mapping.items() if v is not None}
    
    # 3. 检查各平台差异并生成映射建议
    # 逻辑：以 base 为基础，用各平台与 base 的差异来构建平台字典
    platforms = [
        ('meituan', col_meituan, '美团'),
        ('eleme', col_eleme, '饿了么'),
        ('jd', col_jd, '京东'),
    ]
    
    suggested_mappings = {}
    
    for platform_key, platform_col, platform_name in platforms:
        print(f"【{platform_name}平台映射建议】")
        print("-"*60)
        
        # 以 base 为基础，复制一份作为平台映射的初始值
        suggested = dict(base_mapping)
        
        # 记录变更的字段
        changes = {}
        
        # 遍历 Excel 的每一行
        for idx, row in df.iterrows():
            base_metric = row[col_base]
            platform_metric = row[platform_col]
            
            # 如果 base_metric 为空，跳过
            if pd.isna(base_metric):
                continue
            
            # 查找 base_metric 对应的 key
            field_key = reverse_base.get(base_metric)
            
            if field_key is None:
                # 这个指标在 base 中没有定义
                continue
            
            # 获取 base 中的原始值
            base_value = base_mapping.get(field_key)
            
            # 根据平台列的值更新映射
            if pd.isna(platform_metric) or platform_metric == '':
                # 平台没有这个指标，设置为 None
                if base_value is not None:
                    suggested[field_key] = None
                    changes[field_key] = {'from': base_value, 'to': None}
            else:
                platform_value = str(platform_metric).strip()
                # 无论是否与 base 不同，都使用 Excel 中的平台指标值
                if platform_value != base_value:
                    suggested[field_key] = platform_value
                    changes[field_key] = {'from': base_value, 'to': platform_value}
        
        suggested_mappings[platform_key] = suggested
        
        # 打印变更信息
        if changes:
            print(f"📝 与Base字典有差异的字段 ({len(changes)}):")
            for key, change in changes.items():
                print(f"   '{key}':")
                print(f"      Base值: {change['from']}")
                print(f"      平台值: {change['to']}")
            print()
        else:
            print("✅ 平台映射与Base字典完全一致！")
            print()
        
        # 打印完整的建议映射
        print(f"📋 {platform_name}平台完整建议映射 (可直接复制到 field_mapping.py):")
        print()
        print(f"    # ========== {platform_name} 建议映射 ==========")
        print(f"    \"{platform_key}\": {{")
        for key, value in suggested.items():
            if value is None:
                print(f"        \"{key}\": None,")
            else:
                print(f"        \"{key}\": \"{value}\",")
        print(f"    }},")
        print()
    
    print("="*80)
    print("检查完成！")
    
    return suggested_mappings


if __name__ == "__main__":
    check_metric_mapping()