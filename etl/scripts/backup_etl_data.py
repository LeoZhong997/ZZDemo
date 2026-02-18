"""
ETL数据备份脚本
备份2026-01-11至2026-01-18期间的数据
"""
import pandas as pd
from sqlalchemy import create_engine, text
from ..config import DB_CONFIG, get_connection_string, TABLE_NAME
from datetime import datetime
import os

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

def backup_data():
    """备份指定日期范围的数据"""
    print("\n" + "="*60)
    print("💾 ETL数据备份")
    print("="*60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建数据库连接
    print(f"\n📡 连接数据库...")
    engine = create_database_engine()
    
    # 查询要备份的数据
    print(f"\n📊 查询 2026-01-11 至 2026-01-18 的数据...")
    query = text(f"""
        SELECT * FROM {TABLE_NAME}
        WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
        ORDER BY date, platform, brand_store_name
    """)
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    print(f"✅ 查询到 {len(df)} 条记录")
    
    # 保存为CSV文件
    backup_dir = "backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f"daily_orders_backup_20260111_20260118_{timestamp}.csv")
    
    df.to_csv(backup_file, index=False, encoding='utf-8-sig')
    print(f"✅ 备份文件已保存: {backup_file}")
    
    # 也备份到数据库临时表
    temp_table = f"{TABLE_NAME}_backup_{timestamp}"
    print(f"\n💾 创建数据库备份表: {temp_table}")
    
    with engine.connect() as conn:
        # 创建临时表
        create_table_query = text(f"""
            CREATE TABLE {temp_table} LIKE {TABLE_NAME}
        """)
        conn.execute(create_table_query)
        
        # 插入数据
        insert_query = text(f"""
            INSERT INTO {temp_table}
            SELECT * FROM {TABLE_NAME}
            WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
        """)
        result = conn.execute(insert_query)
        
        conn.commit()
        print(f"✅ 数据库备份完成: {result.rowcount} 条记录")
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"✅ 备份完成！")
    
    return backup_file, temp_table

if __name__ == '__main__':
    try:
        backup_file, temp_table = backup_data()
        print(f"\n📝 备份信息:")
        print(f"   CSV文件: {backup_file}")
        print(f"   数据库表: {temp_table}")
    except Exception as e:
        print(f"\n❌ 备份失败: {e}")
        import traceback
        traceback.print_exc()
