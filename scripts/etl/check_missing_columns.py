from sqlalchemy import create_engine, text
from ..config import get_connection_string, TABLE_NAME
from ..core.field_mapping import FIELD_MAPPING
import pandas as pd

print("="*60)
print("📊 缺失列校验报告")
print("="*60)

# 获取数据库表结构
engine = create_engine(get_connection_string())
with engine.connect() as conn:
    result = conn.execute(text(f"DESCRIBE {TABLE_NAME}"))
    db_columns = set(row[0] for row in result)

print(f"\n📋 数据库表 '{TABLE_NAME}' 共有 {len(db_columns)} 列")

# 检查各平台的字段映射
print("\n" + "="*60)
print("🔍 各平台字段映射分析")
print("="*60)

all_missing_columns = {}

for platform_key, mapping in FIELD_MAPPING.items():
    platform_name = {
        'meituan': '美团',
        'eleme': '饿了么',
        'jd': '京东'
    }.get(platform_key, platform_key)
    
    print(f"\n📌 {platform_name} 平台 ({platform_key}):")
    print("-" * 60)
    
    # 获取所有映射的字段名
    mapped_fields = [field_name for field_name, source_name in mapping.items() if source_name is not None]
    
    # 检查哪些字段在数据库中不存在
    missing_in_db = [field for field in mapped_fields if field not in db_columns]
    
    if missing_in_db:
        print(f"   ❌ 缺失字段 ({len(missing_in_db)} 个):")
        for field in missing_in_db:
            source_name = mapping[field]
            print(f"      - {field:30s} <- 源文件: {source_name}")
        all_missing_columns[platform_name] = missing_in_db
    else:
        print(f"   ✅ 所有字段都已映射到数据库")
    
    # 统计
    total_mapped = len(mapped_fields)
    available_in_db = total_mapped - len(missing_in_db)
    print(f"\n   📊 统计:")
    print(f"      - 映射字段总数: {total_mapped}")
    print(f"      - 数据库存在: {available_in_db}")
    print(f"      - 数据库缺失: {len(missing_in_db)}")
    print(f"      - 覆盖率: {available_in_db/total_mapped*100:.1f}%")

# 汇总报告
print("\n" + "="*60)
print("📋 缺失列汇总")
print("="*60)

total_missing = sum(len(cols) for cols in all_missing_columns.values())

if total_missing > 0:
    print(f"\n⚠️  发现 {total_missing} 个缺失字段")
    print("\n详细列表:")
    
    for platform_name, missing_cols in all_missing_columns.items():
        if missing_cols:
            print(f"\n{platform_name}:")
            for field in missing_cols:
                source_name = FIELD_MAPPING[
                    'meituan' if platform_name == '美团' else
                    'eleme' if platform_name == '饿了么' else 'jd'
                ][field]
                print(f"  - {field:30s} (源文件: {source_name})")
else:
    print("\n✅ 所有平台的字段都已正确映射到数据库表")

# 建议
print("\n" + "="*60)
print("💡 建议")
print("="*60)

if total_missing > 0:
    print("\n1. 对于缺失的字段，有以下选择:")
    print("   - 选项A: 在数据库表中添加这些列")
    print("   - 选项B: 在字段映射中移除这些字段（如果不需要）")
    print("   - 选项C: 更新字段映射，将缺失字段映射到现有的列")
    print("\n2. 建议的SQL语句（添加缺失列）:")
    print("\n-- 请根据实际需要选择要添加的列")
    for platform_name, missing_cols in all_missing_columns.items():
        if missing_cols:
            print(f"\n-- {platform_name} 平台缺失列")
            for field in missing_cols:
                print(f"ALTER TABLE {TABLE_NAME} ADD COLUMN `{field}` DECIMAL(10,2) DEFAULT NULL COMMENT '{field}';")
else:
    print("\n✅ 当前字段映射完整，无需修改")

print(f"\n⏰ 报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")