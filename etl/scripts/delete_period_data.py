"""
删除2026-01-12至2026-01-18期间的所有数据，为重新导入做准备
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

def delete_period_data():
    """删除指定日期范围的数据"""
    print("\n" + "="*60)
    print("🗑️  删除旧数据")
    print("="*60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建数据库连接
    print(f"\n📡 连接数据库...")
    engine = create_database_engine()
    
    with engine.connect() as conn:
        # 步骤1: 查询要删除的数据量
        print(f"\n📊 步骤 1/2: 查询要删除的数据...")
        count_query = text(f"""
            SELECT COUNT(*) as count
            FROM {TABLE_NAME}
            WHERE date BETWEEN '2026-01-12' AND '2026-01-18'
        """)
        result = conn.execute(count_query)
        count = result.fetchone()[0]
        
        print(f"   找到 {count} 条记录将被删除")
        
        if count == 0:
            print(f"   无需删除")
            return
        
        # 步骤2: 删除数据
        print(f"\n🗑️  步骤 2/2: 删除数据...")
        delete_query = text(f"""
            DELETE FROM {TABLE_NAME}
            WHERE date BETWEEN '2026-01-12' AND '2026-01-18'
        """)
        
        result = conn.execute(delete_query)
        conn.commit()
        
        print(f"   ✅ 已删除 {result.rowcount} 条记录")
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"✅ 删除完成！")

if __name__ == '__main__':
    try:
        delete_period_data()
    except Exception as e:
        print(f"\n❌ 删除失败: {e}")
        import traceback
        traceback.print_exc()