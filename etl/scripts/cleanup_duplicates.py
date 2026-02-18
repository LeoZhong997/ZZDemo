"""
清理2026-01-11至2026-01-18期间的重复数据
"""
from sqlalchemy import create_engine, text
from ..config import get_connection_string, TABLE_NAME
from datetime import datetime

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

def cleanup_duplicates():
    """清理重复数据"""
    print("\n" + "="*60)
    print("🧹 清理重复数据")
    print("="*60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建数据库连接
    print(f"\n📡 连接数据库...")
    engine = create_database_engine()
    
    with engine.connect() as conn:
        # 步骤1: 查询重复数据
        print(f"\n🔍 步骤 1/3: 查询重复数据...")
        query = text(f"""
            SELECT date, platform, brand_store_name, COUNT(*) as cnt
            FROM {TABLE_NAME}
            WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
            GROUP BY date, platform, brand_store_name
            HAVING cnt > 1
            ORDER BY cnt DESC
        """)
        
        result = conn.execute(query)
        duplicates = result.fetchall()
        
        if len(duplicates) == 0:
            print(f"✅ 未发现重复数据")
            return
        
        print(f"   发现 {len(duplicates)} 组重复数据")
        print(f"\n   重复数据示例（前5组）:")
        for i, row in enumerate(duplicates[:5]):
            print(f"      {i+1}. {row[0]} | {row[1]} | {row[2]} - 重复 {row[3]} 次")
        
        # 步骤2: 删除重复记录（保留ID最小的）
        print(f"\n🗑️  步骤 2/3: 删除重复记录（保留ID最小的）...")
        
        delete_query = text(f"""
            DELETE t1 FROM {TABLE_NAME} t1
            INNER JOIN (
                SELECT MIN(id) as keep_id, date, platform, brand_store_name
                FROM {TABLE_NAME}
                WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
                GROUP BY date, platform, brand_store_name
                HAVING COUNT(*) > 1
            ) t2 ON t1.date = t2.date 
                  AND t1.platform = t2.platform 
                  AND t1.brand_store_name = t2.brand_store_name
                  AND t1.id != t2.keep_id
        """)
        
        result = conn.execute(delete_query)
        deleted_count = result.rowcount
        conn.commit()
        
        print(f"   ✅ 已删除 {deleted_count} 条重复记录")
        
        # 步骤3: 验证清理结果
        print(f"\n✅ 步骤 3/3: 验证清理结果...")
        
        # 查询清理后的记录数
        count_query = text(f"""
            SELECT COUNT(*) as total_count
            FROM {TABLE_NAME}
            WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
        """)
        result = conn.execute(count_query)
        total_count = result.fetchone()[0]
        
        print(f"   清理后记录数: {total_count}")
        
        # 再次检查是否还有重复
        check_query = text(f"""
            SELECT COUNT(*) as duplicate_count
            FROM (
                SELECT date, platform, brand_store_name, COUNT(*) as cnt
                FROM {TABLE_NAME}
                WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
                GROUP BY date, platform, brand_store_name
                HAVING cnt > 1
            ) as duplicates
        """)
        result = conn.execute(check_query)
        remaining_duplicates = result.fetchone()[0]
        
        if remaining_duplicates == 0:
            print(f"   ✅ 已无重复数据")
        else:
            print(f"   ⚠️  仍有 {remaining_duplicates} 组重复数据")
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"✅ 清理完成！")

if __name__ == '__main__':
    try:
        cleanup_duplicates()
    except Exception as e:
        print(f"\n❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()
