"""
ETL系统 - 外卖数据提取、转换、加载系统

这个包包含了处理美团、饿了么、京东等平台数据的完整ETL流程。
"""

__version__ = "1.0.0"
__author__ = "ETL Team"

from .core.etl_main import main as etl_main
from .core.validate_etl_data import main as validate_etl

__all__ = [
    'etl_main',
    'validate_etl',
]