"""
外卖数据看板 - 统一配置文件
所有数据库连接、文件路径、常量均在此处集中管理
"""
import os

# ========== 数据库配置 ==========
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1024Asdf'),
    'database': os.getenv('DB_NAME', 'waimai_db'),
}

# SQLAlchemy 连接字符串
def get_connection_string():
    return (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset=utf8mb4"
    )

# ========== 数据库表名 ==========
TABLE_NAME = 'daily_orders'

# ========== 平台名称（中文，与数据库一致）==========
PLATFORM_MEITUAN = '美团'
PLATFORM_ELEME = '饿了么'
PLATFORM_JD = '京东'
ALL_PLATFORMS = [PLATFORM_MEITUAN, PLATFORM_ELEME, PLATFORM_JD]

# ========== ETL 批处理配置 ==========
BATCH_SIZE = 1000
DUPLICATE_CHECK_DAYS = 90  # 去重检查回溯天数

# ========== 项目根目录 ==========
# etl/config/__file__ -> 项目根目录
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
ETL_DIR = os.path.dirname(CONFIG_DIR)
PROJECT_ROOT = os.path.dirname(ETL_DIR)

# ========== 目录配置 ==========
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
DATA_DIR = os.path.join(PROJECT_ROOT, 'etl', 'data')
SOURCES_DIR = os.path.join(DATA_DIR, 'sources')
BACKUP_DIR = os.path.join(DATA_DIR, 'backup')
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'etl', 'reports')

# 确保目录存在
for directory in [LOG_DIR, DATA_DIR, SOURCES_DIR, BACKUP_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ========== 日志配置 ==========
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'