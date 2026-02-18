-- 门店管理系统 - 数据库表结构
-- 创建时间: 2026-02-14

-- 1. 品牌门店表
CREATE TABLE IF NOT EXISTS brand_stores (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    brand_store_name VARCHAR(100) NOT NULL UNIQUE COMMENT '品牌门店名称',
    store_address VARCHAR(200) COMMENT '门店地址',
    store_type VARCHAR(50) COMMENT '门店类型（如：直营店/加盟店）',
    open_date DATE COMMENT '开店时间',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    contact_person VARCHAR(50) COMMENT '联系人',
    status ENUM('营业中', '关闭', '筹备中') DEFAULT '营业中' COMMENT '门店状态',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_status (status),
    INDEX idx_name (brand_store_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌门店信息表';

-- 2. 门店映射表
CREATE TABLE IF NOT EXISTS store_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    brand_store_id INT NOT NULL COMMENT '品牌门店ID',
    platform VARCHAR(20) NOT NULL COMMENT '平台（美团/饿了么/京东）',
    platform_store_name VARCHAR(100) NOT NULL COMMENT '平台门店名称',
    platform_store_id VARCHAR(50) COMMENT '平台门店ID（如京东的门店id）',
    city VARCHAR(100) COMMENT '门店所在城市',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用（0禁用/1启用）',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_platform_store (platform, platform_store_name),
    FOREIGN KEY (brand_store_id) REFERENCES brand_stores(id) ON DELETE CASCADE,
    INDEX idx_brand_store (brand_store_id),
    INDEX idx_platform (platform),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='门店映射关系表';

-- 3. 插入示例品牌门店数据
INSERT INTO brand_stores (brand_store_name, store_address, store_type, contact_phone, status) VALUES
('信和店', '深圳市南山区信和广场', '直营店', '0755-12345678', '营业中'),
('龙华店', '深圳市龙华区龙华大道', '直营店', '0755-12345679', '营业中'),
('壹方城店', '深圳市南山区壹方城购物中心', '直营店', '0755-12345680', '营业中'),
('新洲店', '深圳市福田区新洲路', '直营店', '0755-12345681', '营业中'),
('塘朗店', '深圳市南山区塘朗路', '直营店', '0755-12345682', '营业中'),
('蛇口店', '深圳市南山区蛇口海上世界', '直营店', '0755-12345683', '营业中'),
('梅林店', '深圳市福田区梅林路', '直营店', '0755-12345684', '营业中'),
('马家龙店', '深圳市南山区马家龙路', '直营店', '0755-12345685', '营业中'),
('皇庭店', '深圳市福田区皇庭广场', '直营店', '0755-12345686', '营业中'),
('登良店', '深圳市南山区登良路', '直营店', '0755-12345687', '营业中');

-- 4. 插入示例门店映射数据（美团）
INSERT INTO store_mapping (brand_store_id, platform, platform_store_name, is_active)
SELECT id, '美团', brand_store_name, 1 FROM brand_stores WHERE brand_store_name IN ('信和店', '龙华店', '壹方城店', '新洲店', '塘朗店', '蛇口店', '梅林店', '马家龙店', '皇庭店', '登良店');

-- 5. 插入示例门店映射数据（京东）
INSERT INTO store_mapping (brand_store_id, platform, platform_store_name, platform_store_id, city, is_active)
VALUES
(1, '京东', '雪乡情大地锅(信和广场店)', 'PPZH2669', '深圳市', 1),
(2, '京东', '雪乡情东北菜（龙华店）', 'PPZH2670', '深圳市', 1),
(3, '京东', '雪乡情东北菜馆（壹方城店）', 'PPZH2671', '深圳市', 1),
(4, '京东', '雪乡情东北菜（新洲店）', 'PPZH2672', '深圳市', 1),
(5, '京东', '雪乡情东北菜馆（大冲店）', 'PPZH2673', '深圳市', 1),
(6, '京东', '雪乡情铁锅炖（后海店）', 'PPZH2674', '深圳市', 1);