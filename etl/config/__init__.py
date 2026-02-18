"""
ETL配置模块

包含数据库连接、路径配置、常量等
"""

from .config import (
    DB_CONFIG,
    get_connection_string,
    TABLE_NAME,
    PLATFORM_MEITUAN,
    PLATFORM_ELEME,
    PLATFORM_JD,
    ALL_PLATFORMS,
    BATCH_SIZE,
    DUPLICATE_CHECK_DAYS,
    PROJECT_ROOT,
    LOG_DIR,
    DATA_DIR,
    SOURCES_DIR,
    BACKUP_DIR,
    REPORTS_DIR,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
)

__all__ = [
    'DB_CONFIG',
    'get_connection_string',
    'TABLE_NAME',
    'PLATFORM_MEITUAN',
    'PLATFORM_ELEME',
    'PLATFORM_JD',
    'ALL_PLATFORMS',
    'BATCH_SIZE',
    'DUPLICATE_CHECK_DAYS',
    'PROJECT_ROOT',
    'LOG_DIR',
    'DATA_DIR',
    'SOURCES_DIR',
    'BACKUP_DIR',
    'REPORTS_DIR',
    'LOG_FORMAT',
    'LOG_DATE_FORMAT',
]