# 门店映射处理模块
# 用于处理平台门店名称到品牌门店名称的映射

import logging
from sqlalchemy import create_engine, text
from etl.config import get_connection_string

logger = logging.getLogger(__name__)


class StoreMapper:
    """门店映射处理器"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.engine = create_engine(get_connection_string())
        self.mapping_cache = {}
        self.unmapped_stores = set()
        self._load_mappings()
    
    def _load_mappings(self):
        """加载所有门店映射关系到缓存"""
        try:
            with self.engine.connect() as conn:
                # 查询所有启用的门店映射
                query = text("""
                    SELECT 
                        sm.platform,
                        sm.platform_store_name,
                        bs.brand_store_name,
                        bs.id as brand_store_id
                    FROM store_mapping sm
                    INNER JOIN brand_stores bs ON sm.brand_store_id = bs.id
                    WHERE sm.is_active = 1
                """)
                result = conn.execute(query)
                
                # 构建缓存: (platform, platform_store_name) -> brand_store_name
                for row in result.all():
                    key = (row.platform, row.platform_store_name)
                    self.mapping_cache[key] = {
                        'brand_store_name': row.brand_store_name,
                        'brand_store_id': row.brand_store_id
                    }
                    
                logger.info(f"✅ 已加载 {len(self.mapping_cache)} 条门店映射关系")
        
        except Exception as e:
            logger.error(f"❌ 加载门店映射失败: {e}")
            raise
    
    def get_brand_store_name(self, platform, platform_store_name):
        """
        获取品牌门店名称
        
        Args:
            platform: 平台名称（美团/饿了么/京东）
            platform_store_name: 平台门店名称
        
        Returns:
            brand_store_name: 品牌门店名称，如果未找到则返回None
        """
        key = (platform, platform_store_name)
        mapping = self.mapping_cache.get(key)
        
        if mapping:
            return mapping['brand_store_name']
        else:
            # 记录未映射的门店
            self.unmapped_stores.add((platform, platform_store_name))
            return None
    
    def get_mapping(self, platform, platform_store_name):
        """
        获取完整的映射信息
        
        Args:
            platform: 平台名称（美团/饿了么/京东）
            platform_store_name: 平台门店名称
        
        Returns:
            dict: 包含 brand_store_name 和 brand_store_id，如果未找到则返回None
        """
        key = (platform, platform_store_name)
        return self.mapping_cache.get(key)
    
    def has_mapping(self, platform, platform_store_name):
        """
        检查是否存在映射关系
        
        Args:
            platform: 平台名称（美团/饿了么/京东）
            platform_store_name: 平台门店名称
        
        Returns:
            bool: 是否存在映射
        """
        key = (platform, platform_store_name)
        return key in self.mapping_cache
    
    def get_unmapped_stores(self):
        """
        获取所有未映射的门店
        
        Returns:
            list: 未映射门店列表，格式为 [(platform, platform_store_name), ...]
        """
        return list(self.unmapped_stores)
    
    def log_unmapped_stores(self):
        """记录所有未映射的门店到日志"""
        if not self.unmapped_stores:
            return
        
        logger.warning("=" * 60)
        logger.warning(f"⚠️  发现 {len(self.unmapped_stores)} 个未映射的门店:")
        logger.warning("=" * 60)
        
        # 按平台分组显示
        by_platform = {}
        for platform, store_name in self.unmapped_stores:
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(store_name)
        
        for platform, stores in sorted(by_platform.items()):
            logger.warning(f"\n{platform} 平台 ({len(stores)} 个):")
            for store in stores:
                logger.warning(f"  - {store}")
        
        logger.warning("=" * 60)
        logger.warning("💡 请在门店管理界面中添加这些门店的映射关系")
        logger.warning("💡 添加映射后，重新运行ETL导入即可导入这些数据")
        logger.warning("=" * 60)
    
    def reload(self):
        """重新加载映射关系"""
        logger.info("🔄 重新加载门店映射关系...")
        self.mapping_cache.clear()
        self.unmapped_stores.clear()
        self._load_mappings()
        logger.info("✅ 门店映射关系重新加载完成")


# 创建全局实例
_mapper = None


def get_store_mapper():
    """获取门店映射器实例（单例模式）"""
    global _mapper
    if _mapper is None:
        _mapper = StoreMapper()
    return _mapper


def reset_mapper():
    """重置门店映射器实例"""
    global _mapper
    _mapper = None