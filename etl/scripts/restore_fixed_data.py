"""
从备份数据恢复并修复后重新导入
"""
import pandas as pd
from sqlalchemy import create_engine, text
from ..config import get_connection_string, TABLE_NAME
from datetime import datetime

def main():
    print("\n" + "="*60)
    print("🔄 恢复并修复备份数据")
    print("="*60)
    
    # 读取备份数据
    backup_file = 'backup/daily_orders_backup_20260111_20260118_20260214_104331.csv'
    print(f"\n📂 读取备份文件: {backup_file}")
    df_backup = pd.read_csv(backup_file)
    
    print(f"   备份数据记录数: {len(df_backup)}")
    print(f"   备份数据日期范围: {df_backup['date'].min()} 到 {df_backup['date'].max()}")
    print(f"\n📊 平台分布:")
    print(df_backup['platform'].value_counts())
    
    # 删除数据库中2026-01-11至2026-01-18的数据
    engine = create_engine(get_connection_string(), echo=False)
    with engine.connect() as conn:
        delete_query = text(f'DELETE FROM {TABLE_NAME} WHERE date BETWEEN "2026-01-11" AND "2026-01-18"')
        result = conn.execute(delete_query)
        conn.commit()
        print(f"\n🗑️  已删除 {result.rowcount} 条旧数据")
    
    # 备份数据是小数格式，需要转换为百分比格式
    print(f"\n🔄 转换转化率数据格式...")
    percentage_cols = [col for col in df_backup.columns if ('率' in str(col) or '转化' in str(col))]
    
    for col in percentage_cols:
        # 备份数据是小数格式（0.07表示7%），需要乘以100
        non_zero_values = df_backup[col][df_backup[col] > 0]
        if len(non_zero_values) > 0:
            avg_value = non_zero_values.mean()
            # 如果平均值小于1，说明是小数格式，需要乘以100
            if avg_value < 1:
                print(f"   📊 {col} 为小数格式，转换为百分比 (平均 {avg_value:.4f}% → {avg_value*100:.2f}%)...")
                df_backup[col] = df_backup[col] * 100
            else:
                print(f"   ✅ {col} 已是百分比格式 (平均 {avg_value:.2f}%)")
    
    # 添加import_time
    df_backup['import_time'] = datetime.now()
    
    # 去除重复数据（保留第一条）
    print(f"\n🔄 去除重复数据...")
    before_dedup = len(df_backup)
    df_backup = df_backup.drop_duplicates(subset=['date', 'platform', 'brand_store_name'], keep='first')
    after_dedup = len(df_backup)
    print(f"   去除重复: {before_dedup} → {after_dedup} 条 (删除 {before_dedup - after_dedup} 条)")
    
    # 使用INSERT IGNORE写入数据库
    print(f"\n💾 写入数据库...")
    BATCH_SIZE = 100
    
    rows_inserted = 0
    rows_skipped = 0
    
    for chunk_start in range(0, len(df_backup), BATCH_SIZE):
        chunk_end = min(chunk_start + BATCH_SIZE, len(df_backup))
        chunk = df_backup.iloc[chunk_start:chunk_end]
        
        # 将NaN替换为None
        chunk = chunk.replace({float('nan'): None})
        
        with engine.connect() as conn:
            insert_stmt = text(f"""
                INSERT IGNORE INTO {TABLE_NAME}
                ({', '.join([f'`{col}`' for col in chunk.columns])})
                VALUES ({', '.join([':' + col for col in chunk.columns])})
            """)
            result = conn.execute(insert_stmt, chunk.to_dict('records'))
            rows_inserted += result.rowcount
            conn.commit()
    
    rows_skipped = len(df_backup) - rows_inserted
    print(f"   ✅ 导入完成:")
    print(f"      - 成功插入: {rows_inserted} 条")
    print(f"      - 跳过重复: {rows_skipped} 条")
    print(f"      - 总计处理: {len(df_backup)} 条")
    
    print(f"\n{'='*60}")
    print(f"✅ 恢复完成！")
    print(f"{'='*60}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 恢复失败: {e}")
        import traceback
        traceback.print_exc()