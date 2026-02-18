"""
外卖数据看板 - 数据处理工具模块
提供可复用的数据清洗、转换、验证和去重功能
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from sqlalchemy import create_engine, text

from .field_mapping import FIELD_MAPPING, FIELD_TYPES
from ..config import get_connection_string, TABLE_NAME, BATCH_SIZE

logger = logging.getLogger(__name__)


def get_engine():
    """创建数据库连接引擎（带连接池）"""
    return create_engine(
        get_connection_string(),
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )


def get_platform_mapping(mapping_key):
    """
    获取指定平台的反向字段映射（中文列名 -> 英文字段名）

    Args:
        mapping_key: 平台映射key (meituan / eleme / jd)

    Returns:
        dict: {英文目标字段名: 中文源列名}，跳过 None 值
    """
    platform_mapping = FIELD_MAPPING.get(mapping_key, {})
    
    # 反向映射：中文列名 -> 英文目标字段名
    return {v: k for k, v in platform_mapping.items() if v is not None}


def clean_percentage_column(series):
    """
    清洗百分比列：去除%、逗号等符号，转为数值

    Args:
        series: pandas Series

    Returns:
        清洗后的 numeric Series
    """
    if series.dtype == 'object':
        series = (
            series.astype(str)
            .str.replace('%', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.replace('¥', '', regex=False)
            .str.replace('nan', '0', regex=False)
            .str.replace('NaN', '0', regex=False)
            .str.replace('c', '0', regex=False)
            .str.strip()
        )
    return pd.to_numeric(series, errors='coerce').fillna(0)


def clean_numeric_columns(df):
    """
    批量清洗 DataFrame 中的数值列

    Args:
        df: 待清洗的 DataFrame

    Returns:
        清洗后的 DataFrame
    """
    # 已经是数值类型的列
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 包含"率"或"转化"的列名视为百分比列
    pct_cols = [col for col in df.columns if ('率' in str(col) or '转化' in str(col))]
    for col in pct_cols:
        df[col] = clean_percentage_column(df[col])

    return df


def standardize_dates(df, date_column='date'):
    """
    统一日期格式

    Args:
        df: DataFrame
        date_column: 日期列名

    Returns:
        处理后的 DataFrame
    """
    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce').dt.date
    return df


def filter_db_columns(df, engine):
    """
    过滤 DataFrame 列，只保留数据库表中存在的列

    Args:
        df: DataFrame
        engine: SQLAlchemy engine

    Returns:
        (filtered_df, removed_columns_list)
    """
    with engine.connect() as conn:
        result = conn.execute(text(f"DESCRIBE {TABLE_NAME}"))
        db_columns = set(row[0] for row in result)

    df_columns = set(df.columns)
    final_columns = list(df_columns & db_columns)
    removed = list(df_columns - db_columns)
    # 排除内部标记列
    removed = [c for c in removed if not c.startswith('_')]

    return df[final_columns], removed


def check_duplicates(df, engine):
    """
    检查数据库中已存在的记录，返回去重后的新数据

    Args:
        df: 待导入的 DataFrame（必须包含 date, platform, brand_store_name 列）
        engine: SQLAlchemy engine

    Returns:
        去重后的 DataFrame（仅包含新记录）
    """
    if df.empty:
        return df

    min_date = df['date'].min()
    max_date = df['date'].max()

    with engine.connect() as conn:
        query = text(f"""
            SELECT DISTINCT date, platform, brand_store_name
            FROM {TABLE_NAME}
            WHERE date BETWEEN :min_date AND :max_date
        """)
        existing_data = pd.read_sql(query, conn, params={
            'min_date': min_date,
            'max_date': max_date
        })

    if existing_data.empty:
        logger.info("数据库中无重复数据，将导入全部记录")
        return df

    existing_keys = set(
        zip(existing_data['date'], existing_data['platform'], existing_data['brand_store_name'])
    )

    mask = df.apply(
        lambda row: (row['date'], row['platform'], row['brand_store_name']) not in existing_keys,
        axis=1
    )
    new_data = df[mask].copy()
    skipped = len(df) - len(new_data)
    logger.info(f"去重完成：跳过 {skipped} 条已存在记录，保留 {len(new_data)} 条新记录")
    return new_data


def import_to_database(df, engine):
    """
    将 DataFrame 导入数据库（append 模式，分批写入）

    Args:
        df: 待导入的 DataFrame
        engine: SQLAlchemy engine

    Returns:
        bool: 是否成功
    """
    if df.empty:
        logger.warning("没有需要导入的数据")
        return True

    try:
        # 过滤列
        df_to_import, removed = filter_db_columns(df, engine)
        if removed:
            logger.info(f"跳过 {len(removed)} 个数据库不存在的列: {', '.join(removed[:5])}...")

        # 添加导入时间
        df_to_import = df_to_import.copy()
        df_to_import['import_time'] = datetime.now()

        # 分批写入
        total_rows = len(df_to_import)
        df_to_import.to_sql(
            name=TABLE_NAME,
            con=engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=BATCH_SIZE
        )

        logger.info(f"成功导入 {total_rows} 条记录到 {TABLE_NAME}")
        return True

    except Exception as e:
        logger.error(f"数据导入失败: {e}", exc_info=True)
        return False


def validate_required_columns(df, required=None):
    """
    验证 DataFrame 是否包含必需列

    Args:
        df: DataFrame
        required: 必需列名列表，默认 ['date', 'platform', 'brand_store_name']

    Returns:
        (is_valid, missing_columns)
    """
    if required is None:
        required = ['date', 'platform', 'brand_store_name']
    missing = [col for col in required if col not in df.columns]
    return len(missing) == 0, missing