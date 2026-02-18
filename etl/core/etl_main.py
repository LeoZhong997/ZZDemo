import pandas as pd
from sqlalchemy import create_engine, text
import sys
import logging
from datetime import datetime
import traceback
import os

# 导入同目录下的模块
from .field_mapping import FIELD_MAPPING, FIELD_TYPES
from .store_mapper import get_store_mapper

# 导入config模块（从上层config目录）
from ..config import (
    DB_CONFIG, 
    get_connection_string, 
    TABLE_NAME, 
    BATCH_SIZE, 
    DUPLICATE_CHECK_DAYS,
    PLATFORM_MEITUAN, 
    PLATFORM_ELEME, 
    PLATFORM_JD,
    LOG_DIR,
    LOG_FORMAT,
    LOG_DATE_FORMAT
)

logger = logging.getLogger(__name__)

# ========== 文件配置 ==========
# 定义要处理的文件列表 (平台中文名, 平台映射key, 文件路径, 表头所在行索引)
FILES_TO_PROCESS = [
    (PLATFORM_MEITUAN, 'meituan', 'etl/data/sources/下载源文件/门店_全部门店_20260112_20260118_PPZH2669_2026-02-10+16_16_14.csv', 0),
    (PLATFORM_ELEME, 'eleme', 'etl/data/sources/下载源文件/门店下载_20260112至20260118_全部门店_5296290467_20260210161649743.xlsx', 0),
    (PLATFORM_JD, 'jd', 'etl/data/sources/下载源文件/门店_20260112_20260118_jd_szsxxqc_2026-02-10 16_17_24.xlsx', 0),
]


def create_database_engine():
    """
    创建数据库连接引擎
    """
    engine = create_engine(
        get_connection_string(),
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )
    return engine


def test_database_connection(engine):
    """
    测试数据库连接是否正常
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def read_excel_file(platform, filepath, header=0):
    """
    读取Excel文件或CSV文件
    
    Args:
        platform: 平台名称
        filepath: 文件路径
        header: 表头所在行索引，默认0
    
    Returns:
        DataFrame 或 None (读取失败时)
    """
    try:
        print(f"\n{'='*60}")
        print(f"📄 正在读取 {platform} 平台数据: {filepath}")
        print(f"{'='*60}")
        
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, header=header, encoding='gbk')
        else:
            df = pd.read_excel(filepath, header=header)
        
        print(f"✅ 文件读取成功，共 {len(df)} 行 {len(df.columns)} 列")
        print(f"   原始列名: {list(df.columns[:10])}...")
        return df
    except FileNotFoundError:
        print(f"❌ 文件不存在: {filepath}")
        print(f"   请检查文件路径是否正确")
        return None
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        traceback.print_exc()
        return None


def process_single_file(platform_name, mapping_key, filepath, header=0):
    """
    处理单个文件：读取 -> 清洗 -> 验证 -> 门店映射

    Args:
        platform_name: 平台中文名称（美团/饿了么/京东）
        mapping_key: 字段映射key（meituan/eleme/jd）
        filepath: 文件路径
        header: 表头所在行索引

    Returns:
        处理后的DataFrame 或 None
    """
    # 读取文件
    df = read_excel_file(platform_name, filepath, header)
    if df is None:
        return None

    # 数据清洗和计算
    try:
        print(f"\n🔄 开始清洗和计算 {platform_name} 数据...")

        # 获取平台专属的字段映射（中文列名 -> 英文字段名）
        platform_mapping = FIELD_MAPPING.get(mapping_key, {})
        if not platform_mapping:
            print(f"❌ 未找到平台 {mapping_key} 的字段映射配置")
            return None

        # 构建反向映射：中文列名 -> 英文字段名（跳过 None 值）
        reverse_mapping = {v: k for k, v in platform_mapping.items() if v is not None}

        df_processed = df.rename(columns=reverse_mapping)
        mapped_count = sum(1 for col in df.columns if col in reverse_mapping)
        print(f"   ✅ 列名映射完成（匹配 {mapped_count}/{len(df.columns)} 列）")
        
        # 门店映射处理
        if 'platform_store_name' in df_processed.columns:
            # 获取门店映射器
            store_mapper = get_store_mapper()
            
            # 为每条记录获取品牌门店名称
            brand_store_names = []
            skipped_count = 0
            
            for idx, row in df_processed.iterrows():
                platform_store = row['platform_store_name']
                brand_store = store_mapper.get_brand_store_name(platform_name, platform_store)
                
                if brand_store:
                    brand_store_names.append(brand_store)
                else:
                    # 未找到映射，跳过该记录
                    skipped_count += 1
                    brand_store_names.append(None)
            
            df_processed['brand_store_name'] = brand_store_names
            
            # 过滤掉未映射的门店记录
            original_count = len(df_processed)
            df_processed = df_processed[df_processed['brand_store_name'].notna()]
            
            if skipped_count > 0:
                print(f"   ⚠️  跳过 {skipped_count} 条未映射门店记录")
                print(f"   ✅ 保留 {len(df_processed)} 条已映射门店记录")
            else:
                print(f"   ✅ 所有门店都已正确映射")
        elif 'brand_store_name' in df_processed.columns:
            # 如果只有brand_store_name而没有platform_store_name
            print(f"   ⚠️  数据中只有brand_store_name，无法进行门店映射验证")
            print(f"   💡 建议添加platform_store_name列以支持门店映射")
        else:
            print(f"   ⚠️  数据中缺少platform_store_name和brand_store_name列")

        # 确保日期格式
        if 'date' in df_processed.columns:
            # 根据日期列的数据类型选择合适的解析方式
            # 数字类型（如 20260112）使用 '%Y%m%d'
            # 字符串类型（如 '2026-01-12'）使用 '%Y-%m-%d'
            
            # 检查日期列的数据类型
            dtype = df_processed['date'].dtype
            
            if dtype in ['int64', 'int32']:
                # 美团：整数格式（如 20260112）
                df_processed['date'] = pd.to_datetime(df_processed['date'].astype(str), format='%Y%m%d', errors='coerce').dt.date
                print(f"   📅 检测到整数格式日期，使用 '%Y%m%d' 解析")
            else:
                # 饿了么/京东：字符串格式（如 '2026-01-12'）
                df_processed['date'] = pd.to_datetime(df_processed['date'], errors='coerce').dt.date
                print(f"   📅 检测到字符串格式日期，使用自动解析")
            
            # 检查日期解析结果
            null_count = df_processed['date'].isnull().sum()
            if null_count > 0:
                print(f"   ⚠️  有 {null_count} 条记录的日期解析失败，将被过滤")
                df_processed = df_processed[df_processed['date'].notna()]

        # 添加平台标识（使用中文名，与数据库一致）
        df_processed['platform'] = platform_name

        # 清洗数值列
        numeric_columns = df_processed.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_columns:
            df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)

        # 清洗百分比列（包含中文"率"或"转化"的列名）
        percentage_cols = [col for col in df_processed.columns if ('率' in str(col) or '转化' in str(col))]
        for col in percentage_cols:
            if df_processed[col].dtype == 'object':
                # 先转换为字符串并清理
                df_processed[col] = (
                    df_processed[col].astype(str)
                    .str.replace('%', '', regex=False)
                    .str.replace(',', '', regex=False)
                    .str.replace('nan', '0', regex=False)
                    .str.replace('c', '0', regex=False)
                    .str.strip()
                )
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
            
            # 智能检测并统一转换率为百分比格式（0-100）
            # 如果值在0-1之间（不包括0和1），假设为小数，乘以100转换为百分比
            # 如果值在1-100之间，假设已经是百分比，保持不变
            if col in df_processed.columns:
                # 获取非零值
                non_zero_values = df_processed[col][df_processed[col] > 0]
                
                if len(non_zero_values) > 0:
                    # 检查大部分值是否小于1（小数格式）
                    values_less_than_1 = (non_zero_values < 1).sum()
                    ratio = values_less_than_1 / len(non_zero_values)
                    
                    # 如果超过80%的值小于1，则认为是小数格式，需要转换
                    if ratio > 0.8:
                        print(f"   📊 检测到 {col} 为小数格式，转换为百分比...")
                        df_processed[col] = df_processed[col] * 100
                        
                        # 显示转换示例
                        sample_before = non_zero_values.iloc[0] if len(non_zero_values) > 0 else 0
                        sample_after = sample_before * 100
                        print(f"      示例: {sample_before:.4f} → {sample_after:.2f}%")
        
        # 验证百分比列的值是否在合理范围内（0-100）
        for col in percentage_cols:
            if col in df_processed.columns:
                out_of_range = df_processed[(df_processed[col] < 0) | (df_processed[col] > 100)]
                if len(out_of_range) > 0:
                    print(f"   ⚠️  {col} 有 {len(out_of_range)} 条记录超出0-100范围，将限制在此范围内")
                    df_processed[col] = df_processed[col].clip(0, 100)

        print(f"✅ {platform_name} 数据清洗完成，共 {len(df_processed)} 行")

        # 简化验证：只检查必需列
        required_columns = ['date', 'platform', 'brand_store_name']
        missing_cols = [col for col in required_columns if col not in df_processed.columns]
        if missing_cols:
            print(f"⚠️  数据缺少必需列: {missing_cols}")
            return None

        print(f"✅ {platform_name} 数据验证通过")

        return df_processed

    except Exception as e:
        print(f"❌ {platform_name} 数据清洗失败: {e}")
        traceback.print_exc()
        return None


def save_to_database(df, engine, table_name):
    """
    将DataFrame保存到数据库（使用 INSERT IGNORE 自动跳过重复数据）
    
    Args:
        df: 要保存的DataFrame
        engine: 数据库引擎
        table_name: 表名
    
    Returns:
        是否保存成功
    """
    try:
        print(f"\n{'='*60}")
        print(f"💾 准备将数据写入数据库表: {table_name}")
        print(f"{'='*60}")
        
        # 打印DataFrame列名
        print(f"\n📊 DataFrame 当前列名 ({len(df.columns)} 列):")
        
        # 获取数据库列名
        with engine.connect() as conn:
            result = conn.execute(text(f"DESCRIBE {table_name}"))
            db_columns = set(row[0] for row in result)
        
        # 只保留数据库存在的列
        df_columns = set(df.columns)
        final_columns = list(df_columns & db_columns)
        df_to_import = df[final_columns]
        
        if len(final_columns) < len(df.columns):
            removed = list(df_columns - set(final_columns))
            print(f"\n⚠️  跳过{len(removed)}个数据库不存在的列: {', '.join(removed[:5])}...")
        
        print(f"\n📋 将要写入的数据: {len(df_to_import)} 行")
        
        # 添加导入时间（去除已存在的import_time列，避免重复）
        if 'import_time' in df_to_import.columns:
            df_to_import = df_to_import.drop(columns=['import_time'])
        df_to_import['import_time'] = datetime.now()
        
        # 将NaN替换为None（MySQL不接受NaN）
        df_to_import = df_to_import.replace({float('nan'): None})
        
        # 写入数据库（使用 INSERT IGNORE 自动跳过重复数据）
        print(f"\n💾 正在写入数据库（使用 INSERT IGNORE 跳过重复数据）...")
        
        # 使用自定义的insert方法来生成 INSERT IGNORE SQL
        from sqlalchemy.dialects.mysql import insert
        
        rows_inserted = 0
        rows_skipped = 0
        
        # 分批处理
        for chunk_start in range(0, len(df_to_import), BATCH_SIZE):
            chunk_end = min(chunk_start + BATCH_SIZE, len(df_to_import))
            chunk = df_to_import.iloc[chunk_start:chunk_end]
            
            # 构建INSERT IGNORE语句
            with engine.connect() as conn:
                # 使用原生SQL INSERT IGNORE
                insert_stmt = text(f"""
                    INSERT IGNORE INTO {table_name}
                    ({', '.join([f'`{col}`' for col in chunk.columns])})
                    VALUES ({', '.join([':' + col for col in chunk.columns])})
                """)
                
                # 执行插入
                result = conn.execute(insert_stmt, chunk.to_dict('records'))
                rows_inserted += result.rowcount
                conn.commit()
        
        rows_skipped = len(df_to_import) - rows_inserted
        print(f"   ✅ 导入完成:")
        print(f"      - 成功插入: {rows_inserted} 条")
        print(f"      - 跳过重复: {rows_skipped} 条")
        print(f"      - 总计处理: {len(df_to_import)} 条")
        
        return True

    except Exception as e:
        print(f"❌ 写入数据库失败: {e}")
        traceback.print_exc()
        return False


def main():
    """
    主函数：完整的ETL流程
    """
    print("\n" + "="*60)
    print("🍔 外卖数据看板 ETL 主程序")
    print(f"{'='*60}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 步骤1: 创建数据库连接
    print(f"\n📡 步骤 1/4: 创建数据库连接...")
    engine = create_database_engine()

    # 测试连接
    if not test_database_connection(engine):
        print("\n❌ 无法连接数据库，程序退出")
        sys.exit(1)

    # 步骤2: 读取和处理所有文件
    print(f"\n📂 步骤 2/4: 读取和处理Excel文件...")

    processed_dataframes = []
    success_count = 0
    failed_platforms = []

    for platform_name, mapping_key, filepath, header in FILES_TO_PROCESS:
        try:
            processed_df = process_single_file(platform_name, mapping_key, filepath, header)
            if processed_df is not None:
                processed_dataframes.append(processed_df)
                success_count += 1
            else:
                failed_platforms.append(platform_name)

        except Exception as e:
            print(f"❌ 处理 {platform_name} 时发生异常: {e}")
            traceback.print_exc()
            failed_platforms.append(platform_name)
            # 继续处理下一个文件
            continue

    # 检查是否所有文件都处理失败
    if len(processed_dataframes) == 0:
        print("\n❌ 所有文件处理失败，程序退出")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"📊 文件处理统计")
    print(f"{'='*60}")
    print(f"✅ 成功处理: {success_count}/{len(FILES_TO_PROCESS)} 个平台")
    if failed_platforms:
        print(f"❌ 处理失败: {', '.join(failed_platforms)}")

    # 步骤3: 合并数据
    print(f"\n🔗 步骤 3/4: 合并所有平台数据...")

    try:
        merged_df = pd.concat(processed_dataframes, ignore_index=True)
        print(f"✅ 数据合并完成，共 {len(merged_df)} 行 {len(merged_df.columns)} 列")

        # 按平台分组统计
        print(f"\n📈 各平台数据量统计:")
        for platform in merged_df['platform'].unique():
            count = len(merged_df[merged_df['platform'] == platform])
            percentage = count / len(merged_df) * 100
            print(f"   {platform:10s}: {count:5d} 行 ({percentage:5.2f}%)")

    except Exception as e:
        print(f"❌ 数据合并失败: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 步骤4: 写入数据库
    print(f"\n💾 步骤 4/4: 写入数据库...")

    if not save_to_database(merged_df, engine, TABLE_NAME):
        print("\n❌ 数据入库失败，程序退出")
        sys.exit(1)

    # 完成
    print(f"\n{'='*60}")
    print(f"🎉 ETL 流程完成！")
    print(f"{'='*60}")
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 总计处理: {len(merged_df)} 条记录")
    print(f"📋 写入表名: {TABLE_NAME}")


def setup_logging():
    """配置日志系统"""
    os.makedirs(LOG_DIR, exist_ok=True)

    log_file = os.path.join(LOG_DIR, f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger.info(f"日志文件: {log_file}")


if __name__ == '__main__':
    setup_logging()
    try:
        main()
        
        # 显示未映射门店提醒
        store_mapper = get_store_mapper()
        store_mapper.log_unmapped_stores()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 程序发生未预期的异常:")
        traceback.print_exc()
        sys.exit(1)