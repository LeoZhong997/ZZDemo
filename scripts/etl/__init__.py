"""
ETL 脚本工具模块

提供数据库管理、检查、修复、导出等功能

模块:
    - db_admin: 数据库管理（初始化/清空/删除/备份/恢复）
    - db_check: 数据库检查（状态/映射/列/指标/验证）
    - data_fix: 数据修复（转化率/重复数据/store_id）
    - store_mapping: 门店映射管理
    - export: 数据导出

使用示例:
    # 命令行使用
    python scripts/etl/db_admin.py init
    python scripts/etl/db_check.py status
    python scripts/etl/data_fix.py conversion
    python scripts/etl/store_mapping.py list
    python scripts/etl/export.py --start 2026-01-11 --end 2026-01-18

详细文档: scripts/etl/README.md
"""

# 数据库管理
from .db_admin import (
    init_database,
    clear_table,
    delete_period,
    backup_data,
    restore_data
)

# 数据库检查
from .db_check import (
    check_status,
    check_unmapped,
    check_columns,
    check_metrics,
    verify_import
)

# 数据修复
from .data_fix import (
    fix_conversion_rates,
    cleanup_duplicates,
    fix_store_id
)

# 门店映射
from .store_mapping import (
    init_store_tables,
    list_mappings
)

# 数据导出
from .export import (
    export_to_excel
)

__all__ = [
    # 数据库管理
    'init_database',
    'clear_table',
    'delete_period',
    'backup_data',
    'restore_data',
    # 数据库检查
    'check_status',
    'check_unmapped',
    'check_columns',
    'check_metrics',
    'verify_import',
    # 数据修复
    'fix_conversion_rates',
    'cleanup_duplicates',
    'fix_store_id',
    # 门店映射
    'init_store_tables',
    'list_mappings',
    # 数据导出
    'export_to_excel'
]