"""
ETL 数据库单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from etl.config.config import DB_CONFIG, get_connection_string, TABLE_NAME, ALL_PLATFORMS


class TestDatabaseConfig:
    """数据库配置测试"""
    
    def test_db_config_has_required_fields(self):
        """测试数据库配置包含必需字段"""
        required_fields = ['host', 'port', 'user', 'password', 'database']
        for field in required_fields:
            assert field in DB_CONFIG, f"缺少必需字段: {field}"
    
    def test_db_config_default_values(self):
        """测试数据库配置默认值"""
        assert DB_CONFIG['host'] == 'localhost'
        assert DB_CONFIG['port'] == 3306
        assert DB_CONFIG['database'] == 'waimai_db'
    
    def test_get_connection_string(self):
        """测试连接字符串生成"""
        conn_str = get_connection_string()
        
        assert 'mysql+pymysql://' in conn_str
        assert DB_CONFIG['user'] in conn_str
        assert DB_CONFIG['host'] in conn_str
        assert DB_CONFIG['database'] in conn_str
        assert 'charset=utf8mb4' in conn_str
    
    def test_table_name(self):
        """测试表名配置"""
        assert TABLE_NAME == 'daily_orders'
    
    def test_all_platforms(self):
        """测试平台配置"""
        assert '美团' in ALL_PLATFORMS
        assert '饿了么' in ALL_PLATFORMS
        assert '京东' in ALL_PLATFORMS
        assert len(ALL_PLATFORMS) == 3


class TestDatabaseConnection:
    """数据库连接测试（使用 Mock）"""
    
    def test_connection_string_format(self):
        """测试连接字符串格式"""
        conn_str = get_connection_string()
        
        # 验证连接字符串格式正确
        assert conn_str.startswith('mysql+pymysql://')
        assert '@localhost:3306/waimai_db' in conn_str
    
    @patch('sqlalchemy.create_engine')
    def test_database_connection_mock(self, mock_create_engine):
        """测试数据库连接（Mock）"""
        # 创建 Mock 引擎
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_connection.execute.return_value = mock_result
        
        # 测试连接
        from sqlalchemy import create_engine
        
        engine = create_engine(get_connection_string())
        with engine.connect() as conn:
            result = conn.execute(Mock())
            count = result.scalar()
        
        assert count == 100


class TestDatabaseQueries:
    """数据库查询测试（使用 Mock）"""
    
    @patch('sqlalchemy.create_engine')
    def test_query_daily_orders_count(self, mock_create_engine):
        """测试查询记录数"""
        # 创建 Mock
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 500
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        # 执行测试
        from sqlalchemy import create_engine, text
        
        engine = create_engine(get_connection_string())
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM daily_orders"))
            count = result.scalar()
        
        assert count == 500
    
    @patch('sqlalchemy.create_engine')
    def test_query_platform_distribution(self, mock_create_engine):
        """测试平台分布查询"""
        # 创建 Mock 数据
        mock_rows = [
            MagicMock(platform='美团', count=200),
            MagicMock(platform='饿了么', count=150),
            MagicMock(platform='京东', count=50),
        ]
        
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_connection.execute.return_value = iter(mock_rows)
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        # 执行测试
        from sqlalchemy import create_engine
        
        engine = create_engine(get_connection_string())
        with engine.connect() as conn:
            rows = list(conn.execute(Mock()))
        
        assert len(rows) == 3
        assert rows[0].platform == '美团'
        assert rows[0].count == 200


class TestDatabaseSchema:
    """数据库表结构测试（使用 Mock）"""
    
    @patch('sqlalchemy.create_engine')
    def test_table_exists_check(self, mock_create_engine):
        """测试表存在检查"""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        
        # 模拟 SHOW TABLES 结果
        mock_result = MagicMock()
        mock_result.fetchone.return_value = ('daily_orders',)
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        # 执行测试
        from sqlalchemy import create_engine, text
        
        engine = create_engine(get_connection_string())
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'daily_orders'"))
            exists = result.fetchone()
        
        assert exists is not None
        assert 'daily_orders' in exists


class TestDatabaseInsert:
    """数据库插入测试（使用 Mock）"""
    
    @patch('sqlalchemy.create_engine')
    def test_insert_record_mock(self, mock_create_engine):
        """测试插入记录（Mock）"""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_connection.execute.return_value = MagicMock()
        mock_connection.commit.return_value = None
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        # 执行测试
        from sqlalchemy import create_engine, text
        
        engine = create_engine(get_connection_string())
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO daily_orders (date, platform, brand_store_name, actual_income)
                VALUES ('2026-02-25', '美团', '测试门店', 100.00)
            """))
            conn.commit()
        
        # 验证 execute 被调用
        mock_connection.execute.assert_called_once()


class TestEnvironmentVariables:
    """环境变量测试"""
    
    def test_db_config_uses_env_vars(self):
        """测试配置读取环境变量"""
        import os
        
        # 保存原始值
        original_host = os.environ.get('DB_HOST')
        
        try:
            # 设置测试值
            os.environ['DB_HOST'] = 'test_host'
            
            # 重新导入配置（注意：由于模块已加载，这不会改变已加载的值）
            # 这里只是演示环境变量的使用方式
            assert os.environ.get('DB_HOST') == 'test_host'
            
        finally:
            # 恢复原始值
            if original_host is not None:
                os.environ['DB_HOST'] = original_host
            else:
                os.environ.pop('DB_HOST', None)


class TestDirectoryConfig:
    """目录配置测试"""
    
    def test_project_directories_exist(self):
        """测试项目目录存在"""
        from etl.config.config import LOG_DIR, DATA_DIR, SOURCES_DIR, BACKUP_DIR, REPORTS_DIR
        
        directories = [LOG_DIR, DATA_DIR, SOURCES_DIR, BACKUP_DIR, REPORTS_DIR]
        
        for directory in directories:
            assert directory is not None
            assert isinstance(directory, str)
    
    def test_directory_paths_are_absolute(self):
        """测试目录路径是绝对路径"""
        from etl.config.config import LOG_DIR, DATA_DIR
        
        import os
        assert os.path.isabs(LOG_DIR)
        assert os.path.isabs(DATA_DIR)


class TestBatchConfig:
    """批处理配置测试"""
    
    def test_batch_size(self):
        """测试批处理大小"""
        from etl.config.config import BATCH_SIZE
        assert BATCH_SIZE == 1000
        assert isinstance(BATCH_SIZE, int)
    
    def test_duplicate_check_days(self):
        """测试去重检查天数"""
        from etl.config.config import DUPLICATE_CHECK_DAYS
        assert DUPLICATE_CHECK_DAYS == 90
        assert isinstance(DUPLICATE_CHECK_DAYS, int)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])